from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Callable
from typing import ClassVar
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

import yaml

from pydantic.typing import resolve_annotations
from typing_extensions import Literal

from . import utils
from .api.io.argoproj.workflow import v1alpha1
from .api.io.k8s.api.core import v1


_T = TypeVar("_T")


class Template(ABC):
    name: ClassVar[Optional[str]] = None
    Parameters: ClassVar[Optional[Type]] = None
    template: v1alpha1.Template
    __hooks__: ClassVar[List[Callable[[v1alpha1.Template], v1alpha1.Template]]] = []

    def __init__(self):
        self.construct()
        self.template = self.compile()
        for hook in self.__hooks__:
            self.template = hook(self.template)

    def construct(self):
        """
        Subclass need to implement `construct` method rather than __init__
        """

    @abstractmethod
    def compile(self) -> v1alpha1.Template:
        ...

    def __repr__(self) -> str:
        return yaml.dump(self.template.dict(exclude_none=True), Dumper=utils.BlockDumper)


def new_parameters(cls: Optional[Type]) -> Optional[List[v1alpha1.Parameter]]:
    if cls is None:
        return None

    annos = resolve_annotations(
        cls.__annotations__,
        cls.__module__,
    )

    default_values: Dict[str, str] = {
        field: value for field, value in cls.__dict__.items() if not field.startswith("_")
    }

    parameters: List[v1alpha1.Parameter] = []
    for parameter_name, parameter_type in annos.items():
        parameter = v1alpha1.Parameter(name=parameter_name)

        if parameter_name in default_values:
            default_value = default_values[parameter_name]

            if isinstance(default_value, v1alpha1.ValueFrom):
                parameter.valueFrom = default_value
                parameters.append(parameter)
                continue

            parameter.default = default_value

        origin_type = getattr(parameter_type, "__origin__", parameter_type)
        if origin_type == Literal:
            parameter.enum = list(parameter_type.__args__)

        parameters.append(parameter)

    return parameters


class ExecutorTemplate(Template, Generic[_T]):
    manifest: Union[v1alpha1.ScriptTemplate, v1alpha1.ScriptTemplate, v1alpha1.ResourceTemplate]

    def construct(self):  # pragma: no cover
        if not hasattr(self, "manifest"):
            self.manifest = self.specify_manifest()

    @property
    def _manifest_type(self) -> str:
        if isinstance(self.manifest, v1.Container):
            return "container"
        elif isinstance(self.manifest, v1alpha1.ScriptTemplate):
            return "script"
        elif isinstance(self.manifest, v1alpha1.ResourceTemplate):
            return "resource"
        else:
            raise RuntimeError(
                f"Unknown manifest type `{type(self.manifest)}`, must be v1.Container, "
                "v1alpha1.ScriptTemplate or v1alpha1.ResourceTemplate"
            )

    def compile(self) -> v1alpha1.Template:
        parameters = new_parameters(self.Parameters)
        name = self.name or self.__class__.__name__

        return v1alpha1.Template.validate(
            {"name": name, "inputs": v1alpha1.Inputs(parameters=parameters), self._manifest_type: self.manifest}
        )

    def specify_manifest(self) -> _T:
        """
        If class var `manifest` is not provided, use this method to
        init `manifest`
        """
        raise RuntimeError("Need implement method `specify_manifest`")


class ContainerTemplate(ExecutorTemplate[v1.Container]):
    image: str

    def specify_manifest(self) -> v1.Container:
        return v1.Container(image=self.image)


class ScriptTemplate(ExecutorTemplate[v1alpha1.ScriptTemplate]):
    image: str
    source: str

    def specify_manifest(self) -> v1alpha1.ScriptTemplate:
        return v1alpha1.ScriptTemplate(image=self.image, source=self.source)


class ResourceTemplate(ExecutorTemplate[v1alpha1.ResourceTemplate]):
    action: Literal["get", "create", "apply", "delete", "replace", "patch"]
    resource_manifest: Optional[str] = None
    failureCondition: Optional[str] = None
    flags: Optional[List[str]] = None
    mergeStrategy: Optional[Literal["strategic", "merge", "json"]] = None
    setOwnerReference: Optional[bool] = None
    successCondition: Optional[str] = None

    def specify_manifest(self) -> v1alpha1.ResourceTemplate:
        return v1alpha1.ResourceTemplate(
            action=self.action,
            manifest=self.resource_manifest,
            failureCondition=self.failureCondition,
            flags=self.flags,
            mergeStrategy=self.mergeStrategy,
            setOwnerReference=self.setOwnerReference,
            successCondition=self.successCondition,
        )
