import json, os, base64
from openai import OpenAI
from src.extractors.base import BaseExtractor
from src.prompt import EXTRACTION_PROMPT
from src.schema import ExtractionResult, TaxDetails

class OpenAIExtractor(BaseExtractor):
    name = "openai"

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENROUTER_API_KEY"),base_url="https://openrouter.ai/api/v1")

    def extract(self, image_path: str, bill_id: str) -> ExtractionResult:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        response = self.client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": EXTRACTION_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }]
        )

        raw_text = response.choices[0].message.content.strip()
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
                raw_response=raw_text
            )
        except (json.JSONDecodeError, TypeError):
            return ExtractionResult(bill_id=bill_id, model_name=self.name, raw_response=raw_text)