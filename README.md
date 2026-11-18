# CurrentIQ — Fixed MVP

## Included
- Streamlit bill-upload interface for JPG/JPEG/PNG/WEBP and PDF.
- OCR with Tesseract for images and scanned PDF pages; direct text extraction for text PDFs.
- OCR suggestions for units, energy charges, fixed charges and duty.
- Manual confirmation before bill totals and estimates are calculated.
- English and Telugu interface labels and charge explanations.
- Usage history editor, charts, CSV export and a simple illustrative estimate.

## Deploy the updated version
1. In your GitHub repository, replace the existing `app.py`, `requirements.txt`, and `packages.txt` with the files in this folder.
2. Commit the changes to the same branch connected to Streamlit Community Cloud (usually `main`).
3. Streamlit should detect the commit and redeploy. If it does not, open the app dashboard and choose Reboot.
4. Wait for deployment to finish, then refresh the app.

The `packages.txt` file installs the Tesseract OCR engine and English language data on Streamlit Community Cloud.

## Local run
Use Python 3.10 or newer. Install the Tesseract system program separately, then run:
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Important limitations
- OCR is best-effort and can misread numbers. Verify every suggested value against the original bill.
- This MVP does not implement an official Telangana tariff engine or connect to TSSPDCL/TGSPDCL.
- Telugu is used for the app's labels and explanatory text. OCR currently reads English text; Telugu OCR is not configured.
- Usage history is held in the current Streamlit session and is not permanent cloud storage.
- Forecasting is a simple illustrative baseline, not an official bill prediction.
- Use fictional or anonymised bills in demos. Never upload bills containing identifiable customer information.
- This is an independent student prototype, not affiliated with a utility or government.
