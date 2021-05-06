from __future__ import annotations

from contextlib import contextmanager
from typing import Literal

from argo_dsl.api.io.argoproj.workflow.v1alpha1 import ValueFrom


class Task:
    ...


class Template:
    ...


class DagTemplate(Template):
    ...


class StepsTemplate(Template):
    ...


class TaskTemplate(Template):
    ...


@contextmanager
def parallel():
    ...


def template(args):
    def inner(f):
        ...

    return inner


class Workflow:
    # meta configs
    entrypoint = "Main"

    class Main(StepsTemplate):
        ...

    class Tmpl1(DagTemplate):
        ...

    class Tmpl2(TaskTemplate):
        class Parameters:
            v1: str
            v2: str = "123"
            v3: Literal["1", "2", "3"]
            v4: ValueFrom
