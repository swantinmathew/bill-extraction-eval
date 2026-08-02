import json
import os
from google import genai
from src.extractors.base import BaseExtractor
from src.prompt import EXTRACTION_PROMPT
from src.schema import ExtractionResult, TaxDetails


class GeminiExtractor(BaseExtractor):
    name = "gemini"

    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def extract(self, image_path: str, bill_id: str) -> ExtractionResult:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        mime_type = "image/jpeg" if image_path.lower().endswith((".jpg", ".jpeg")) else "image/png"

        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                {"inline_data": {"mime_type": mime_type, "data": image_bytes}},
                EXTRACTION_PROMPT
            ]
        )

        input_tokens = output_tokens = None
        usage = getattr(response, "usage_metadata", None)
        if usage:
            input_tokens = getattr(usage, "prompt_token_count", None)
            output_tokens = getattr(usage, "candidates_token_count", None)

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        try:
            data = json.loads(raw_text)
            return ExtractionResult(
                bill_id=bill_id, model_name=self.name,
                vendor=data.get("vendor"), invoice_number=data.get("invoice_number"),
                date=data.get("date"), amount=data.get("amount"),
                currency=data.get("currency", "INR"),
                tax_details=TaxDetails(**(data.get("tax_details") or {})),
                raw_response=raw_text,
                input_tokens=input_tokens, output_tokens=output_tokens,
            )
        except (json.JSONDecodeError, TypeError):
            return ExtractionResult(
                bill_id=bill_id, model_name=self.name, raw_response=raw_text,
                input_tokens=input_tokens, output_tokens=output_tokens,
            )