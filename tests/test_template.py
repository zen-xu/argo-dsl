import pytest

from argo_dsl.template import *


def test_new_parameters():
    class Parameters:
        v1: str
        v2: str = "123"
        v3: Literal["1", "2", "3"] = "2"
        v4: v1alpha1.ValueFrom = v1alpha1.ValueFrom(default="123")

    parameters = new_parameters(Parameters)

    assert parameters == [
        v1alpha1.Parameter(name="v1"),
        v1alpha1.Parameter(name="v2", default="123"),
        v1alpha1.Parameter(name="v3", enum=["1", "2", "3"], default="2"),
        v1alpha1.Parameter(name="v4", valueFrom=v1alpha1.ValueFrom(default="123")),
    ]
    assert new_parameters(None) is None


def test_executor_template():
    with pytest.raises(RuntimeError, match=r"Unknown manifest type"):

        class T(ExecutorTemplate):
            def specify_manifest(self) -> int:
                return 1

        T()

    with pytest.raises(RuntimeError, match=r"Need implement method"):

        class T(ExecutorTemplate):
            ...

        T()


def test_container_template():
    container = v1.Container(image="ubuntu")

    class TestTemplate(ContainerTemplate):
        name: ClassVar[str] = "test"
        image = "ubuntu"

        class Parameters:
            v1: str
            v2: str = "123"

    assert TestTemplate().template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        container=container,
    )


def test_script_template():
    script = v1alpha1.ScriptTemplate(image="ubuntu", source="echo hello")

    class TestScriptTemplate(ScriptTemplate):
        name: ClassVar[str] = "test"
        image = "ubuntu"
        source = "echo hello"

        class Parameters:
            v1: str
            v2: str = "123"

    assert TestScriptTemplate().template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        script=script,
    )


def test_resource_template():
    resource = v1alpha1.ResourceTemplate(action="get")

    class TestResourceTemplate(ResourceTemplate):
        name: ClassVar[str] = "test"
        action = "get"

        class Parameters:
            v1: str
            v2: str = "123"

    assert TestResourceTemplate().template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        resource=resource,
    )


def test_template_hooks():
    container = v1.Container(image="ubuntu")

    class TestTemplate(ContainerTemplate):
        name: ClassVar[str] = "test"

        class Parameters:
            v1: str
            v2: str = "123"

        def specify_manifest(self) -> v1.Container:
            return container

    def change_name(template: v1alpha1.Template) -> v1alpha1.Template:
        template.name = "test2"
        return template

    TestTemplate.__hooks__.append(change_name)

    assert TestTemplate().template == v1alpha1.Template(
        name="test2",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        container=container,
    )
