from typing_extensions import Literal

from argo_dsl.api.io.argoproj.workflow.v1alpha1 import Parameter
from argo_dsl.api.io.argoproj.workflow.v1alpha1 import ValueFrom
from argo_dsl.template import new_parameters
from argo_dsl.utils import *


def test_get_function_body():
    def calculator():
        import math

        a = 1
        b = 2

        print(math.pow(a, b))

    assert (
        get_function_body(calculator)
        == """\
import math

a = 1
b = 2

print(math.pow(a, b))
"""
    )


def test_check_function_has_return_value():
    def no_return():
        print(1 + 1)

    assert check_function_has_return_value(no_return) is False

    def has_return():
        return 1 + 1

    assert check_function_has_return_value(has_return) is True


def test_function_class_with_func():
    def hello(
        a, b: str = "123", c: Literal["apple", "orange", "peach"] = "apple", d: ValueFrom = ValueFrom(default="123")
    ):
        """
        This is a demo
        """

        print("Hello World")

    func = Function(hello)

    assert (
        func.body
        == """\
\"""
This is a demo
\"""

print("Hello World")
"""
    )
    assert func.docstring == "This is a demo"
    assert new_parameters(func.parameter_class) == [
        Parameter(name="a"),
        Parameter(name="b", default="123"),
        Parameter(name="c", enum=["apple", "orange", "peach"], default="apple"),
        Parameter(name="d", valueFrom=ValueFrom(default="123")),
    ]
    assert func.return_value is None


def test_function_class_with_func_with_return_value():
    def hello(
        a, b: str = "123", c: Literal["apple", "orange", "peach"] = "apple", d: ValueFrom = ValueFrom(default="123")
    ) -> str:
        return "This is a demo"

    func = Function(hello)

    assert func.return_value == "This is a demo"


def test_function_class_with_method():
    class C:
        def hello(
            self,
            a,
            b: str = "123",
            c: Literal["apple", "orange", "peach"] = "apple",
            d: ValueFrom = ValueFrom(default="123"),
        ):
            """
            This is a demo
            """

            print("Hello World")

    func = Function(C().hello)

    assert (
        func.body
        == """\
\"""
This is a demo
\"""

print("Hello World")
"""
    )
    assert func.docstring == "This is a demo"
    assert new_parameters(func.parameter_class) == [
        Parameter(name="a"),
        Parameter(name="b", default="123"),
        Parameter(name="c", enum=["apple", "orange", "peach"], default="apple"),
        Parameter(name="d", valueFrom=ValueFrom(default="123")),
    ]
    assert func.return_value is None
