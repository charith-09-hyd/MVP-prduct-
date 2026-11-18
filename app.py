import re
from io import BytesIO
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image, ImageOps, ImageEnhance

st.set_page_config(page_title="CurrentIQ",page_icon="⚡",layout="wide")
st.markdown("""<style>.stApp{background:#f4f7fb}.block-container{max-width:1200px;padding-top:1.2rem}.hero{padding:24px 28px;border-radius:18px;color:white;background:linear-gradient(110deg,#102a43,#176b87);margin-bottom:16px}.hero h1{color:white;margin:0}.hero p{color:#e3f1f6;margin:7px 0 0}</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>⚡ CurrentIQ</h1><p>Understand your electricity bill • Track usage • Plan ahead</p></div>',unsafe_allow_html=True)
st.caption("Student MVP • TISC 2026 Challenge 13 • Independent prototype; not affiliated with any DISCOM or government.")
if "history" not in st.session_state:
    st.session_state.history=pd.DataFrame({"Month":["May","Jun","Jul","Aug","Sep","Oct"],"Units (kWh)":[142,158,151,173,166,181]})
if "bill" not in st.session_state:
    st.session_state.bill={"month":"November 2026","units":181.0,"energy":1086.0,"fixed":40.0,"duty":54.3,"other":0.0}

def ocr_image(f):
    import pytesseract
    im=Image.open(f).convert("RGB")
    im=ImageEnhance.Contrast(ImageOps.grayscale(im)).enhance(1.6)
    return pytesseract.image_to_string(im,config="--psm 6")

def ocr_pdf(f):
    import fitz
    doc=fitz.open(stream=f.read(),filetype="pdf")
    out=[]
    for page in doc:
        txt=page.get_text("text").strip()
        if txt: out.append(txt)
        else:
            import pytesseract
            pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
            im=Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")
            out.append(pytesseract.image_to_string(ImageOps.grayscale(im),config="--psm 6"))
    return "\n\n".join(out)

def num(patterns,text):
    for p in patterns:
        m=re.search(p,text,re.I|re.M)
        if m:
            try:return float(m.group(1).replace(",",""))
            except:pass
    return None

def suggestions(t):
    return {
      "units":num([r"(?:units consumed|consumption|units|kwh)\\s*[:\\-]?\\s*([0-9,]+(?:\\.[0-9]+)?)",r"([0-9,]+(?:\\.[0-9]+)?)\\s*(?:kwh|units)\\b"],t),
      "energy":num([r"(?:energy charges?|consumption charges?)\\s*[:\\-₹ ]+\\s*([0-9,]+(?:\\.[0-9]{1,2})?)"],t),
      "fixed":num([r"(?:fixed charges?|customer charges?)\\s*[:\\-₹ ]+\\s*([0-9,]+(?:\\.[0-9]{1,2})?)"],t),
      "duty":num([r"(?:electricity duty|duty|tax)\\s*[:\\-₹ ]+\\s*([0-9,]+(?:\\.[0-9]{1,2})?)"],t)
    }

def money(x):return f"₹{x:,.2f}"

with st.sidebar:
    lang=st.radio("Explanation language",["English","తెలుగు / Telugu"])
    if st.button("Load fictional sample bill"):
        st.session_state.bill={"month":"November 2026","units":181.0,"energy":1086.0,"fixed":40.0,"duty":54.3,"other":0.0}
        st.rerun()
    st.caption("Sample values are fictional, not official tariff data.")

t1,t2,t3,t4,t5=st.tabs(["Overview","Upload & explain bill","Consumption","Next-bill estimate","About"])
with t1:
    h=st.session_state.history
    vals=pd.to_numeric(h["Units (kWh)"],errors="coerce").fillna(0)
    a,b,c=st.columns(3);a.metric("Latest usage",f"{vals.iloc[-1]:.0f} kWh" if len(vals) else "—");b.metric("3-month average",f"{vals.tail(3).mean():.0f} kWh" if len(vals) else "—");c.metric("Months",len(vals))
    if len(h):st.plotly_chart(px.line(h,x="Month",y="Units (kWh)",markers=True,title="Monthly consumption"),use_container_width=True)
    st.info("Upload a bill in the next tab. Review OCR output and confirm every value before using it.")
with t2:
    st.subheader("1. Upload a bill")
    st.warning("For public demos, use fictional or anonymised bills. Hide name, address, service number, phone, QR/barcodes and payment details.")
    f=st.file_uploader("Upload JPG, PNG, WEBP or PDF",type=["jpg","jpeg","png","webp","pdf"])
    txt=""; err=None; sug={}
    if f:
        if f.name.lower().endswith(".pdf"):
            try:txt=ocr_pdf(f)
            except ImportError:err="PDF/OCR package missing. Install requirements.txt and Tesseract (see README)."
            except Exception as e:err=f"PDF extraction failed: {e}"
            st.success("PDF uploaded.")
        else:
            st.image(f,caption="Uploaded bill preview",use_container_width=True)
            f.seek(0)
            try:txt=ocr_image(f)
            except ImportError:err="pytesseract is missing. Install requirements.txt."
            except Exception as e:err=f"OCR unavailable: {e}. Install Tesseract OCR engine; see README."
        if err:st.warning(err)
        if txt.strip():
            st.success("Text extraction completed. OCR may misread digits; verify everything.")
            with st.expander("Show raw extracted text"):st.text_area("OCR text",txt,height=170)
            sug=suggestions(txt)
            st.caption("Auto-detected values below are suggestions only. Confirm against the original bill.")
    st.subheader("2. Confirm / edit values")
    old=st.session_state.bill
    def val(k):return float(sug[k] if sug.get(k) is not None else old[k])
    with st.form("bill"):
        l,r=st.columns(2)
        with l:
            month=st.text_input("Billing month",old["month"])
            units=st.number_input("Units consumed (kWh)",min_value=0.0,value=val("units"),step=1.0)
            energy=st.number_input("Energy charge (₹)",min_value=0.0,value=val("energy"),step=1.0)
        with r:
            fixed=st.number_input("Fixed charge (₹)",min_value=0.0,value=val("fixed"),step=1.0)
            duty=st.number_input("Duty / tax (₹)",min_value=0.0,value=val("duty"),step=1.0)
            other=st.number_input("Other charges (₹)",min_value=0.0,value=float(old["other"]),step=1.0)
        save=st.form_submit_button("Confirm bill values",type="primary")
        if save:
            st.session_state.bill={"month":month,"units":units,"energy":energy,"fixed":fixed,"duty":duty,"other":other};st.rerun()
    b=st.session_state.bill;total=b["energy"]+b["fixed"]+b["duty"]+b["other"];rate=b["energy"]/b["units"] if b["units"] else 0
    x,y,z=st.columns(3);x.metric("Entered total",money(total));y.metric("Energy charge / unit",f"₹{rate:.2f}" if b["units"] else "—");z.metric("Period",b["month"])
    explanations={
      "Energy charge":("Charge associated with electricity units consumed in this period.","ఈ బిల్లింగ్ కాలంలో వినియోగించిన విద్యుత్ యూనిట్లకు సంబంధించిన ఛార్జీ."),
      "Fixed charge":("A fixed service or connection charge that may apply independently of usage.","వినియోగంతో సంబంధం లేకుండా వర్తించే స్థిర సేవ లేదా కనెక్షన్ ఛార్జీ."),
      "Duty / tax":("A duty or tax component shown on the bill; confirm its basis with the bill issuer.","బిల్లులో చూపిన డ్యూటీ లేదా పన్ను. ఖచ్చితమైన వివరాలను బిల్లు జారీ చేసిన సంస్థతో నిర్ధారించండి."),
      "Other charges":("Other adjustments entered for this demonstration.","ఈ డెమో కోసం నమోదు చేసిన ఇతర సర్దుబాట్లు."),
      "Total bill":("Sum of all charge components entered above.","పైన నమోదు చేసిన అన్ని ఛార్జీల మొత్తం.")}
    for label,amount in [("Energy charge",b["energy"]),("Fixed charge",b["fixed"]),("Duty / tax",b["duty"]),("Other charges",b["other"]),("Total bill",total)]:
        with st.expander(f"{label} — {money(amount)}",expanded=label=="Total bill"):st.write(explanations[label][0 if lang=="English" else 1])
    if st.button("Add confirmed usage to history"):
        st.session_state.history=pd.concat([st.session_state.history,pd.DataFrame({"Month":[b["month"]],"Units (kWh)":[b["units"]]})],ignore_index=True).tail(18);st.success("Added to session history.")
with t3:
    st.subheader("Monthly usage history")
    edited=st.data_editor(st.session_state.history,num_rows="dynamic",use_container_width=True)
    if st.button("Save history"):
        edited["Units (kWh)"]=pd.to_numeric(edited["Units (kWh)"],errors="coerce").fillna(0);st.session_state.history=edited;st.success("Saved.")
    if len(edited):
        d=edited.copy();d["Units (kWh)"]=pd.to_numeric(d["Units (kWh)"],errors="coerce").fillna(0)
        st.plotly_chart(px.bar(d,x="Month",y="Units (kWh)",title="Monthly units consumed"),use_container_width=True)
        if len(d)>1:
            diff=d["Units (kWh)"].iloc[-1]-d["Units (kWh)"].iloc[-2];st.metric("Change vs previous entry",f"{diff:+.0f} kWh")
    st.download_button("Download usage CSV",st.session_state.history.to_csv(index=False).encode(), "currentiq_usage.csv","text/csv")
with t4:
    h=st.session_state.history;u=pd.to_numeric(h["Units (kWh)"],errors="coerce").fillna(0) if len(h) else pd.Series(dtype=float)
    predicted=float(u.tail(3).mean()) if len(u) else 0;b=st.session_state.bill
    rate=b["energy"]/b["units"] if b["units"] else 0;estimate=predicted*rate+b["fixed"]+b["duty"]+b["other"]
    a,bcol=st.columns(2);a.metric("Estimated next usage",f"{predicted:.0f} kWh");bcol.metric("Illustrative next bill",money(estimate))
    st.write("Baseline: average of latest three unit readings × current bill's effective energy rate, plus current fixed charge, duty and other charges.")
    st.code("Predicted units = mean(latest 3 monthly readings)\\nEnergy rate = current energy charge / current units\\nEstimated total = predicted units * energy rate + fixed + duty + other")
    st.warning("Not a guaranteed bill or official tariff calculation. Real bills depend on tariff slabs, consumer category, billing days, subsidy, arrears, meter adjustments, taxes and tariff changes.")
with t5:
    st.success("Working: file upload, OCR extraction where configured, raw text preview, editable value confirmation, bilingual explanations, charts, CSV export and a baseline estimate.")
    st.warning("Not implemented: official Telangana tariff engine, utility integration, production-grade bill-layout recognition, cloud accounts, secure long-term storage or validated forecasting.")
    st.markdown("**Demo:** load fictional sample → upload redacted bill → inspect OCR → correct values → show Telugu explanation → add usage → show chart → explain forecast limitations.")
    st.caption("CurrentIQ is an independent student prototype. It is not connected to TSSPDCL, TGSPDCL or any electricity provider.")
