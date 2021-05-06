from __future__ import annotations

from abc import ABCMeta
from typing import Dict
from typing import List
from typing import Optional
from typing import TypeVar

from pydantic.typing import resolve_annotations
from typing_extensions import Literal

from argo_dsl.api.io.argoproj.workflow.v1alpha1 import Parameter
from argo_dsl.api.io.argoproj.workflow.v1alpha1 import ValueFrom


T = TypeVar("T")


class Template(metaclass=ABCMeta):
    name: Optional[str] = None
    Parameters: Optional[type] = None


def new_parameters(cls: Optional[type]) -> List[Parameter]:
    if cls is None:
        return []

    annos = resolve_annotations(
        cls.__annotations__,
        cls.__module__,
    )

    default_values: Dict[str, str] = {
        field: value
        for field, value in cls.__dict__.items()
        if not field.startswith("_")
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
