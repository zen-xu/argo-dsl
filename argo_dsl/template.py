from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import ClassVar
from typing import Dict
from typing import Final
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar

import yaml

from pydantic.typing import resolve_annotations
from typing_extensions import Literal

from argo_dsl.api.io.argoproj.workflow import v1alpha1
from argo_dsl.api.io.k8s.api.core import v1


T = TypeVar("T")


class Template(ABC):
    name: ClassVar[Optional[str]] = None
    Parameters: ClassVar[Optional[type]] = None

    def __init__(self):
        self.template = self.compile()

    def update_template(self):
        self.template = self.compile()

    @abstractmethod
    def compile(self) -> v1alpha1.Template:
        ...

    def __repr__(self) -> str:
        return yaml.dump(self.template.dict(exclude_none=True))


def new_parameters(cls: Optional[type]) -> List[v1alpha1.Parameter]:
    if cls is None:
        return []

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
    manifest_type: ClassVar[str]

    def __init__(self, manifest: Optional[T] = None):
        super().__init__()
        self.manifest: T = manifest or self.specify_manifest()

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
    manifest_type: Final[ClassVar[str]] = "container"  # type: ignore


class ScriptTemplate(ExecutorTemplate[v1alpha1.ScriptTemplate]):
    manifest_type: Final[ClassVar[str]] = "script"  # type: ignore


class ResourceTemplate(ExecutorTemplate[v1alpha1.ResourceTemplate]):
    manifest_type: Final[ClassVar[str]] = "resource"  # type: ignore
