from argo_dsl.decorator import *
from argo_dsl.template import new_parameters


def test_script_decorator():
    @script(image="ubuntu", command="cat", pre_run="echo start", post_run="echo done")
    def script_template(a: str, b: int = 2):
        """
        hello world
        """

    class Parameters:
        a: str
        b: int = 2

    assert issubclass(script_template, ScriptTemplate)
    assert script_template.image == "ubuntu"
    assert script_template.name == "script_template"
    assert new_parameters(script_template.Parameters) == new_parameters(Parameters)
    assert (
        script_template().manifest.source
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
    @bash(image="ubuntu")
    def bash_template(a: str, b: int = 2):
        """
        echo $a, $b
        """

    assert (
        bash_template().manifest.source
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
    @python(image="python")
    def python_template(a: str, b: int = 2):
        print(a * b)

    assert (
        python_template().manifest.source
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

    assert new_parameters(python_template.Parameters) == [
        v1alpha1.Parameter(name="a"),
        v1alpha1.Parameter(name="b", default="2"),
        v1alpha1.Parameter(name="arg_pickle"),
    ]
