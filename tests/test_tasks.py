from pydantic import BaseModel

from argo_dsl.decorator import python_template
from argo_dsl.tasks import *
from argo_dsl.tasks import _StepOutputs  # noqa


def test_default_resolve_arguments():
    arguments = {"a": 1, "b": 1.2}
    assert default_resolve_arguments(arguments) == {"a": "1", "b": "1.2"}


def test_step_outputs():
    inst = _StepOutputs(name="test", kind="params")

    assert inst == "{{steps.test.outputs.params}}"
    assert inst.abc == "{{steps.test.outputs.params.abc}}"

    class Model(BaseModel):
        v: str

    assert Model(v=inst).dict()["v"] == "{{steps.test.outputs.params}}"


def test_item():
    assert Item == "{{item}}"

    class Model(BaseModel):
        v: str

    assert Model(v=Item).dict()["v"] == "{{item}}"


def test_task_step():
    @python_template(image="python")
    def echo():
        ...

    template = echo()
    tst = TaskStepMaker(template=template)
    step = tst("demo")
    assert step.name == "demo"
    assert step.resolve_arguments_func == template.resolve_arguments

    step.call(a="a", b="b")
    assert step._arguments == {"a": "a", "b": "b"}

    step.batch_call([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
    assert step._batch_arguments == [{"a": 1, "b": 2}, {"a": 3, "b": 4}]

    step.sequence(count=4, start=1)
    assert step._sequence == v1alpha1.Sequence(count=4, start=1)

    step.when("{{steps.demo.outputs.result}} == abc")
    assert step._when == "{{steps.demo.outputs.result}} == abc"

    assert step.id == "{{steps.demo.id}}"
    assert step.ip == "{{steps.demo.ip}}"
    assert step.status == "{{steps.demo.status}}"
    assert step.exit_code == "{{steps.demo.exitCode}}"
    assert step.started_at == "{{steps.demo.startedAt}}"
    assert step.finished_at == "{{steps.demo.finishedAt}}"
    assert step.outputs_result == "{{steps.demo.outputs.result}}"
    assert step.outputs_parameters == "{{steps.demo.outputs.parameters}}"
    assert step.outputs_artifacts == "{{steps.demo.outputs.artifacts}}"


def test_task_steps():
    @python_template(image="python")
    def echo():
        ...

    task_steps = TaskSteps()
    step = TaskStepMaker(template=echo())("demo")

    task_steps.add(step)
    assert task_steps.steps == [[step]]

    with task_steps.parallel():
        task_steps.add(step)
        task_steps.add(step)
    assert task_steps.steps == [[step], [step, step]]

    task_steps.add(step)
    assert task_steps.steps == [[step], [step, step], [step]]
