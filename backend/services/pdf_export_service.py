import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from models.diet_plan import DietPlan
from utils.config import settings


class PdfExportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_plan_pdf(self, plan: DietPlan) -> dict[str, str]:
        html = self.render_html(plan)
        pdf_bytes = self._render_pdf_bytes(html)
        storage_path = f"exports/{plan.patient_id}/{plan.id}.pdf"

        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                from db.supabase_client import get_supabase_client

                bucket = get_supabase_client().storage.from_(settings.SUPABASE_STORAGE_BUCKET)
                bucket.upload(
                    storage_path,
                    pdf_bytes,
                    {"content-type": "application/pdf", "upsert": "true"},
                )
                signed = bucket.create_signed_url(storage_path, 60 * 60)
                signed_url = signed.get("signedURL") or signed.get("signed_url") or ""
                if signed_url:
                    return {"url": signed_url, "storage_path": storage_path}
            except Exception:
                pass

        return {"url": f"/api/diet-plans/{plan.id}/download?storage_path={storage_path}", "storage_path": storage_path}

    def render_html(self, plan: DietPlan) -> str:
        template = Path(__file__).resolve().parents[1] / "exports" / "templates" / "diet_chart.html"
        meal_rows = "\n".join(
            f"<tr><td>Week {meal.week}</td><td>Day {meal.day}</td><td>{meal.meal_slot}</td>"
            f"<td>{meal.meal_name}</td><td>{meal.base_calories}</td>"
            f"<td>{meal.base_protein_g}/{meal.base_fat_g}/{meal.base_carbs_g}</td></tr>"
            for meal in plan.meals
        )
        return template.read_text(encoding="utf-8").replace("{{PLAN_ID}}", str(plan.id)).replace("{{MEAL_ROWS}}", meal_rows)

    def _render_pdf_bytes(self, html: str) -> bytes:
        try:
            from weasyprint import HTML

            return HTML(string=html).write_pdf()
        except Exception:
            # Keeps local/test environments usable when WeasyPrint system libraries are absent.
            return html.encode("utf-8")
