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
    def print_result(a: str, b: int = 2):
        print(a * b)

    assert (
        print_result().manifest.source
        == """\
cat > /tmp/script << EOL
def load_args():
    import pickle
    pickle_data = bytearray.fromhex("{{inputs.parameters.arg_pickle}}")
    return pickle.loads(pickle_data, protocol=None)
globals().update(load_args())
del load_args

print(a * b)
EOL

set -e


python /tmp/script"""
    )

    assert new_parameters(print_result.Parameters) == [
        v1alpha1.Parameter(name="a"),
        v1alpha1.Parameter(name="b", default="2"),
        v1alpha1.Parameter(name="arg_pickle"),
    ]


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
