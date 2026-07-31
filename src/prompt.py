EXTRACTION_PROMPT = """You are reading a handwritten Indian bill/receipt image.
Extract the following fields as strict JSON, no markdown, no explanation:

{
  "vendor": string or null,
  "invoice_number": string or null,
  "date": string in YYYY-MM-DD format or null,
  "amount": number or null,
  "currency": string, default "INR",
  "tax_details": {"gst_number": string or null, "gst_amount": number or null}
}

If a field is not visible or illegible, use null. Do not guess.
Return only the JSON object."""