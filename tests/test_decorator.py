import re

from argo_dsl.decorator import *
from argo_dsl.template import new_parameters


def test_script_decorator():
    @script_template(image="ubuntu", command="cat", pre_run="echo start", post_run="echo done")
    def script(a: str, b: int = 2):
        """
        hello world
        """

    class Parameters:
        a: str
        b: int = 2

    assert issubclass(script, ScriptTemplate)
    assert script.image == "ubuntu"
    assert script.name == "script"
    assert new_parameters(script.Parameters) == new_parameters(Parameters)
    assert (
        script().manifest.source
        == """\
cat > /tmp/script << EOL
hello world
EOL

set -e

echo start
cat /tmp/script
echo done"""
    )

    assert script().serialize_argument(1) == "1"


def test_bash_decorator():
    @bash_template(image="ubuntu")
    def echo(a: str, b: int = 2):
        """
        echo $a, $b
        """

    assert (
        echo().manifest.source
        == """\
cat > /tmp/script << EOL
a="{{inputs.parameters.a}}"
b="{{inputs.parameters.b}}"
echo $a, $b
EOL

set -e


bash /tmp/script"""
    )


def test_python_decorator_with_parameters():
    @python_template(image="python")
    def print_result(
        a: str,
        b: int = 2,
        c: float = 3.3,
        d: bool = False,
        e: complex = 2j,
        f: re.Pattern = re.compile("abc"),
        g: v1alpha1.ValueFrom = v1alpha1.ValueFrom(default="4"),
    ):
        print(a * b)

    assert (
        print_result().manifest.source
        == """\
cat > /tmp/script << EOL
import pickle
a = "{{inputs.parameters.a}}"
b = {{inputs.parameters.b}}
c = {{inputs.parameters.c}}
d = {{inputs.parameters.d}}
e = {{inputs.parameters.e}}
f = pickle.loads(bytearray.fromhex("{{inputs.parameters.f}}"), protocol=None)
g = "{{inputs.parameters.g}}"

print(a * b)
EOL

set -e


python /tmp/script"""
    )

    assert print_result().serialize_argument("a") == "a"
    assert print_result().serialize_argument(1) == "1"
    assert print_result().serialize_argument(1.1) == "1.1"
    assert print_result().serialize_argument(2j) == "2j"
    assert print_result().serialize_argument(True) == "True"
    assert print_result().serialize_argument(re.compile("abc")) == str(pickle.dumps(re.compile("abc")).hex())

    assert new_parameters(print_result.Parameters) == [
        v1alpha1.Parameter(name="a"),
        v1alpha1.Parameter(name="b", default="2"),
        v1alpha1.Parameter(name="c", default="3.3"),
        v1alpha1.Parameter(name="d", default="False"),
        v1alpha1.Parameter(name="e", default="2j"),
        v1alpha1.Parameter(name="f", default=str(pickle.dumps(re.compile("abc")).hex())),
        v1alpha1.Parameter(name="g", valueFrom=v1alpha1.ValueFrom(default="4")),
    ]


def test_python_decorator_with_builtin_parameters():
    @python_template(image="python")
    def print_result(
        a: str,
        b: int = 2,
    ):
        print(a * b)

    assert (
        print_result().manifest.source
        == """\
cat > /tmp/script << EOL
a = "{{inputs.parameters.a}}"
b = {{inputs.parameters.b}}

print(a * b)
EOL

set -e


python /tmp/script"""
    )


def test_python_decorator_without_parameters():
    @python_template(image="python")
    def print_str():
        print("Hello World")

    assert (
        print_str().manifest.source
        == """\
cat > /tmp/script << EOL
print("Hello World")
EOL

set -e


python /tmp/script"""
    )


def test_resource_decorator_with_parameters():
    @resource_template(action="get")
    def get_pod(name):
        """
        apiVersion: v1
        kind: Pod
        metadata:
          name: {{inputs.parameters.name}}
        """

    assert (
        get_pod().resource_manifest
        == """\
apiVersion: v1
kind: Pod
metadata:
  name: {{inputs.parameters.name}}"""
    )
    assert get_pod().name == "get_pod"
    assert new_parameters(get_pod.Parameters) == [
        v1alpha1.Parameter(name="name"),
    ]


def test_resource_decorator_without_parameters():
    @resource_template(action="get")
    def get_pod():
        """
        apiVersion: v1
        kind: Pod
        metadata:
          name: demo
        """

    assert (
        get_pod().resource_manifest
        == """\
apiVersion: v1
kind: Pod
metadata:
  name: demo"""
    )


def test_hook():
    class image(Hook):
        image: str

        def hook(self) -> Callable[[v1alpha1.Template], v1alpha1.Template]:
            def add_image(template: v1alpha1.Template) -> v1alpha1.Template:
                template.script.image = "test"
                return template

            return add_image

    @image(image="test")
    @script_template(image="ubuntu")
    def script():
        ...

    assert script().template.script.image == "test"
