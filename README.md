# Packing Slip Printable Checklist

Upload one or more text-based packing slip PDFs. The application extracts **Stop ID**, destination **City**, and every **SH LPN from the final Container List**, ignoring SH numbers in individual product lines. It creates a clean, **US Letter (8.5 × 11 inch) PDF** for printing, with blank **Date, Transporter, Trailer ID, and Name** fields and blank **Pallet, Box, Pipe, Bundle** columns to mark by hand.

All uploaded packing slips are combined into one table with Stop ID, City, and LPN on every row. Long lists continue onto additional pages with repeated table headings. There is no Excel/CSV export.

## Start the app

```bash
cd packing_slip_parser
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Upload packing slips, click **Extract LPNs**, then **Download printable PDF**. Open the PDF and print at **Actual size** on Letter paper.

Notes: Documents with missing Stop ID, destination City, or final Container List are flagged. The same PDF won't import twice during a session. This version doesn't support image-only scanned PDFs.
