import re
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image, ImageOps, ImageEnhance

st.set_page_config(page_title="CurrentIQ", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.stApp {background:#f4f7fb}
.block-container {max-width:1200px;padding-top:1.2rem}
.hero {padding:24px 28px;border-radius:18px;color:white;
       background:linear-gradient(110deg,#102a43,#176b87);margin-bottom:16px}
.hero h1 {color:white;margin:0}
.hero p {color:#e3f1f6;margin:7px 0 0}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="hero"><h1>⚡ CurrentIQ</h1>'
    '<p>Understand your electricity bill • Track usage • Plan ahead</p></div>',
    unsafe_allow_html=True,
)
st.caption(
    "Student MVP • Independent prototype • Not affiliated with any electricity provider or government."
)

# Keep application data keys separate from Streamlit widget/form keys.
if "currentiq_history" not in st.session_state:
    st.session_state["currentiq_history"] = pd.DataFrame({
        "Month": ["May", "Jun", "Jul", "Aug", "Sep", "Oct"],
        "Units (kWh)": [142, 158, 151, 173, 166, 181],
    })
if "currentiq_bill" not in st.session_state:
    st.session_state["currentiq_bill"] = {
        "month": "November 2026", "units": 181.0, "energy": 1086.0,
        "fixed": 40.0, "duty": 54.3, "other": 0.0,
    }

def money(value):
    return f"₹{float(value):,.2f}"

def run_tesseract(image):
    """Run OCR and provide a useful message if the system OCR engine is absent."""
    try:
        import pytesseract
        return pytesseract.image_to_string(image, lang="eng", config="--psm 6")
    except Exception as exc:
        message = str(exc).lower()
        if "not found" in message or "not installed" in message or "tesseract" in message:
            raise RuntimeError(
                "The Tesseract OCR engine is unavailable on this deployment. "
                "Check that packages.txt contains tesseract-ocr and redeploy."
            ) from exc
        raise RuntimeError(f"OCR could not read this file: {exc}") from exc

def extract_image(upload):
    upload.seek(0)
    image = Image.open(upload).convert("RGB")
    image = ImageOps.grayscale(image)
    image = ImageEnhance.Contrast(image).enhance(1.7)
    image = ImageEnhance.Sharpness(image).enhance(1.4)
    return run_tesseract(image)

def extract_pdf(upload):
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PDF support is missing. Install PyMuPDF from requirements.txt.") from exc

    doc = fitz.open(stream=upload.getvalue(), filetype="pdf")
    pages = []
    for page in doc:
        text = page.get_text("text").strip()
        if text:
            pages.append(text)
        else:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")
            pages.append(run_tesseract(ImageOps.grayscale(image)))
    return "\n\n".join(pages)

def find_number(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            raw = match.group(1).replace(",", "").strip()
            try:
                return float(raw)
            except ValueError:
                continue
    return None

def suggest_values(text):
    # Best-effort label matching only. User must verify every suggested value.
    return {
        "units": find_number(text, [
            r"(?:units\s+consumed|consumption\s+units|consumption|units|kwh)\s*[:=\-]?\s*([0-9,]+(?:\.[0-9]+)?)",
            r"([0-9,]+(?:\.[0-9]+)?)\s*(?:kwh|units)\b",
        ]),
        "energy": find_number(text, [
            r"(?:energy\s+charges?|consumption\s+charges?)\s*[:=\-₹ ]+\s*([0-9,]+(?:\.[0-9]{1,2})?)",
        ]),
        "fixed": find_number(text, [
            r"(?:fixed\s+charges?|customer\s+charges?)\s*[:=\-₹ ]+\s*([0-9,]+(?:\.[0-9]{1,2})?)",
        ]),
        "duty": find_number(text, [
            r"(?:electricity\s+duty|duty|tax)\s*[:=\-₹ ]+\s*([0-9,]+(?:\.[0-9]{1,2})?)",
        ]),
    }

def safe_num(value, fallback):
    return float(value) if value is not None else float(fallback)

with st.sidebar:
    st.subheader("Language / భాష")
    language = st.radio(
        "Choose explanation language",
        ["English", "తెలుగు / Telugu"],
        key="currentiq_language",
    )
    if st.button("Load fictional sample bill", use_container_width=True):
        st.session_state["currentiq_bill"] = {
            "month": "November 2026", "units": 181.0, "energy": 1086.0,
            "fixed": 40.0, "duty": 54.3, "other": 0.0,
        }
        st.rerun()
    st.caption("Sample figures are fictional and are not official tariff values.")

is_telugu = language == "తెలుగు / Telugu"

tab_labels = (
    ["సారాంశం", "బిల్లు అప్‌లోడ్", "వినియోగం", "తదుపరి బిల్లు అంచనా", "గురించి"]
    if is_telugu else
    ["Overview", "Upload & explain bill", "Consumption", "Next-bill estimate", "About"]
)
overview_tab, bill_tab, usage_tab, estimate_tab, about_tab = st.tabs(tab_labels)

with overview_tab:
    history = st.session_state["currentiq_history"].copy()
    units_series = pd.to_numeric(history["Units (kWh)"], errors="coerce").fillna(0)
    c1, c2, c3 = st.columns(3)
    c1.metric("తాజా వినియోగం" if is_telugu else "Latest usage",
              f"{units_series.iloc[-1]:.0f} kWh" if len(units_series) else "—")
    c2.metric("3 నెలల సగటు" if is_telugu else "3-month average",
              f"{units_series.tail(3).mean():.0f} kWh" if len(units_series) else "—")
    c3.metric("నెలలు" if is_telugu else "Months", len(history))
    if len(history):
        st.plotly_chart(
            px.line(history, x="Month", y="Units (kWh)", markers=True,
                    title="నెలవారీ విద్యుత్ వినియోగం" if is_telugu else "Monthly consumption"),
            use_container_width=True,
        )
    st.info(
        "బిల్లు ట్యాబ్‌లో బిల్లును అప్‌లోడ్ చేసి, OCR సూచించిన విలువలను తనిఖీ చేయండి."
        if is_telugu else
        "Upload a bill in the next tab. Review OCR suggestions and confirm every value."
    )

with bill_tab:
    st.subheader("1. బిల్లును అప్‌లోడ్ చేయండి" if is_telugu else "1. Upload a bill")
    st.warning(
        "పబ్లిక్ డెమో కోసం కల్పిత లేదా వ్యక్తిగత వివరాలు తొలగించిన బిల్లులను మాత్రమే వాడండి. పేరు, చిరునామా, సర్వీస్ నంబర్, ఫోన్, QR/బార్‌కోడ్ మరియు చెల్లింపు వివరాలను దాచండి."
        if is_telugu else
        "For public demos, use fictional or anonymised bills. Hide name, address, service number, phone, QR/barcodes and payment details."
    )
    uploaded = st.file_uploader(
        "JPG, PNG, WEBP లేదా PDF అప్‌లోడ్ చేయండి" if is_telugu else "Upload JPG, PNG, WEBP or PDF",
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        key="currentiq_bill_uploader",
    )

    extracted_text = ""
    suggestions = {"units": None, "energy": None, "fixed": None, "duty": None}
    if uploaded is not None:
        suffix = uploaded.name.lower().rsplit(".", 1)[-1]
        try:
            if suffix == "pdf":
                extracted_text = extract_pdf(uploaded)
            else:
                st.image(uploaded, caption="Uploaded bill preview", use_container_width=True)
                extracted_text = extract_image(uploaded)
            if extracted_text.strip():
                st.success("బిల్లు టెక్స్ట్ చదవబడింది. ప్రతి సంఖ్యను తనిఖీ చేయండి." if is_telugu
                           else "Text extraction completed. OCR can misread digits; verify every value.")
                suggestions = suggest_values(extracted_text)
                with st.expander("చదివిన ముడి టెక్స్ట్" if is_telugu else "Show raw extracted text"):
                    st.text_area("OCR text", extracted_text, height=180, disabled=True)
            else:
                st.warning("ఈ ఫైల్‌లో చదవగలిగే టెక్స్ట్ దొరకలేదు. స్పష్టమైన చిత్రం లేదా text PDF ప్రయత్నించండి.")
        except Exception as exc:
            st.error(str(exc))
            st.info("Tip: try a clear, well-lit image or a text-based PDF. Check the deployment logs if the OCR engine is missing.")

    st.subheader("2. విలువలను నిర్ధారించండి / సవరించండి" if is_telugu else "2. Confirm / edit values")
    current = st.session_state["currentiq_bill"]
    # OCR suggestions are only defaults. No widget state is mutated after creation.
    with st.form("confirm_bill_values_form_v2"):
        left, right = st.columns(2)
        with left:
            month_value = st.text_input("బిల్లింగ్ నెల" if is_telugu else "Billing month",
                                        value=current["month"])
            units_value = st.number_input(
                "వినియోగించిన యూనిట్లు (kWh)" if is_telugu else "Units consumed (kWh)",
                min_value=0.0, value=safe_num(suggestions["units"], current["units"]), step=1.0,
            )
            energy_value = st.number_input(
                "ఎనర్జీ ఛార్జీ (₹)" if is_telugu else "Energy charge (₹)",
                min_value=0.0, value=safe_num(suggestions["energy"], current["energy"]), step=1.0,
            )
        with right:
            fixed_value = st.number_input(
                "స్థిర ఛార్జీ (₹)" if is_telugu else "Fixed charge (₹)",
                min_value=0.0, value=safe_num(suggestions["fixed"], current["fixed"]), step=1.0,
            )
            duty_value = st.number_input(
                "డ్యూటీ / పన్ను (₹)" if is_telugu else "Duty / tax (₹)",
                min_value=0.0, value=safe_num(suggestions["duty"], current["duty"]), step=1.0,
            )
            other_value = st.number_input(
                "ఇతర ఛార్జీలు (₹)" if is_telugu else "Other charges (₹)",
                min_value=0.0, value=float(current["other"]), step=1.0,
            )
        submitted = st.form_submit_button(
            "విలువలను నిర్ధారించండి" if is_telugu else "Confirm bill values",
            type="primary",
        )
    if submitted:
        st.session_state["currentiq_bill"] = {
            "month": month_value, "units": units_value, "energy": energy_value,
            "fixed": fixed_value, "duty": duty_value, "other": other_value,
        }
        st.success("బిల్లు విలువలు సేవ్ అయ్యాయి." if is_telugu else "Bill values confirmed for this session.")
        st.rerun()

    bill_data = st.session_state["currentiq_bill"]
    total = bill_data["energy"] + bill_data["fixed"] + bill_data["duty"] + bill_data["other"]
    rate = bill_data["energy"] / bill_data["units"] if bill_data["units"] else 0
    m1, m2, m3 = st.columns(3)
    m1.metric("మొత్తం" if is_telugu else "Entered total", money(total))
    m2.metric("యూనిట్‌కు ఎనర్జీ ఛార్జీ" if is_telugu else "Energy charge / unit",
              f"₹{rate:.2f}" if bill_data["units"] else "—")
    m3.metric("కాలం" if is_telugu else "Period", bill_data["month"])

    explanations = {
        "Energy charge": (
            "Charge associated with electricity units consumed in this period.",
            "ఈ బిల్లింగ్ కాలంలో వినియోగించిన విద్యుత్ యూనిట్లకు సంబంధించిన ఛార్జీ.",
        ),
        "Fixed charge": (
            "A fixed service or connection charge that may apply independently of usage.",
            "వినియోగంతో సంబంధం లేకుండా వర్తించే స్థిర సేవ లేదా కనెక్షన్ ఛార్జీ.",
        ),
        "Duty / tax": (
            "A duty or tax component shown on the bill; confirm its basis with the bill issuer.",
            "బిల్లులో చూపిన డ్యూటీ లేదా పన్ను. ఖచ్చితమైన వివరాలను బిల్లు జారీ చేసిన సంస్థతో నిర్ధారించండి.",
        ),
        "Other charges": (
            "Other adjustments entered for this demonstration.",
            "ఈ డెమో కోసం నమోదు చేసిన ఇతర సర్దుబాట్లు.",
        ),
        "Total bill": (
            "Sum of all charge components entered above.",
            "పైన నమోదు చేసిన అన్ని ఛార్జీల మొత్తం.",
        ),
    }
    for label, amount in [
        ("Energy charge", bill_data["energy"]), ("Fixed charge", bill_data["fixed"]),
        ("Duty / tax", bill_data["duty"]), ("Other charges", bill_data["other"]),
        ("Total bill", total),
    ]:
        display_label = {
            "Energy charge": "ఎనర్జీ ఛార్జీ", "Fixed charge": "స్థిర ఛార్జీ",
            "Duty / tax": "డ్యూటీ / పన్ను", "Other charges": "ఇతర ఛార్జీలు",
            "Total bill": "మొత్తం బిల్లు",
        }.get(label, label) if is_telugu else label
        with st.expander(f"{display_label} — {money(amount)}", expanded=label == "Total bill"):
            st.write(explanations[label][1 if is_telugu else 0])

    if st.button("వినియోగాన్ని చరిత్రలో చేర్చండి" if is_telugu else "Add confirmed usage to history"):
        new_row = pd.DataFrame({
            "Month": [bill_data["month"]],
            "Units (kWh)": [bill_data["units"]],
        })
        st.session_state["currentiq_history"] = pd.concat(
            [st.session_state["currentiq_history"], new_row], ignore_index=True
        ).tail(18)
        st.success("ఈ సెషన్ చరిత్రకు జోడించబడింది." if is_telugu else "Added to session history.")

with usage_tab:
    st.subheader("నెలవారీ వినియోగ చరిత్ర" if is_telugu else "Monthly usage history")
    history = st.session_state["currentiq_history"].copy()
    edited = st.data_editor(history, num_rows="dynamic", use_container_width=True,
                            key="currentiq_history_editor")
    if st.button("చరిత్రను సేవ్ చేయండి" if is_telugu else "Save history"):
        edited["Units (kWh)"] = pd.to_numeric(edited["Units (kWh)"], errors="coerce").fillna(0)
        st.session_state["currentiq_history"] = edited
        st.success("సేవ్ చేయబడింది." if is_telugu else "Saved for this session.")
    if len(edited):
        chart_data = edited.copy()
        chart_data["Units (kWh)"] = pd.to_numeric(chart_data["Units (kWh)"], errors="coerce").fillna(0)
        st.plotly_chart(
            px.bar(chart_data, x="Month", y="Units (kWh)",
                   title="నెలవారీ యూనిట్లు" if is_telugu else "Monthly units consumed"),
            use_container_width=True,
        )
        if len(chart_data) > 1:
            difference = chart_data["Units (kWh)"].iloc[-1] - chart_data["Units (kWh)"].iloc[-2]
            st.metric("మునుపటి నెలతో మార్పు" if is_telugu else "Change vs previous entry",
                      f"{difference:+.0f} kWh")
    st.download_button(
        "వినియోగ CSV డౌన్‌లోడ్" if is_telugu else "Download usage CSV",
        st.session_state["currentiq_history"].to_csv(index=False).encode("utf-8"),
        "currentiq_usage.csv", "text/csv",
    )

with estimate_tab:
    history = st.session_state["currentiq_history"]
    usage = pd.to_numeric(history["Units (kWh)"], errors="coerce").fillna(0) if len(history) else pd.Series(dtype=float)
    predicted_units = float(usage.tail(3).mean()) if len(usage) else 0.0
    bill_data = st.session_state["currentiq_bill"]
    effective_rate = bill_data["energy"] / bill_data["units"] if bill_data["units"] else 0.0
    estimate = predicted_units * effective_rate + bill_data["fixed"] + bill_data["duty"] + bill_data["other"]
    left, right = st.columns(2)
    left.metric("అంచనా వినియోగం" if is_telugu else "Estimated next usage", f"{predicted_units:.0f} kWh")
    right.metric("సూచనాత్మక బిల్లు అంచనా" if is_telugu else "Illustrative next bill", money(estimate))
    st.write(
        "ఆధారం: గత 3 నెలల సగటు వినియోగం × ప్రస్తుత బిల్లులోని యూనిట్‌కు ఎనర్జీ ఛార్జీ + ఇతర స్థిర ఛార్జీలు."
        if is_telugu else
        "Baseline: average of the latest three usage readings × the current bill's effective energy rate, plus current fixed, duty and other charges."
    )
    st.warning(
        "ఇది హామీ ఇచ్చిన బిల్లు కాదు. నిజమైన బిల్లు టారిఫ్ స్లాబ్‌లు, వినియోగదారు వర్గం, బిల్లింగ్ రోజులు, సబ్సిడీ, బకాయిలు మరియు ఇతర సర్దుబాట్లపై ఆధారపడి ఉంటుంది."
        if is_telugu else
        "This is not a guaranteed bill or official tariff calculation. Real bills depend on tariff slabs, consumer category, billing days, subsidy, arrears, meter adjustments, taxes and tariff changes."
    )

with about_tab:
    st.success(
        "CurrentIQ ఒక విద్యార్థి ప్రోటోటైప్. బిల్లు OCR సూచనలు, విలువల నిర్ధారణ, ద్విభాషా వివరణలు, వినియోగ చార్ట్‌లు మరియు ప్రాథమిక అంచనాలను చూపిస్తుంది."
        if is_telugu else
        "CurrentIQ is a student prototype demonstrating OCR suggestions, manual value confirmation, bilingual explanations, usage charts and a baseline estimate."
    )
    st.warning(
        "ఇంకా అమలు చేయనివి: అధికారిక తెలంగాణ టారిఫ్ ఇంజిన్, విద్యుత్ సంస్థల అనుసంధానం, అన్ని బిల్లు నమూనాల గుర్తింపు, ఖాతాలు మరియు శాశ్వత క్లౌడ్ నిల్వ."
        if is_telugu else
        "Not implemented: official Telangana tariff engine, utility integration, production-grade recognition of all bill layouts, user accounts or permanent cloud storage."
    )
    st.caption("Use fictional or anonymised bills only. OCR suggestions must always be checked against the original bill.")
