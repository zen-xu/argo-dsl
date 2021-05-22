from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from argo_dsl.api.io.argoproj.workflow import v1alpha1


if TYPE_CHECKING:
    from .template import Template


class _StepOutputs(str):
    _name: str
    _kind: str

    def __new__(cls, name, kind):
        obj = super().__new__(cls, "{{steps.%s.outputs.%s}}" % (name, kind))
        obj._name = name
        obj._kind = kind
        return obj

    def __getattribute__(self, item: str) -> Any:
        if item.startswith("_"):
            return super().__getattribute__(item)

        return "{{steps.%s.outputs.%s.%s}}" % (self._name, self._kind, item)


class _Item(str):
    def __new__(cls) -> _Item:
        return super().__new__(cls, "{{item}}")


Item = _Item()


def default_resolve_arguments(arguments: Dict[str, Any]) -> Dict[str, str]:
    return {k: str(v) for k, v in arguments.items()}


class TaskStep:
    template: Template
    name: str

    def __init__(self):
        self._arguments: Optional[Dict[str, Any]] = None
        self._batch_arguments: Optional[Union[str, List[Dict[str, Any]]]] = None
        self._sequence: Optional[v1alpha1.Sequence] = None
        self._when: Optional[str] = None

    def call(self, **arguments) -> TaskStep:
        self._arguments = arguments
        return self

    def batch_call(self, batch_arguments: Union[str, List[Dict[str, Any]]]) -> TaskStep:
        self._batch_arguments = batch_arguments
        return self

    def sequence(
        self,
        count: Optional[int] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        format: Optional[str] = None,
    ):
        self._sequence = v1alpha1.Sequence(count=count, start=start, end=end, format=format)
        return self

    def when(self, expression: str):
        self._when = expression

    @property
    def id(self) -> str:
        return "{{steps.%s.id}}" % self.name

    @property
    def ip(self) -> str:
        return "{{steps.%s.ip}}" % self.name

    @property
    def status(self) -> str:
        return "{{steps.%s.status}}" % self.name

    @property
    def exit_code(self) -> str:
        return "{{steps.%s.exitCode}}" % self.name

    @property
    def started_at(self) -> str:
        return "{{steps.%s.startedAt}}" % self.name

    @property
    def finished_at(self) -> str:
        return "{{steps.%s.finishedAt}}" % self.name

    @property
    def outputs_result(self) -> str:
        return "{{steps.%s.outputs.result}}" % self.name

    @property
    def outputs_parameters(self) -> _StepOutputs:
        return _StepOutputs(self.name, "parameters")

    @property
    def outputs_artifacts(self) -> _StepOutputs:
        return _StepOutputs(self.name, "artifacts")


class TaskStepMaker:
    def __init__(self, template: Template):
        self.template = template

    def __call__(self, name: str) -> TaskStep:
        s = TaskStep()
        s.template = self.template
        s.name = name

        return s


class TaskSteps:
    def __init__(self):
        self.steps: List[List[TaskStep]] = []
        self._parallel: bool = False
        self._inited_parallel_steps: bool = False

    @contextmanager
    def parallel(self):
        try:
            self._parallel = True
            self._inited_parallel_steps = False
            yield None
        finally:
            self._parallel = False
            self._inited_parallel_steps = False

    def add(self, step: TaskStep):
        if self._parallel:
            if not self._inited_parallel_steps:
                self.steps.append([])
                self._inited_parallel_steps = True
            self.steps[-1].append(step)
        else:
            self.steps.append([step])
