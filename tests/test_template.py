from typing_extensions import Literal

from argo_dsl.api.io.argoproj.workflow.v1alpha1 import Parameter
from argo_dsl.api.io.argoproj.workflow.v1alpha1 import ValueFrom
from argo_dsl.template import new_parameters


def test_new_parameters():
    class Parameters:
        v1: str
        v2: str = "123"
        v3: Literal["1", "2", "3"] = "2"
        v4: ValueFrom = ValueFrom(default="123")

    parameters = new_parameters(Parameters)

    assert parameters == [
        Parameter(name="v1"),
        Parameter(name="v2", default="123"),
        Parameter(name="v3", enum=["1", "2", "3"], default="2"),
        Parameter(name="v4", valueFrom=ValueFrom(default="123")),
    ]
