import asyncio
import logging
from uuid import UUID
from app.database import get_db
from app.services.visual_validator import perform_visual_validation
from app.services.ai_client import execute_asesmen_sosial_logic_async

logger = logging.getLogger(__name__)

class AsesmenQueue:
    def __init__(self):
        self.queue = None
        self._worker_task = None
        self._loop = None

    def _init_queue(self):
        if self.queue is None:
            self._loop = asyncio.get_event_loop()
            self.queue = asyncio.Queue()

    def start_worker(self):
        self._init_queue()
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = self._loop.create_task(self._worker())

    async def _worker(self):
        while True:
            task_data = await self.queue.get()
            keluarga_id, user_id, task_type = task_data
            try:
                db_gen = get_db()
                db = next(db_gen)
                try:
                    if task_type == "visual":
                        logger.info(f"[Queue Worker] Memulai validasi visual untuk KK {keluarga_id}")
                        await perform_visual_validation(keluarga_id, user_id, db)
                    elif task_type == "asesmen":
                        logger.info(f"[Queue Worker] Memulai asesmen sosial untuk KK {keluarga_id}")
                        await execute_asesmen_sosial_logic_async(keluarga_id, user_id, db)
                except Exception as e:
                    logger.error(f"[Queue Worker Exec Error] {e}", exc_info=True)
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"[Queue Worker DB Error] {e}", exc_info=True)
            finally:
                self.queue.task_done()

    def add_task(self, keluarga_id: UUID, user_id: UUID, task_type: str):
        self._init_queue()
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(
                self.queue.put_nowait, (keluarga_id, user_id, task_type)
            )
            self._loop.call_soon_threadsafe(self.start_worker)
        else:
            self.queue.put_nowait((keluarga_id, user_id, task_type))
            self.start_worker()

asesmen_queue = AsesmenQueue()


async def run_async_assessment(keluarga_id: UUID, user_id: UUID):
    asesmen_queue.add_task(keluarga_id, user_id, "asesmen")


async def run_async_visual_validation(keluarga_id: UUID, user_id: UUID):
    asesmen_queue.add_task(keluarga_id, user_id, "visual")
