from enum import Enum
from pydantic import BaseModel, Field


class Protocol(str, Enum):
    CAN = "can_sim"
    ZIGBEE = "zigbee_sim"


class EntityKind(str, Enum):
    LIGHT = "light"
    SWITCH = "switch"
    TEMPERATURE = "temperature_sensor"


class Entity(BaseModel):
    id: str
    name: str
    kind: EntityKind
    protocol: Protocol
    address: str
    capabilities: list[str] = Field(default_factory=list)
    state: dict[str, bool | float | str | None] = Field(default_factory=dict)


class LightCommand(BaseModel):
    on: bool


class Event(BaseModel):
    entity_id: str
    protocol: Protocol
    state: dict[str, bool | float | str | None]
    sequence: int
