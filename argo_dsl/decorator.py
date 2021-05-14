from typing import Callable
from typing import ClassVar
from typing import Optional
from typing import Type

from pydantic import BaseModel
from pydantic import PrivateAttr

from .api.io.argoproj.workflow import v1alpha1
from .template import ScriptTemplate
from .utils import Function


class ExecutorTemplateDecorator(BaseModel):
    _func: Function = PrivateAttr()

    @property
    def func(self) -> Function:
        return self._func

    def __call__(
        self,
        func: Callable[..., Optional[str]],
    ) -> Type[ScriptTemplate]:
        self._func = Function(func)
        return self.generate_template()

    def generate_template(self) -> Type[ScriptTemplate]:
        raise NotImplementedError


class ScriptDecorator(ExecutorTemplateDecorator):
    image: str
    command: str = ""
    pre_run: str = ""
    post_run: str = ""

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
            image = decorator.image
            name: ClassVar[str] = decorator.func.name
            Parameters = decorator.generate_parameter_class()

            def specify_manifest(self) -> v1alpha1.ScriptTemplate:
                return v1alpha1.ScriptTemplate(image=self.image, source=source, command=["bash"])

        return Script

    def generate_source(self) -> str:
        return self.func.docstring or self.func.return_value or ""

    def generate_parameter_class(self) -> type:
        return self.func.parameter_class


script = ScriptDecorator


class BashDecorator(ScriptDecorator):
    command: str = "bash"

    def generate_source(self) -> str:
        source = super().generate_source()
        parameters = ['%s="{{inputs.parameters.%s}}"' % (parameter, parameter) for parameter in self.func.parameters]
        source = "\n".join(parameters) + "\n" + source

        return source


bash = BashDecorator


class PythonDecorator(ScriptDecorator):
    command: str = "python"
    pickle_protocol: Optional[int] = None
    max_args_repr_length: int = 20

    def generate_source(self) -> str:
        source = self.func.body.strip()

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

            source = f"{pickle_func_source}\n\n{source}"

        return source

    def generate_parameter_class(self) -> Type:
        parameter_class = self.func.parameter_class
        if not self.func.parameters:
            return parameter_class

        class Parameters(parameter_class):  # type: ignore
            arg_pickle: str

        return Parameters


python = PythonDecorator
