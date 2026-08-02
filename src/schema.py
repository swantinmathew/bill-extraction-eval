from pydantic import BaseModel
from typing import Optional

class TaxDetails(BaseModel):
    gst_number: Optional[str] = None
    gst_amount: Optional[float] = None

class ExtractionResult(BaseModel):
    bill_id: str
    model_name: str
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "INR"
    tax_details: TaxDetails = TaxDetails()
    raw_response: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None