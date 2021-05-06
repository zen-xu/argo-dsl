# generated by datamodel-codegen:
#   filename:  https://raw.githubusercontent.com/argoproj/argo-workflows/stable/api/openapi-spec/swagger.json

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from .io.argoproj.events import v1alpha1
from .io.k8s.apimachinery.pkg.apis.meta import v1


class DeleteSensorResponse(BaseModel):
    pass


class LogEntry(BaseModel):
    dependencyName: Optional[str] = Field(
        None, title="optional - trigger dependency name"
    )
    eventContext: Optional[str] = Field(None, title="optional - Cloud Event context")
    level: Optional[str] = None
    msg: Optional[str] = None
    namespace: Optional[str] = None
    sensorName: Optional[str] = None
    time: Optional[v1.Time] = None
    triggerName: Optional[str] = Field(None, title="optional - any trigger name")


class CreateSensorRequest(BaseModel):
    createOptions: Optional[v1.CreateOptions] = None
    namespace: Optional[str] = None
    sensor: Optional[v1alpha1.Sensor] = None


class SensorWatchEvent(BaseModel):
    object: Optional[v1alpha1.Sensor] = None
    type: Optional[str] = None


class UpdateSensorRequest(BaseModel):
    name: Optional[str] = None
    namespace: Optional[str] = None
    sensor: Optional[v1alpha1.Sensor] = None