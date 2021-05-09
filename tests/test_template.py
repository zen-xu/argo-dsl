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

        @classmethod
        def specify_manifest(cls) -> v1.Container:
            return container

    assert TestTemplate().template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        container=container,
    )


def test_script_template_with_input_parameters():
    script = v1alpha1.ScriptTemplate(image="ubuntu", source="echo hello")

    class Parameters:
        v1: str
        v2: str = "123"

    assert ContainerTemplate(name="test", parameters_class=Parameters, manifest=script).template == v1alpha1.Template(
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

        @classmethod
        def specify_manifest(cls) -> v1alpha1.ScriptTemplate:
            return script

    assert TestScriptTemplate().template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        script=script,
    )


def test_resource_template_with_input_parameters():
    resource = v1alpha1.ResourceTemplate(action="get")

    class Parameters:
        v1: str
        v2: str = "123"

    assert ContainerTemplate(name="test", parameters_class=Parameters, manifest=resource).template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        resource=resource,
    )


def test_resource_template_with_implementation():
    resource = v1alpha1.ResourceTemplate(action="get")

    class TestResourceTemplate(ScriptTemplate):
        name: ClassVar[str] = "test"

        class Parameters:
            v1: str
            v2: str = "123"

        @classmethod
        def specify_manifest(cls) -> v1alpha1.ResourceTemplate:
            return resource

    assert TestResourceTemplate().template == v1alpha1.Template(
        name="test",
        inputs=v1alpha1.Inputs(
            parameters=[v1alpha1.Parameter(name="v1"), v1alpha1.Parameter(name="v2", default="123")]
        ),
        resource=resource,
    )
