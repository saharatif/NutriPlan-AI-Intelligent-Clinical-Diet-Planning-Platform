import asyncio
import uuid
from collections.abc import Callable

from db.database import AsyncSessionLocal
from services.diet_plan_service import DietPlanService
from workers.celery_app import celery_app


@celery_app.task(name="workers.task_diet_plan.generate_diet_plan", bind=True)
def generate_diet_plan(
    self,
    patient_id: str,
    selected_favourites: list[str] | None = None,
    plan_type: str = "standard",
) -> str:
    async def _run() -> str:
        def on_progress(current: int, total: int) -> None:
            self.update_state(
                state="PROGRESS",
                meta={"progress": round(current / total * 100), "current": current, "total": total},
            )

        async with AsyncSessionLocal() as db:
            plan = await DietPlanService(db).generate_plan(
                uuid.UUID(patient_id),
                selected_favourites or [],
                plan_type,
                progress_callback=on_progress,
            )
            await db.commit()
            return str(plan.id)

    return asyncio.run(_run())
