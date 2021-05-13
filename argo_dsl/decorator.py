from typing import Callable
from typing import ClassVar
from typing import Final
from typing import Optional
from typing import Type

from typing_extensions import Literal

from .api.io.argoproj.workflow import v1alpha1
from .template import ScriptTemplate
from .utils import Function


SerializeEngine = Literal["yaml", "pickle"]


class ExecutorTemplateDecorator:
    def __call__(
        self,
        func: Callable[..., Optional[str]],
    ) -> Type[ScriptTemplate]:
        return self.generate_template(Function(func))

    def generate_template(self, func: Function) -> Type[ScriptTemplate]:
        raise NotImplementedError


class ScriptDecorator(ExecutorTemplateDecorator):
    command: ClassVar[str]

    def generate_template(self, func: Function) -> Type[ScriptTemplate]:
        source = self.generate_source(func)
        decorator = self

        class Script(ScriptTemplate):
            name: ClassVar[str] = func.name
            Parameters = func.parameter_class

            def specify_manifest(self) -> v1alpha1.ScriptTemplate:
                return v1alpha1.ScriptTemplate(image=self.image, source=source, command=decorator.command)

        return Script

    def generate_source(self, func: Function) -> str:
        return func.docstring or func.return_value or ""


script = ScriptDecorator()


class BashDecorator(ScriptDecorator):
    command: Final[str] = "bash"  # type: ignore

    def generate_source(self, func: Function) -> str:
        source = super().generate_source(func)
        parameters = ["%s={{inputs.parameters.%s}}" % (parameter, parameter) for parameter in func.parameters]
        source = "\n".join(parameters) + "\n" + source

        return source


bash = BashDecorator()


class PythonDecorator(ScriptDecorator):
    command: Final[str] = "python"  # type: ignore
    serialize_engine: SerializeEngine = "pickle"
    pickle_protocol: Optional[int] = None

    def generate_source(self, func: Function) -> str:
        ...


python = PythonDecorator()


def image(image_name: str) -> Callable[[Type[ScriptTemplate]], Type[ScriptTemplate]]:
    def wrapper(kls: Type[ScriptTemplate]) -> Type[ScriptTemplate]:
        ...

    return wrapper
