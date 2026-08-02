import json
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent.parent))
from src.eval.scorer import score_field

# ---------- paths ----------
GROUND_TRUTH_PATH = Path("data/ground_truth.json")
RAW_BILLS_DIR = Path("data/raw_bills")
RAW_OUTPUTS_DIR = Path("results/raw_outputs")
FIELDS = ["vendor", "invoice_number", "date", "amount", "currency"]
TAX_FIELDS = ["gst_number", "gst_amount"]

st.set_page_config(page_title="Bill Extraction Audit", page_icon="\U0001F4D2", layout="wide")

# ---------- design tokens ----------
# paper cream / ink navy / stamp rust — evokes an old ledger book, not a dashboard
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Source+Serif+4:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap');

    :root {
        --paper: #F6F1E7;
        --paper-dim: #EDE6D5;
        --ink: #1F2A3C;
        --ink-soft: #5B5648;
        --stamp: #B23A2E;
        --match: #4E7A51;
        --mismatch: #B23A2E;
        --hairline: #D8CFB8;
    }

    .stApp { background-color: var(--paper); }
    html, body, [class*="css"] { color: var(--ink); }

    h1, h2, h3 { font-family: 'Fraunces', serif !important; letter-spacing: -0.01em; }

    .eyebrow {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--stamp);
        margin-bottom: -0.6rem;
    }

    .ledger-title {
        font-family: 'Fraunces', serif;
        font-weight: 700;
        font-size: 2.4rem;
        margin-top: 0.2rem;
        border-bottom: 2px solid var(--ink);
        padding-bottom: 0.5rem;
    }

    .receipt-frame {
        background: #fff;
        border: 1px solid var(--hairline);
        padding: 0.75rem;
        box-shadow: 3px 4px 0 rgba(31,42,60,0.08);
        transform: rotate(-0.6deg);
    }

    .ledger-card {
        background: var(--paper-dim);
        border: 1px solid var(--hairline);
        border-radius: 2px;
        padding: 1.1rem 1.3rem;
        font-family: 'Source Serif 4', serif;
    }

    .ledger-card h4 {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--ink-soft);
        margin: 0 0 0.7rem 0;
        border-bottom: 1px dashed var(--hairline);
        padding-bottom: 0.4rem;
    }

    .field-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        padding: 0.28rem 0;
        border-bottom: 1px dotted var(--hairline);
        font-size: 0.95rem;
    }
    .field-row:last-child { border-bottom: none; }

    .field-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: var(--ink-soft);
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .field-value { font-family: 'JetBrains Mono', monospace; font-size: 0.92rem; }
    .match { color: var(--match); }
    .mismatch { color: var(--mismatch); }

    .mark { font-size: 0.85rem; margin-right: 0.35rem; }

    .stamp {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.95rem;
        color: var(--stamp);
        border: 2px solid var(--stamp);
        border-radius: 50%;
        width: 92px;
        height: 92px;
        line-height: 1.1;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        transform: rotate(-8deg);
        opacity: 0.88;
        margin: 0 auto;
    }

    .stamp-label {
        text-align: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--ink-soft);
        margin-top: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- data ----------
if not GROUND_TRUTH_PATH.exists():
    st.error("data/ground_truth.json not found. Run this from the repo root.")
    st.stop()

ground_truth = json.loads(GROUND_TRUTH_PATH.read_text())
bill_ids = sorted(ground_truth.keys())
model_dirs = sorted([d for d in RAW_OUTPUTS_DIR.iterdir() if d.is_dir()]) if RAW_OUTPUTS_DIR.exists() else []

# ---------- header ----------
st.markdown('<div class="eyebrow">Field-by-field verification</div>', unsafe_allow_html=True)
st.markdown('<div class="ledger-title">Bill Extraction Audit</div>', unsafe_allow_html=True)
st.write("")

tab_dataset, tab_upload = st.tabs(["Evaluation dataset", "Upload a bill"])

