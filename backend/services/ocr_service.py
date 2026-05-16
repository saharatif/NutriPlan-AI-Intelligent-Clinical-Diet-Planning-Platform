import base64
import re
from dataclasses import dataclass, field

import httpx

from utils.clinical_rules import CONDITION_ALIASES, KNOWN_ALLERGENS
from utils.config import settings


@dataclass
class ParsedBloodMarker:
    marker_name: str
    value: float | None
    unit: str | None
    reference_range: str | None
    is_abnormal: bool
    raw_text: str


@dataclass
class ParsedOcrResult:
    raw_text: str
    blood_markers: list[ParsedBloodMarker] = field(default_factory=list)
    allergens: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)


MARKER_PATTERN = re.compile(
    r"(?P<name>[A-Za-z][A-Za-z0-9 /()%.-]{1,60}?)\s*[:=-]\s*"
    r"(?P<value>-?\d+(?:\.\d+)?)\s*"
    r"(?P<unit>[A-Za-z/%]+)?"
    r"(?:\s*\(?(?:ref(?:erence)?|range)?\s*(?P<low>-?\d+(?:\.\d+)?)\s*[-–]\s*(?P<high>-?\d+(?:\.\d+)?)\)?)?",
    re.IGNORECASE,
)



class OcrService:
    async def extract_text(self, pdf_bytes: bytes) -> str:
        if not settings.MISTRAL_API_KEY:
            raise RuntimeError("MISTRAL_API_KEY is required for live OCR")

        # Mistral OCR requires the document as a base64 data-URL in a JSON body.
        b64 = base64.standard_b64encode(pdf_bytes).decode()
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.mistral.ai/v1/ocr",
                headers={
                    "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mistral-ocr-latest",
                    "document": {
                        "type": "document_url",
                        "document_url": f"data:application/pdf;base64,{b64}",
                    },
                },
            )
            response.raise_for_status()
            payload = response.json()
        pages = payload.get("pages", [])
        return "\n".join(page.get("markdown") or page.get("text") or "" for page in pages).strip()

    def parse_text(self, raw_text: str) -> ParsedOcrResult:
        markers = self._parse_blood_markers(raw_text)
        return ParsedOcrResult(
            raw_text=raw_text,
            blood_markers=markers,
            allergens=self._parse_allergens(raw_text),
            conditions=self._parse_conditions(raw_text),
        )

    async def process_pdf(self, pdf_bytes: bytes) -> ParsedOcrResult:
        return self.parse_text(await self.extract_text(pdf_bytes))

    def _parse_blood_markers(self, raw_text: str) -> list[ParsedBloodMarker]:
        markers: list[ParsedBloodMarker] = []
        for line in raw_text.splitlines():
            match = MARKER_PATTERN.search(line.strip())
            if not match:
                continue
            value = float(match.group("value"))
            low = float(match.group("low")) if match.group("low") else None
            high = float(match.group("high")) if match.group("high") else None
            reference_range = f"{low:g}-{high:g}" if low is not None and high is not None else None
            markers.append(
                ParsedBloodMarker(
                    marker_name=match.group("name").strip(),
                    value=value,
                    unit=match.group("unit"),
                    reference_range=reference_range,
                    is_abnormal=(low is not None and value < low) or (high is not None and value > high),
                    raw_text=line.strip(),
                )
            )
        return markers

    def _parse_allergens(self, raw_text: str) -> list[str]:
        lowered = raw_text.lower()
        found = {allergen for allergen in KNOWN_ALLERGENS if re.search(rf"\b{re.escape(allergen)}\b", lowered)}
        return sorted(found)

    def _parse_conditions(self, raw_text: str) -> list[str]:
        lowered = raw_text.lower()
        found = {normalised for alias, normalised in CONDITION_ALIASES.items() if re.search(rf"\b{re.escape(alias)}\b", lowered)}
        return sorted(found)
