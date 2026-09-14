from threading import Lock
from .adapters import ProtocolAdapter
from .domain import Entity, EntityKind, Event, Protocol
from .events import EventPublisher
from .registry import EntityRegistry


class EntityNotFound(Exception):
    pass


class UnsupportedOperation(Exception):
    pass


class EntityService:
    def __init__(self, registry: EntityRegistry, adapters: dict[Protocol, ProtocolAdapter], publisher: EventPublisher):
        self.registry, self.adapters, self.publisher = registry, adapters, publisher
        self._sequence = 0
        self._lock = Lock()

    def _hydrate(self, entity: Entity) -> Entity:
        return entity.model_copy(update={"state": self.adapters[entity.protocol].read(entity)})

    def list_entities(self) -> list[Entity]:
        return [self._hydrate(entity) for entity in self.registry.all()]

    def get_entity(self, entity_id: str) -> Entity:
        entity = self.registry.get(entity_id)
        if entity is None:
            raise EntityNotFound(entity_id)
        return self._hydrate(entity)

    def set_light(self, entity_id: str, on: bool) -> Entity:
        entity = self.registry.get(entity_id)
        if entity is None:
            raise EntityNotFound(entity_id)
        if entity.kind != EntityKind.LIGHT or "on_off" not in entity.capabilities:
            raise UnsupportedOperation(entity_id)
        state = self.adapters[entity.protocol].set_light(entity, on)
        with self._lock:
            self._sequence += 1
            sequence = self._sequence
        result = entity.model_copy(update={"state": state})
        self.publisher.publish(Event(entity_id=entity.id, protocol=entity.protocol, state=state, sequence=sequence))
        return result
