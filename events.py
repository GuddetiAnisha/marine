import json
import logging
from typing import Protocol as TypingProtocol
from .domain import Event

logger = logging.getLogger(__name__)


class EventPublisher(TypingProtocol):
    def publish(self, event: Event) -> None: ...


class NullPublisher:
    def publish(self, event: Event) -> None:
        pass


class MqttPublisher:
    def __init__(self, host: str, port: int, prefix: str):
        import paho.mqtt.client as mqtt
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.connect(host, port, keepalive=30)
        self._client.loop_start()
        self._prefix = prefix.strip("/")

    def publish(self, event: Event) -> None:
        topic = f"{self._prefix}/entities/{event.entity_id}/state"
        info = self._client.publish(topic, event.model_dump_json(), qos=1, retain=True)
        if info.rc != 0:
            raise RuntimeError(f"MQTT publish failed: {info.rc}")

    def close(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