# ==================== TAB 1: existing dataset comparison ====================
with tab_dataset:
    selected = st.selectbox("Bill", bill_ids, label_visibility="collapsed")
    st.write("")

    truth = ground_truth[selected]

    col_img, col_truth, *col_models = st.columns([1.1, 1, *([1] * len(model_dirs))])

    with col_img:
        st.markdown('<div class="field-label">Original</div>', unsafe_allow_html=True)
        image_path = None
        for ext in (".jpg", ".jpeg", ".png"):
            candidate = RAW_BILLS_DIR / f"{selected}{ext}"
            if candidate.exists():
                image_path = candidate
                break
        if image_path:
            st.markdown('<div class="receipt-frame">', unsafe_allow_html=True)
            st.image(str(image_path), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No image found for this bill.")

    with col_truth:
        st.markdown('<div class="ledger-card"><h4>Ground truth</h4>', unsafe_allow_html=True)
        for field in FIELDS:
            val = truth.get(field)
            display = val if val is not None else "\u2014"
            st.markdown(
                f'<div class="field-row"><span class="field-label">{field}</span>'
                f'<span class="field-value">{display}</span></div>',
                unsafe_allow_html=True,
            )
        truth_tax = truth.get("tax_details", {}) or {}
        for tax_field in TAX_FIELDS:
            val = truth_tax.get(tax_field)
            display = val if val is not None else "\u2014"
            st.markdown(
                f'<div class="field-row"><span class="field-label">{tax_field}</span>'
                f'<span class="field-value">{display}</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    for col, model_dir in zip(col_models, model_dirs):
        out_path = model_dir / f"{selected}.json"
        with col:
            st.markdown(f'<div class="ledger-card"><h4>{model_dir.name}</h4>', unsafe_allow_html=True)
            if out_path.exists():
                pred = json.loads(out_path.read_text())
                scores = []
                for field in FIELDS:
                    pred_val = pred.get(field)
                    truth_val = truth.get(field)
                    score = score_field(field, truth_val, pred_val)
                    scores.append(score)
                    is_match = score >= 0.85
                    mark = "\u2713" if is_match else "\u2717"
                    css_class = "match" if is_match else "mismatch"
                    display = pred_val if pred_val is not None else "\u2014"
                    st.markdown(
                        f'<div class="field-row"><span class="field-label">{field}</span>'
                        f'<span class="field-value {css_class}"><span class="mark">{mark}</span>{display}</span></div>',
                        unsafe_allow_html=True,
                    )
                pred_tax = pred.get("tax_details", {}) or {}
                truth_tax = truth.get("tax_details", {}) or {}
                for tax_field in TAX_FIELDS:
                    pred_val = pred_tax.get(tax_field)
                    truth_val = truth_tax.get(tax_field)
                    is_match = (str(pred_val) == str(truth_val)) if (truth_val is not None or pred_val is not None) else True
                    mark = "\u2713" if is_match else "\u2717"
                    css_class = "match" if is_match else "mismatch"
                    display = pred_val if pred_val is not None else "\u2014"
                    st.markdown(
                        f'<div class="field-row"><span class="field-label">{tax_field}</span>'
                        f'<span class="field-value {css_class}"><span class="mark">{mark}</span>{display}</span></div>',
                        unsafe_allow_html=True,
                    )
                st.markdown('</div>', unsafe_allow_html=True)
                avg = sum(scores) / len(scores)
                st.markdown(
                    f'<div style="margin-top:0.9rem;">'
                    f'<div class="stamp">{avg*100:.0f}%</div>'
                    f'<div class="stamp-label">accuracy</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.write("No output for this bill.")
                st.markdown('</div>', unsafe_allow_html=True)

# ==================== TAB 2: live upload + extraction ====================
with tab_upload:
    st.markdown(
        '<p style="font-family:\'Source Serif 4\',serif; color:var(--ink-soft); font-size:0.95rem;">'
        'Upload a photo of a handwritten bill to see how each configured model reads it. '
        'Extraction only runs when you click the button below \u2014 it calls live APIs and '
        'counts against your usage quota.</p>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader("Upload a bill image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

    if uploaded_file is not None:
        col_preview, _ = st.columns([1, 2])
        with col_preview:
            st.markdown('<div class="receipt-frame">', unsafe_allow_html=True)
            st.image(uploaded_file, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        run_extraction = st.button("Extract & compare", type="primary")

        # cache result in session_state, keyed by filename+size, so a Streamlit
        # rerun (e.g. from an unrelated widget interaction) never re-fires the APIs
        cache_key = f"{uploaded_file.name}_{uploaded_file.size}"

        if run_extraction:
            temp_path = Path("data/raw_bills/_temp_upload.jpg")
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.write_bytes(uploaded_file.getvalue())

            live_results = {}

            import os

            if os.getenv("GEMINI_API_KEY"):
                try:
                    from src.extractors.gemini_extractor import GeminiExtractor
                    with st.spinner("Gemini reading the bill..."):
                        result = GeminiExtractor().extract(str(temp_path), "_temp_upload")
                    live_results["gemini"] = json.loads(result.model_dump_json())
                except Exception as e:
                    live_results["gemini"] = {"error": str(e)}

            if os.getenv("OPENROUTER_API_KEY"):
                try:
                    from src.extractors.openai_extractor import OpenAIExtractor
                    with st.spinner("OpenAI reading the bill..."):
                        result = OpenAIExtractor().extract(str(temp_path), "_temp_upload")
                    live_results["openai"] = json.loads(result.model_dump_json())
                except Exception as e:
                    live_results["openai"] = {"error": str(e)}

            st.session_state[cache_key] = live_results
            temp_path.unlink(missing_ok=True)

        if cache_key in st.session_state:
            st.write("")
            if not st.session_state[cache_key]:
                st.warning("No models ran. Check that GEMINI_API_KEY and/or OPENROUTER_API_KEY are set in your .env file.")
            else:
                result_cols = st.columns(len(st.session_state[cache_key]))
                for col, (model_name, pred) in zip(result_cols, st.session_state[cache_key].items()):
                    with col:
                        st.markdown(f'<div class="ledger-card"><h4>{model_name}</h4>', unsafe_allow_html=True)
                        if "error" in pred:
                            st.markdown(
                                f'<div class="field-value mismatch">Request failed: {pred["error"][:120]}</div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            for field in FIELDS:
                                display = pred.get(field) if pred.get(field) is not None else "\u2014"
                                st.markdown(
                                    f'<div class="field-row"><span class="field-label">{field}</span>'
                                    f'<span class="field-value">{display}</span></div>',
                                    unsafe_allow_html=True,
                                )
                            pred_tax = pred.get("tax_details", {}) or {}
                            for tax_field in TAX_FIELDS:
                                display = pred_tax.get(tax_field) if pred_tax.get(tax_field) is not None else "\u2014"
                                st.markdown(
                                    f'<div class="field-row"><span class="field-label">{tax_field}</span>'
                                    f'<span class="field-value">{display}</span></div>',
                                    unsafe_allow_html=True,
                                )
                        st.markdown('</div>', unsafe_allow_html=True)

                st.caption("No ground truth exists for an uploaded bill, so results are shown without accuracy scoring \u2014 read them side by side and judge for yourself.")
    else:
        st.info("Choose an image to get started.")