# CurrentIQ Full MVP

## Features
- Upload JPG/JPEG/PNG/WEBP images and PDF bills.
- OCR images and scanned PDF pages with Tesseract; read text PDFs directly.
- Suggest common bill fields (units, energy charge, fixed charge, duty) using simple label matching.
- Manually review and confirm all values before calculations.
- English and Telugu template explanations, usage history, charts, CSV export and baseline forecast.

## Run locally
1. Install Python 3.10+.
2. Install Tesseract OCR engine separately:
   - Windows: install Tesseract and add its installation folder to PATH.
   - macOS: `brew install tesseract`
   - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
3. In this folder run `pip install -r requirements.txt`.
4. Run `streamlit run app.py` and open the local URL shown (usually http://localhost:8501).

## Deploy to Streamlit Community Cloud
Upload app.py, requirements.txt and packages.txt to a GitHub repo. Create a Streamlit app from that repo; packages.txt installs the Linux Tesseract engine. Test OCR with redacted sample bills after deployment.

## Limitations
OCR is best-effort and can misread digits or labels. Suggested values are not verified; manually check them. Heuristic extraction will not recognise every bill layout. Forecast is a simple baseline, not an official Telangana tariff calculation. No TSSPDCL/TGSPDCL integration, user accounts or cloud database. Use only fictional or anonymised bills for public demos; never upload identifiable customer bills. This is not affiliated with a utility or government.
