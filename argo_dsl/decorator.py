import pickle

from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar

from pydantic import BaseModel
from pydantic import PrivateAttr
from pydantic.generics import GenericModel
from typing_extensions import Literal

from .api.io.argoproj.workflow import v1alpha1
from .template import ResourceTemplate
from .template import ScriptTemplate
from .template import Template
from .utils import Function


_T = TypeVar("_T", bound=Template)


class TemplateDecorator(BaseModel, Generic[_T]):
    _func: Function = PrivateAttr()

    @property
    def func(self) -> Function:
        return self._func

    def __call__(
        self,
        func: Callable[..., Optional[str]],
    ) -> Type[_T]:
        self._func = Function(func)
        return self.generate_template()

    def generate_template(self) -> Type[_T]:
        raise NotImplementedError

    def generate_parameter_class(self) -> type:
        return self.func.parameter_class


class ScriptDecorator(TemplateDecorator[ScriptTemplate]):
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


script_template = ScriptDecorator


class BashDecorator(ScriptDecorator):
    command: str = "bash"

    def generate_source(self) -> str:
        source = super().generate_source()
        parameters = ['%s="{{inputs.parameters.%s}}"' % (parameter, parameter) for parameter in self.func.parameters]
        source = "\n".join(parameters) + "\n" + source

        return source


bash_template = BashDecorator


class PythonDecorator(ScriptDecorator):
    command: str = "python"
    pickle_protocol: Optional[int] = None

    def generate_source(self) -> str:
        source = self.func.body.strip()
        parameter_class = self.func.parameter_class

        is_value_from_param = lambda name, annotation: annotation == v1alpha1.ValueFrom or isinstance(
            getattr(parameter_class, name, None), v1alpha1.ValueFrom
        )

        codes = []
        for param_name, param_annotation in parameter_class.__annotations__.items():
            if is_value_from_param(param_name, param_annotation) or param_annotation == str:
                codes.append('%s = "{{inputs.parameters.%s}}"' % (param_name, param_name))
            elif param_annotation in [int, float, bool, complex]:
                codes.append("%s = {{inputs.parameters.%s}}" % (param_name, param_name))
            else:
                if codes[0] != "import pickle":
                    codes = ["import pickle"] + codes
                codes.append(
                    '%s = pickle.loads(bytearray.fromhex("{{inputs.parameters.%s}}"), protocol=%s)'
                    % (param_name, param_name, self.pickle_protocol)
                )

        if self.func.parameters:
            source = "\n".join(codes) + f"\n\n{source}"

        return source

    def generate_parameter_class(self) -> Type:
        parameter_class = self.func.parameter_class
        if not self.func.parameters:
            return parameter_class

        annotations = dict(parameter_class.__annotations__)

        def serialize_default_value(v: Any):
            if isinstance(v, v1alpha1.ValueFrom):
                return v
            elif isinstance(v, (str, int, float, bool, complex)):
                return str(v)
            else:
                return str(pickle.dumps(v, protocol=self.pickle_protocol).hex())

        default_fields: Dict[str, Any] = {
            k: serialize_default_value(v) for k, v in parameter_class.__dict__.items() if not k.startswith("_")
        }
        return type("Parameters", (), {"__annotations__": annotations, **default_fields})


python_template = PythonDecorator


class ResourceDecorator(TemplateDecorator[ResourceTemplate]):
    action: Literal["get", "create", "apply", "delete", "replace", "patch"]
    resource_manifest: Optional[str] = None
    failureCondition: Optional[str] = None
    flags: Optional[List[str]] = None
    mergeStrategy: Optional[Literal["strategic", "merge", "json"]] = None
    setOwnerReference: Optional[bool] = None
    successCondition: Optional[str] = None

    def generate_template(self) -> Type[ResourceTemplate]:
        manifest = self.generate_manifest()

        class Resource(ResourceTemplate):
            name = self.func.name
            Parameters = self.generate_parameter_class()
            action = self.action
            resource_manifest = manifest
            failureCondition = self.failureCondition
            flags = self.flags
            mergeStrategy = self.mergeStrategy
            setOwnerReference = self.setOwnerReference
            successCondition = self.successCondition

        return Resource

    def generate_manifest(self) -> str:
        return self.func.docstring or self.func.return_value or ""


resource_template = ResourceDecorator


class Hook(GenericModel, Generic[_T]):
    def __call__(self, t: Type[_T]) -> Type[_T]:
        class T(t):  # type: ignore
            __hooks__ = t.__hooks__ + [self.hook()]

        return T

    def hook(self) -> Callable[[v1alpha1.Template], v1alpha1.Template]:
        raise NotImplementedError
