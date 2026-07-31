import base64, json, os
from anthropic import Anthropic
from src.extractors.base import BaseExtractor
from src.prompt import EXTRACTION_PROMPT
from src.schema import ExtractionResult, TaxDetails

class ClaudeExtractor(BaseExtractor):
    name = "claude"

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def extract(self, image_path: str, bill_id: str) -> ExtractionResult:
        with open(image_path, "rb") as f:
            img_b64 = base64.standard_b64encode(f.read()).decode()

        media_type = "image/jpeg" if image_path.lower().endswith((".jpg", ".jpeg")) else "image/png"

        response = self.client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_b64}},
                    {"type": "text", "text": EXTRACTION_PROMPT}
                ]
            }]
        )

        raw_text = response.content[0].text
        try:
            data = json.loads(raw_text)
            return ExtractionResult(
                bill_id=bill_id, model_name=self.name,
                vendor=data.get("vendor"), invoice_number=data.get("invoice_number"),
                date=data.get("date"), amount=data.get("amount"),
                currency=data.get("currency", "INR"),
                tax_details=TaxDetails(**data.get("tax_details", {})),
                raw_response=raw_text
            )
        except (json.JSONDecodeError, TypeError):
            return ExtractionResult(bill_id=bill_id, model_name=self.name, raw_response=raw_text)