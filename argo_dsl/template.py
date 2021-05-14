from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Callable
from typing import ClassVar
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union
from typing import cast

import yaml

from pydantic.typing import resolve_annotations
from typing_extensions import Literal

from argo_dsl.api.io.argoproj.workflow import v1alpha1
from argo_dsl.api.io.k8s.api.core import v1


T = TypeVar("T")


class Template(ABC):
    name: ClassVar[Optional[str]] = None
    Parameters: ClassVar[Optional[Type]] = None
    template: v1alpha1.Template
    __hooks__: ClassVar[List[Callable[[v1alpha1.Template], v1alpha1.Template]]] = []

    def __new__(
        cls,
        *,
        name: Optional[str] = None,
        parameters_class: Optional[Type] = None,
        hooks: Optional[List[Callable[[v1alpha1.Template], v1alpha1.Template]]] = None,
    ) -> Template:
        cls.name = name or cls.name
        cls.Parameters = parameters_class or cls.Parameters
        cls.__hooks__ = hooks or cls.__hooks__

        template = super().__new__(cls)
        return template

    def __init__(self, **kwargs):
        self.template = self.compile()
        for hook in self.__hooks__:
            self.template = hook(self.template)

    def update_template(self):
        self.template = self.compile()

    @abstractmethod
    def compile(self) -> v1alpha1.Template:
        ...

    def __repr__(self) -> str:
        return yaml.dump(self.template.dict(exclude_none=True))


def new_parameters(cls: Optional[Type]) -> Optional[List[v1alpha1.Parameter]]:
    if cls is None:
        return None

    annos = resolve_annotations(
        cls.__annotations__,
        cls.__module__,
    )

    default_values: Dict[str, str] = {
        field: value for field, value in cls.__dict__.items() if not field.startswith("_")
    }

    parameters: List[v1alpha1.Parameter] = []
    for parameter_name, parameter_type in annos.items():
        parameter = v1alpha1.Parameter(name=parameter_name)

        if parameter_name in default_values:
            default_value = default_values[parameter_name]

            if isinstance(default_value, v1alpha1.ValueFrom):
                parameter.valueFrom = default_value
                parameters.append(parameter)
                continue

            parameter.default = default_value

        origin_type = getattr(parameter_type, "__origin__", parameter_type)
        if origin_type == Literal:
            parameter.enum = list(parameter_type.__args__)

        parameters.append(parameter)

    return parameters


class ExecutorTemplate(Template, Generic[T]):
    manifest_type: str
    manifest: Union[v1.Container, v1alpha1.ScriptTemplate, v1alpha1.ResourceTemplate]

    def __new__(
        cls,
        *,
        name: Optional[str] = None,
        parameters_class: Optional[Type] = None,
        hooks: Optional[List[Callable[[v1alpha1.Template], v1alpha1.Template]]] = None,
        manifest: Optional[Union[v1.Container, v1alpha1.ScriptTemplate, v1alpha1.ResourceTemplate]] = None,
    ) -> ExecutorTemplate:
        template = cast(
            ExecutorTemplate, super().__new__(cls, name=name, parameters_class=parameters_class, hooks=hooks)
        )

        manifest: T = manifest or template.specify_manifest()

        if isinstance(manifest, v1.Container):
            template.manifest_type = "container"
        elif isinstance(manifest, v1alpha1.ScriptTemplate):
            template.manifest_type = "script"
        elif isinstance(manifest, v1alpha1.ResourceTemplate):
            template.manifest_type = "resource"
        else:
            raise RuntimeError(
                f"Unknown manifest type `{type(manifest)}`, must be v1.Container, "
                "v1alpha1.ScriptTemplate or v1alpha1.ResourceTemplate"
            )
        template.manifest = manifest

        return template

    def compile(self) -> v1alpha1.Template:
        parameters = new_parameters(self.Parameters)
        name = self.name or self.__class__.__name__

        return v1alpha1.Template.validate(
            {"name": name, "inputs": v1alpha1.Inputs(parameters=parameters), self.manifest_type: self.manifest}
        )

    def specify_manifest(self) -> T:
        # if `manifest` is not provided when __init__, Template should promise
        # has implemented the method `specify_manifest`
        raise RuntimeError("Need implement method `specify_manifest`")


class ContainerTemplate(ExecutorTemplate[v1.Container]):
    image: Optional[str] = None

    def __new__(
        cls,
        *,
        name: Optional[str] = None,
        image: Optional[str] = None,
        parameters_class: Optional[type] = None,
        hooks: Optional[List[Callable[[v1alpha1.Template], v1alpha1.Template]]] = None,
        manifest: Optional[Union[v1.Container, v1alpha1.ScriptTemplate, v1alpha1.ResourceTemplate]] = None,
    ) -> ContainerTemplate:
        template = cast(
            ContainerTemplate,
            super().__new__(cls, name=name, parameters_class=parameters_class, hooks=hooks, manifest=manifest),
        )
        template.image = image or cls.image
        return template


class ScriptTemplate(ExecutorTemplate[v1alpha1.ScriptTemplate]):
    image: Optional[str] = None

    def __new__(
        cls,
        *,
        name: Optional[str] = None,
        image: Optional[str] = None,
        parameters_class: Optional[type] = None,
        hooks: Optional[List[Callable[[v1alpha1.Template], v1alpha1.Template]]] = None,
        manifest: Optional[Union[v1.Container, v1alpha1.ScriptTemplate, v1alpha1.ResourceTemplate]] = None,
    ) -> ScriptTemplate:
        template = cast(
            ScriptTemplate,
            super().__new__(cls, name=name, parameters_class=parameters_class, hooks=hooks, manifest=manifest),
        )
        template.image = image or cls.image
        return template


class ResourceTemplate(ExecutorTemplate[v1alpha1.ResourceTemplate]):
    action: Literal["get", "create", "apply", "delete", "replace", "patch"]
    failureCondition: Optional[str] = None
    flags: List[str] = []
    mergeStrategy: Literal["strategic", "merge", "json"] = "strategic"
    setOwnerReference: bool = False
    successCondition: Optional[str] = None

    def __new__(
        cls,
        *,
        name: Optional[str] = None,
        parameters_class: Optional[Type] = None,
        hooks: Optional[List[Callable[[v1alpha1.Template], v1alpha1.Template]]] = None,
        manifest: Optional[Union[v1.Container, v1alpha1.ScriptTemplate, v1alpha1.ResourceTemplate]] = None,
        action: Optional[Literal["get", "create", "apply", "delete", "replace", "patch"]] = None,
        failureCondition: Optional[str] = None,
        flags: Optional[List[str]] = None,
        mergeStrategy: Optional[Literal["strategic", "merge", "json"]] = None,
        setOwnerReference: Optional[bool] = None,
        successCondition: Optional[str] = None,
    ) -> ResourceTemplate:
        template = cast(
            ResourceTemplate,
            super().__new__(cls, name=name, parameters_class=parameters_class, hooks=hooks, manifest=manifest),
        )

        if template.manifest is None:
            try:
                template.action = cls.action if action is None else action
            except AttributeError:
                raise RuntimeError("action is not specified for ResourceTemplate")

        template.failureCondition = cls.failureCondition if failureCondition is None else failureCondition
        template.flags = cls.flags if flags is None else flags
        template.mergeStrategy = cls.mergeStrategy if mergeStrategy is None else mergeStrategy
        template.setOwnerReference = cls.setOwnerReference if setOwnerReference is None else setOwnerReference
        template.successCondition = cls.successCondition if successCondition is None else successCondition
        return template
