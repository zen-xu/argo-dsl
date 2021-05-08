from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional
from typing import TypeVar

import yaml

from pydantic.typing import resolve_annotations
from typing_extensions import Literal

from argo_dsl.api.io.argoproj.workflow.v1alpha1 import Inputs
from argo_dsl.api.io.argoproj.workflow.v1alpha1 import Parameter
from argo_dsl.api.io.argoproj.workflow.v1alpha1 import ScriptTemplate as ArgoScriptTemplate
from argo_dsl.api.io.argoproj.workflow.v1alpha1 import Template as ArgoTemplate
from argo_dsl.api.io.argoproj.workflow.v1alpha1 import ValueFrom
from argo_dsl.api.io.k8s.api.core.v1 import Container


T = TypeVar("T")


class Template(ABC):
    name: ClassVar[Optional[str]] = None
    Parameters: ClassVar[Optional[type]] = None

    def __init__(self):
        self.template = self.compile()

    def update_template(self):
        self.template = self.compile()

    @abstractmethod
    def compile(self) -> ArgoTemplate:
        ...

    def __repr__(self) -> str:
        return yaml.dump(self.template.dict(exclude_none=True))


def new_parameters(cls: Optional[type]) -> List[Parameter]:
    if cls is None:
        return []

    annos = resolve_annotations(
        cls.__annotations__,
        cls.__module__,
    )

    default_values: Dict[str, str] = {
        field: value for field, value in cls.__dict__.items() if not field.startswith("_")
    }

    parameters: List[Parameter] = []
    for parameter_name, parameter_type in annos.items():
        parameter = Parameter(name=parameter_name)

        if parameter_name in default_values:
            default_value = default_values[parameter_name]

            if isinstance(default_value, ValueFrom):
                parameter.valueFrom = default_value
                parameters.append(parameter)
                continue

            parameter.default = default_value

        origin_type = getattr(parameter_type, "__origin__", parameter_type)
        if origin_type == Literal:
            parameter.enum = list(parameter_type.__args__)

        parameters.append(parameter)

    return parameters


class ContainerTemplate(Template):
    def __init__(self, container: Optional[Container]):
        self.container = container or self.specify_container()
        super().__init__()

    def compile(self) -> ArgoTemplate:
        parameters = new_parameters(self.Parameters)
        name = self.name or self.__class__.__name__

        return ArgoTemplate(
            name=name,
            inputs=Inputs(parameters=parameters),
            container=self.container,
        )

    def specify_container(self) -> Container:
        raise NotImplementedError


class ScriptTemplate(Template):
    def __init__(self, script: Optional[ArgoScriptTemplate]):
        self.script = script or self.specify_script()
        super().__init__()

    def compile(self) -> ArgoTemplate:
        parameters = new_parameters(self.Parameters)
        name = self.name or self.__class__.__name__

        return ArgoTemplate(
            name=name,
            inputs=Inputs(parameters=parameters),
            script=self.script,
        )

    def specify_script(self) -> ArgoScriptTemplate:
        raise NotImplementedError
