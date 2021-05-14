from typing import Callable
from typing import ClassVar
from typing import Final
from typing import Optional
from typing import Type

from .api.io.argoproj.workflow import v1alpha1
from .template import ScriptTemplate
from .utils import Function


class ExecutorTemplateDecorator:
    func: Function

    def __call__(
        self,
        func: Callable[..., Optional[str]],
    ) -> Type[ScriptTemplate]:
        self.func = Function(func)
        return self.generate_template()

    def generate_template(self) -> Type[ScriptTemplate]:
        raise NotImplementedError


class ScriptDecorator(ExecutorTemplateDecorator):
    command: ClassVar[str]
    pre_run: ClassVar[str] = ""
    post_run: ClassVar[str] = ""

    def generate_template(self) -> Type[ScriptTemplate]:
        source = self.generate_source()
        source = f"""\
cat > /tmp/script << EOL
{source}
EOL

set -e

{self.pre_run}
{self.command} /tmp/script
{self.post_run}
""".strip()
        decorator = self

        class Script(ScriptTemplate):
            name: ClassVar[str] = decorator.func.name
            Parameters = decorator.generate_parameter_class()

            def specify_manifest(self) -> v1alpha1.ScriptTemplate:
                return v1alpha1.ScriptTemplate(image=self.image, source=source, command=["bash"])

        return Script

    def generate_source(self) -> str:
        return self.func.docstring or self.func.return_value or ""

    def generate_parameter_class(self) -> type:
        return self.func.parameter_class


script = ScriptDecorator()


class BashDecorator(ScriptDecorator):
    command: Final[str] = "bash"  # type: ignore

    def generate_source(self) -> str:
        source = super().generate_source()
        parameters = ['%s="{{inputs.parameters.%s}}"' % (parameter, parameter) for parameter in self.func.parameters]
        source = "\n".join(parameters) + "\n" + source

        return source


bash = BashDecorator()


class PythonDecorator(ScriptDecorator):
    command: Final[str] = "python"  # type: ignore
    pickle_protocol: Optional[int] = None
    max_args_repr_length: int = 20

    def generate_source(self) -> str:
        source = super().generate_source()

        if self.func.parameters:
            pickle_func_source = (
                """\
def load_args():
    import pickle
    pickle_data = bytearray.fromhex("{{inputs.parameters.arg_pickle}}")
    return pickle.loads(pickle_data, protocol=%s)
globals().update(load_args())
del load_args"""
                % self.pickle_protocol
            )

            source = f"{pickle_func_source}\n{source}"

        return source

    def generate_parameter_class(self) -> Type:
        parameter_class = self.func.parameter_class
        if not self.func.parameters:
            return parameter_class

        class Parameters(parameter_class):  # type: ignore
            arg_pickle: str

        return Parameters


python = PythonDecorator()


def image(image_name: str) -> Callable[[Type[ScriptTemplate]], Type[ScriptTemplate]]:
    def wrapper(kls: Type[ScriptTemplate]) -> Type[ScriptTemplate]:
        ...

    return wrapper
