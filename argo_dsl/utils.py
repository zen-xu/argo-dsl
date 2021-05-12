import inspect
import re
import textwrap

from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Union


def get_function_body(func: Callable[..., Any]) -> str:
    body_lines = []
    left_bracket_num = 0
    right_bracket_num = 0
    def_found = False
    end_of_signature = False

    for line in inspect.getsourcelines(func)[0]:

        if end_of_signature:
            body_lines.append(line)

        if re.match(r"\s*def", line):
            def_found = True

        if not def_found and "def" not in line:
            continue

        for char in line:
            if char == "(":
                left_bracket_num += 1
            elif char == ")":
                right_bracket_num += 1

        if (left_bracket_num - right_bracket_num == 0) and ":" in line:
            end_of_signature = True

    return textwrap.dedent("".join(body_lines))


def check_function_has_return_value(func: Callable[..., Any]) -> bool:
    return inspect.getsourcelines(func)[0][-1].lstrip().startswith("return ")


class Function:
    def __init__(self, func: Callable[..., Union[Optional[str], None]]):
        self.func = func
        self.body = get_function_body(func)
        self.docstring = textwrap.dedent(func.__doc__ or "").strip()
        parameters: Dict[str, inspect.Parameter] = dict(inspect.signature(func).parameters)
        parameters.pop("self", None)
        self.parameter_class = self._new_parameters_class(parameters)
        self.return_value = None

        if check_function_has_return_value(func):
            self.return_value = str(func(*([None] * len(parameters))))

    @staticmethod
    def _new_parameters_class(parameters: Dict[str, inspect.Parameter]) -> type:
        annotations = {
            parameter.name: str if parameter.annotation is parameter.empty else parameter.annotation
            for parameter in parameters.values()
        }

        defaults = {
            parameter.name: parameter.default
            for parameter in parameters.values()
            if parameter.default != parameter.empty
        }

        return type("Parameters", (), {**defaults, "__annotations__": annotations})