import logging
from time import sleep

from acrally import ACRallySharedMemory
from acrally.models.static import StaticPage

from lib import serialize_page
from session import Session

logger = logging.getLogger(__name__)


def capture_driving(memory: ACRallySharedMemory, static: StaticPage, *, retry_capture_in_sec: float) -> None:
    logger.info("Capturing '%s' stage.", static.track)

    with Session(static.track, static.car_model) as session:
        session.append(serialize_page(static))

        while True:
            sleep(retry_capture_in_sec)
            snapshot = memory.read_snapshot()

            if snapshot.static.track != static.track:
                logger.info("Stage '%s' has ended.", static.track)
                return

            session.append(serialize_page(snapshot.physics))
            session.append(serialize_page(snapshot.graphics))


def connect_and_capture() -> None:
    with ACRallySharedMemory() as memory:
        static = memory.read_static()

        if not static.track:
            return

        logger.info("Connected to Assetto Corsa Rally.")

        capture_driving(memory, static, retry_capture_in_sec=1 / 30)

    logger.info("Disconnected from Assetto Corsa Rally.")
