from .domain import Entity, EntityKind, Protocol


class EntityRegistry:
    def __init__(self, entities: list[Entity]):
        ids = [entity.id for entity in entities]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate entity id")
        self._entities = {entity.id: entity for entity in entities}

    def all(self) -> list[Entity]:
        return list(self._entities.values())

    def get(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)


def demo_registry() -> EntityRegistry:
    return EntityRegistry([
        Entity(id="can-light-1", name="Simulated CAN cabin light", kind=EntityKind.LIGHT, protocol=Protocol.CAN, address="can:node-1:output-1", capabilities=["on_off"]),
        Entity(id="zigbee-light-1", name="Simulated Zigbee cabin light", kind=EntityKind.LIGHT, protocol=Protocol.ZIGBEE, address="zigbee:0x1234:ep1", capabilities=["on_off"]),
        Entity(id="can-temp-1", name="Simulated CAN temperature", kind=EntityKind.TEMPERATURE, protocol=Protocol.CAN, address="can:node-1:temp-1", capabilities=["read_temperature"]),
        Entity(id="zigbee-temp-1", name="Simulated Zigbee temperature", kind=EntityKind.TEMPERATURE, protocol=Protocol.ZIGBEE, address="zigbee:0x1234:temp", capabilities=["read_temperature"]),
        Entity(id="can-switch-1", name="Simulated CAN switch", kind=EntityKind.SWITCH, protocol=Protocol.CAN, address="can:node-1:switch-1", capabilities=["read_on_off"]),
    ])
