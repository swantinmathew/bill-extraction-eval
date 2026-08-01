import streamlit as st
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

st.set_page_config(page_title="Bill Extraction Comparison", layout="wide")
st.title("Handwritten Bill Extraction — Model Comparison")

GROUND_TRUTH = json.loads(Path("data/ground_truth.json").read_text())
RAW_OUTPUTS = Path("results/raw_outputs")

bill_ids = sorted(GROUND_TRUTH.keys())
selected = st.selectbox("Select a bill", bill_ids)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Bill Image")
    for ext in (".jpg", ".jpeg", ".png"):
        img_path = Path(f"data/raw_bills/{selected}{ext}")
        if img_path.exists():
            st.image(str(img_path))
            break

with col2:
    st.subheader("Ground Truth")
    st.json(GROUND_TRUTH[selected])

with col3:
    st.subheader("Model Outputs")
    for model_dir in RAW_OUTPUTS.iterdir():
        if model_dir.is_dir():
            out_file = model_dir / f"{selected}.json"
            if out_file.exists():
                st.markdown(f"**{model_dir.name}**")
                st.json(json.loads(out_file.read_text()))