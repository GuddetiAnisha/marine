import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from .adapters import AdapterError, make_adapters
from .config import Settings
from .domain import Entity, LightCommand
from .events import MqttPublisher, NullPublisher
from .registry import demo_registry
from .service import EntityNotFound, EntityService, UnsupportedOperation


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({"level": record.levelname, "logger": record.name, "message": record.getMessage()})


def create_app(settings: Settings | None = None, service: EntityService | None = None) -> FastAPI:
    settings = settings or Settings()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.getLogger("bridge").addHandler(handler)
    logging.getLogger("bridge").setLevel(settings.log_level.upper())
    publisher = None
    if service is None:
        publisher = MqttPublisher(settings.mqtt_host, settings.mqtt_port, settings.mqtt_topic_prefix) if settings.mqtt_enabled else NullPublisher()
        service = EntityService(demo_registry(), make_adapters(), publisher)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        if isinstance(publisher, MqttPublisher):
            publisher.close()

    app = FastAPI(title="Marine Entity Bridge (Simulated PoC)", version="0.1.0", lifespan=lifespan)
    app.state.service = service

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "simulation", "mqtt_enabled": settings.mqtt_enabled}

    @app.get("/api/v1/entities", response_model=list[Entity])
    def entities(request: Request):
        return request.app.state.service.list_entities()

    @app.get("/api/v1/entities/{entity_id}", response_model=Entity)
    def get_entity(entity_id: str, request: Request):
        try:
            return request.app.state.service.get_entity(entity_id)
        except EntityNotFound:
            raise HTTPException(404, "Entity not found")
        except AdapterError as exc:
            raise HTTPException(502, str(exc))

    @app.put("/api/v1/entities/{entity_id}/light", response_model=Entity)
    def set_light(entity_id: str, command: LightCommand, request: Request):
        try:
            result = request.app.state.service.set_light(entity_id, command.on)
            logging.getLogger("bridge.api").info("light_command entity_id=%s on=%s", entity_id, command.on)
            return result
        except EntityNotFound:
            raise HTTPException(404, "Entity not found")
        except UnsupportedOperation:
            raise HTTPException(409, "Entity does not support on/off")
        except AdapterError as exc:
            raise HTTPException(502, str(exc))
        except Exception:
            logging.getLogger("bridge.api").exception("command_delivery_failed entity_id=%s", entity_id)
            raise HTTPException(503, "Command applied locally but event delivery failed")

    return app


app = create_app()
