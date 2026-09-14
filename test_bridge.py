from fastapi.testclient import TestClient
from bridge.adapters import make_adapters
from bridge.api import create_app
from bridge.config import Settings
from bridge.domain import Event, Protocol
from bridge.registry import demo_registry
from bridge.service import EntityService


class RecordingPublisher:
    def __init__(self):
        self.events: list[Event] = []

    def publish(self, event: Event):
        self.events.append(event)


def fixture():
    publisher = RecordingPublisher()
    adapters = make_adapters()
    service = EntityService(demo_registry(), adapters, publisher)
    client = TestClient(create_app(Settings(mqtt_enabled=False), service))
    return client, adapters, publisher


def test_identical_api_command_controls_both_protocols():
    client, adapters, publisher = fixture()
    for entity_id in ("can-light-1", "zigbee-light-1"):
        response = client.put(f"/api/v1/entities/{entity_id}/light", json={"on": True})
        assert response.status_code == 200
        assert response.json()["state"] == {"on": True}
        assert client.get(f"/api/v1/entities/{entity_id}").json()["state"] == {"on": True}
    assert adapters[Protocol.CAN].command_log == [{"address": "can:node-1:output-1", "operation": "set_light", "on": True}]
    assert adapters[Protocol.ZIGBEE].command_log == [{"address": "zigbee:0x1234:ep1", "operation": "set_light", "on": True}]
    assert [event.entity_id for event in publisher.events] == ["can-light-1", "zigbee-light-1"]
    assert [event.sequence for event in publisher.events] == [1, 2]


def test_capability_and_input_errors():
    client, _, _ = fixture()
    assert client.put("/api/v1/entities/can-temp-1/light", json={"on": True}).status_code == 409
    assert client.put("/api/v1/entities/unknown/light", json={"on": True}).status_code == 404
    assert client.put("/api/v1/entities/can-light-1/light", json={"on": "invalid"}).status_code == 422
    assert client.get("/health").json()["mode"] == "simulation"
    entities = client.get("/api/v1/entities").json()
    assert len(entities) == 5
    assert {e["kind"] for e in entities} == {"light", "switch", "temperature_sensor"}


def test_state_is_isolated_between_app_instances():
    first, _, _ = fixture()
    second, _, _ = fixture()
    first.put("/api/v1/entities/can-light-1/light", json={"on": True})
    assert second.get("/api/v1/entities/can-light-1").json()["state"] == {"on": False}
