from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Callable
from typing import ClassVar
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar
from typing import Union
from typing import cast

import yaml

from pydantic.typing import resolve_annotations
from typing_extensions import Literal

from argo_dsl.api.io.argoproj.workflow import v1alpha1
from argo_dsl.api.io.k8s.api.core import v1


T = TypeVar("T")


class Template(ABC):
    name: ClassVar[Optional[str]] = None
    Parameters: ClassVar[Optional[type]] = None
    template: v1alpha1.Template
    __hooks__: ClassVar[List[Callable[[v1alpha1.Template], v1alpha1.Template]]] = []

    def __new__(
        cls,
        *,
        name: Optional[str] = None,
        parameters_class: Optional[type] = None,
        hooks: Optional[List[Callable[[v1alpha1.Template], v1alpha1.Template]]] = None,
    ) -> Template:
        cls.name = name or cls.name
        cls.Parameters = parameters_class or cls.Parameters
        cls.__hooks__ = hooks or cls.__hooks__

        template = super().__new__(cls)
        return template

    def __init__(self, **kwargs):
        self.template = self.compile()
        for hook in self.__hooks__:
            self.template = hook(self.template)

    def update_template(self):
        self.template = self.compile()

    @abstractmethod
    def compile(self) -> v1alpha1.Template:
        ...

    def __repr__(self) -> str:
        return yaml.dump(self.template.dict(exclude_none=True))


def new_parameters(cls: Optional[type]) -> Optional[List[v1alpha1.Parameter]]:
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


class ExecutorTemplate(Template, Generic[T]):
    manifest_type: str
    manifest: Union[v1.Container, v1alpha1.ScriptTemplate, v1alpha1.ResourceTemplate]

    def __new__(
        cls,
        *,
        name: Optional[str] = None,
        parameters_class: Optional[type] = None,
        hooks: Optional[List[Callable[[v1alpha1.Template], v1alpha1.Template]]] = None,
        manifest: Optional[Union[v1.Container, v1alpha1.ScriptTemplate, v1alpha1.ResourceTemplate]] = None,
    ) -> ExecutorTemplate:
        template = cast(
            ExecutorTemplate, super().__new__(cls, name=name, parameters_class=parameters_class, hooks=hooks)
        )

        manifest: T = manifest or template.specify_manifest()

        if isinstance(manifest, v1.Container):
            template.manifest_type = "container"
        elif isinstance(manifest, v1alpha1.ScriptTemplate):
            template.manifest_type = "script"
        elif isinstance(manifest, v1alpha1.ResourceTemplate):
            template.manifest_type = "resource"
        else:
            raise RuntimeError(
                f"Unknown manifest type `{type(manifest)}`, must be v1.Container, "
                "v1alpha1.ScriptTemplate or v1alpha1.ResourceTemplate"
            )
        template.manifest = manifest

        return template

    def compile(self) -> v1alpha1.Template:
        parameters = new_parameters(self.Parameters)
        name = self.name or self.__class__.__name__

        return v1alpha1.Template.validate(
            {"name": name, "inputs": v1alpha1.Inputs(parameters=parameters), self.manifest_type: self.manifest}
        )

    def specify_manifest(self) -> T:
        # if `manifest` is not provided when __init__, Template should promise
        # has implemented the method `specify_manifest`
        raise RuntimeError("Need implement method `specify_manifest`")


class ContainerTemplate(ExecutorTemplate[v1.Container]):
    ...


class ScriptTemplate(ExecutorTemplate[v1alpha1.ScriptTemplate]):
    ...


class ResourceTemplate(ExecutorTemplate[v1alpha1.ResourceTemplate]):
    ...
