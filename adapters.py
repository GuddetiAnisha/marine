"""Adapter boundary: replace simulators with hardware-backed implementations later.

No real CAN frames, PGNs, Zigbee clusters, or radio traffic are emitted here.
"""
from abc import ABC, abstractmethod
from threading import Lock
from .domain import Entity, EntityKind, Protocol


class AdapterError(Exception):
    pass


class ProtocolAdapter(ABC):
    protocol: Protocol

    @abstractmethod
    def read(self, entity: Entity) -> dict:
        raise NotImplementedError

    @abstractmethod
    def set_light(self, entity: Entity, on: bool) -> dict:
        raise NotImplementedError


class SimulatedAdapter(ProtocolAdapter):
    def __init__(self, protocol: Protocol, initial: dict[str, dict]):
        self.protocol = protocol
        self._states = {key: value.copy() for key, value in initial.items()}
        self._lock = Lock()
        self.command_log: list[dict] = []

    def read(self, entity: Entity) -> dict:
        with self._lock:
            if entity.address not in self._states:
                raise AdapterError(f"Unknown simulated address: {entity.address}")
            return self._states[entity.address].copy()

    def set_light(self, entity: Entity, on: bool) -> dict:
        if entity.kind != EntityKind.LIGHT or entity.protocol != self.protocol:
            raise AdapterError("Adapter cannot control this entity")
        with self._lock:
            if entity.address not in self._states:
                raise AdapterError(f"Unknown simulated address: {entity.address}")
            # This command record stands in for a CAN/J1939-style or Zigbee action.
            self.command_log.append({"address": entity.address, "operation": "set_light", "on": on})
            self._states[entity.address]["on"] = on
            return self._states[entity.address].copy()


def make_adapters() -> dict[Protocol, ProtocolAdapter]:
    return {
        Protocol.CAN: SimulatedAdapter(Protocol.CAN, {"can:node-1:output-1": {"on": False}, "can:node-1:temp-1": {"celsius": 21.5}, "can:node-1:switch-1": {"on": False}}),
        Protocol.ZIGBEE: SimulatedAdapter(Protocol.ZIGBEE, {"zigbee:0x1234:ep1": {"on": False}, "zigbee:0x1234:temp": {"celsius": 22.0}}),
    }
