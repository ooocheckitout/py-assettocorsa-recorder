import ctypes
import logging
from time import sleep
from typing import Any

from acevo import ACEvoSharedMemory
from acevo.models.static import StaticPage
from acevo.models.enums import ACEVO_SESSION_TYPE, ACEVO_STATUS

from session import Session

logger = logging.getLogger(__name__)


def serialize_page(value: object) -> Any:
    if isinstance(value, ctypes.Structure):
        return {name: serialize_page(getattr(value, name)) for name, *_ in value._fields_}
    if isinstance(value, ctypes.Array):
        return [serialize_page(item) for item in value]
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def capture_driving(memory: ACEvoSharedMemory, static: StaticPage, *, retry_capture_in_sec: float) -> None:
    static_page = serialize_page(static)
    graphics_page = serialize_page(memory.read_graphics())
    session_name = static_page["session_name"]
    logger.info("Capturing '%s' session.", session_name)

    with Session(static_page["track"], graphics_page["car_model"]) as session:
        session.append(static_page)

        while True:
            sleep(retry_capture_in_sec)
            snapshot = memory.read_snapshot()

            if snapshot.static.session == ACEVO_SESSION_TYPE.AC_UNKNOWN:
                logger.info("Session '%s' has ended.", session_name)
                return

            if snapshot.graphics.status != ACEVO_STATUS.AC_LIVE:
                continue

            if snapshot.graphics.is_in_pit_box:
                continue

            session.append(serialize_page(snapshot.physics))
            session.append(serialize_page(snapshot.graphics))


def connect_and_capture() -> None:
    with ACEvoSharedMemory() as memory:
        static = memory.read_static()

        if static.session == ACEVO_SESSION_TYPE.AC_UNKNOWN:
            return

        logger.info("Connected to Assetto Corsa.")

        capture_driving(memory, static, retry_capture_in_sec=1 / 30)

    logger.info("Disconnected from Assetto Corsa.")
