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


def test_container_template_with_input_parameters():
    container = v1.Container(image="ubuntu")

    class Parameters:
        v1: str
        v2: str = "123"

    assert ContainerTemplate(
        name="test", parameters_class=Parameters, manifest=container
    ).template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        container=container,
    )


def test_container_template_with_implementation():
    container = v1.Container(image="ubuntu")

    class TestTemplate(ContainerTemplate):
        name: ClassVar[str] = "test"

        class Parameters:
            v1: str
            v2: str = "123"

        def specify_manifest(self) -> v1.Container:
            return container

    assert TestTemplate().template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        container=container,
    )


def test_container_template_with_given_image():
    container = v1.Container(image="ubuntu")

    class TestTemplate(ScriptTemplate):
        name: ClassVar[str] = "test"
        image = "ubuntu"

        class Parameters:
            v1: str
            v2: str = "123"

        def specify_manifest(self) -> v1alpha1.ScriptTemplate:
            return container

    assert TestTemplate().image == "ubuntu"

    assert (
        TestTemplate(name="test", image="ubuntu", parameters_class=TestTemplate.Parameters, manifest=container).image
        == "ubuntu"
    )


def test_script_template_with_input_parameters():
    script = v1alpha1.ScriptTemplate(image="ubuntu", source="echo hello")

    class Parameters:
        v1: str
        v2: str = "123"

    assert ScriptTemplate(name="test", parameters_class=Parameters, manifest=script).template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        script=script,
    )


def test_script_template_with_implementation():
    script = v1alpha1.ScriptTemplate(image="ubuntu", source="echo hello")

    class TestScriptTemplate(ScriptTemplate):
        name: ClassVar[str] = "test"

        class Parameters:
            v1: str
            v2: str = "123"

        def specify_manifest(self) -> v1alpha1.ScriptTemplate:
            return script

    assert TestScriptTemplate().template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        script=script,
    )


def test_script_template_with_given_image():
    script = v1alpha1.ScriptTemplate(image="ubuntu", source="echo hello")

    class TestScriptTemplate(ScriptTemplate):
        name: ClassVar[str] = "test"
        image = "ubuntu"

        class Parameters:
            v1: str
            v2: str = "123"

        def specify_manifest(self) -> v1alpha1.ScriptTemplate:
            return script

    assert TestScriptTemplate().image == "ubuntu"

    assert (
        ScriptTemplate(
            name="test", image="ubuntu", parameters_class=TestScriptTemplate.Parameters, manifest=script
        ).image
        == "ubuntu"
    )


def test_resource_template_with_input_parameters():
    resource = v1alpha1.ResourceTemplate(action="get")

    class Parameters:
        v1: str
        v2: str = "123"

    assert ResourceTemplate(
        action="get", name="test", parameters_class=Parameters, manifest=resource
    ).template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        resource=resource,
    )

    with pytest.raises(RuntimeError):
        ResourceTemplate(name="test", parameters_class=Parameters)


def test_resource_template_with_implementation():
    resource = v1alpha1.ResourceTemplate(action="get")

    class TestResourceTemplate(ResourceTemplate):
        name: ClassVar[str] = "test"

        class Parameters:
            v1: str
            v2: str = "123"

        def specify_manifest(self) -> v1alpha1.ResourceTemplate:
            return resource

    assert TestResourceTemplate().template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        resource=resource,
    )

    with pytest.raises(RuntimeError):

        class TestResourceTemplate2(ResourceTemplate):
            name: ClassVar[str] = "test"

            class Parameters:
                v1: str
                v2: str = "123"

            def specify_manifest(self):
                return None

        TestResourceTemplate2()


def test_template_hooks_with_input_parameters():
    container = v1.Container(image="ubuntu")

    class Parameters:
        v1: str
        v2: str = "123"

    def change_name(template: v1alpha1.Template) -> v1alpha1.Template:
        template.name = "test2"
        return template

    assert ContainerTemplate(
        name="test", parameters_class=Parameters, manifest=container, hooks=[change_name]
    ).template == v1alpha1.Template(
        name="test2",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        container=container,
    )


def test_template_hooks_with_implementation():
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
