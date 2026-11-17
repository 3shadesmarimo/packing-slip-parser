
"""Upload packing slips and generate paper checklists for manual inspections."""

import hashlib
import io
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from barcode_slideshow import show_barcode_slideshow
from parser import parse_pdf, PackingSlipError, sort_rows
from print_report import create_print_pdf


st.set_page_config(
    page_title="Packing Slip Checklist",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Packing Slip Checklist")


# Session state initialization
if "rows" not in st.session_state:
    st.session_state.rows = []

if "processed" not in st.session_state:
    st.session_state.processed = set()

if "extraction_date" not in st.session_state:
    st.session_state.extraction_date = None


def set_extraction_date():
    """Set the checklist date if it has not already been set."""
    if st.session_state.extraction_date is None:
        st.session_state.extraction_date = datetime.now(
            ZoneInfo("America/Toronto")
        ).strftime("%m/%d/%Y")


# -----------------------------------
# PDF UPLOAD
# -----------------------------------

st.subheader("📄 Import Packing Slips")

uploads = st.file_uploader(
    "Upload one or more packing slip PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

if st.button(
    "Extract LPNs",
    type="primary",
    disabled=not uploads
):
    successes = 0

    for f in uploads:
        raw = f.getvalue()
        key = (f.name, hashlib.sha256(raw).hexdigest())

        if key in st.session_state.processed:
            st.info(f"{f.name}: already imported this session.")
            continue

        try:
            parsed = parse_pdf(io.BytesIO(raw))

            st.session_state.rows.extend(parsed)
            st.session_state.processed.add(key)
            successes += 1

        except Exception as exc:
            st.error(f"{f.name}: {exc}")

    if successes:
        set_extraction_date()
        st.success(f"Imported {successes} packing slip(s).")


# -----------------------------------
# PACKING SLIP INFORMATION
# -----------------------------------

st.divider()
st.subheader("🚚 Packing Slip Information")

transporter = st.text_input(
    "Transporter *",
    placeholder="Enter transporter",
    key="transporter"
)

name = st.text_input(
    "Name *",
    placeholder="Enter name",
    key="inspector_name"
)

if not transporter.strip() or not name.strip():
    st.warning(
        "Transporter and Name are required "
        "before downloading the printable PDF."
    )




# -----------------------------------
# MANUAL ENTRY
# -----------------------------------

st.divider()
st.subheader("✍️ Add Packing Slip Manually")


def add_manual_lpns():
    city = st.session_state.manual_city.strip().upper()
    stop_id = st.session_state.manual_stop_id.strip()
    lpns = [
        line.strip()
        for line in st.session_state.manual_lpns.splitlines()
        if line.strip()
    ]

    if not city or not stop_id or not lpns:
        st.session_state.manual_feedback = (
            "error",
            "Enter a city, a stop ID, and at least one LPN."
        )
        return

    st.session_state.rows.extend(
        {"Stop ID": stop_id, "City": city, "LPN": lpn}
        for lpn in lpns
    )
    set_extraction_date()

    st.session_state.manual_lpns = ""
    st.session_state.manual_feedback = (
        "success",
        f"Added {len(lpns)} LPN(s) for {city}, stop {stop_id}."
    )


with st.expander("➕ Manual Entry", expanded=False):
    with st.form("manual_entry_form"):
        st.text_input(
            "City *",
            placeholder="Example: EDMUNDSTON",
            key="manual_city"
        )
        st.text_input(
            "Stop ID *",
            placeholder="Enter Stop ID",
            key="manual_stop_id"
        )
        st.text_area(
            "LPNs *",
            placeholder="Enter or paste one LPN per line",
            height=220,
            key="manual_lpns"
        )
        st.caption("Press Enter after each LPN to start a new line.")

        st.form_submit_button(
            "➕ Add LPNs to Checklist",
            type="primary",
            on_click=add_manual_lpns
        )

    feedback = st.session_state.pop("manual_feedback", None)
    if feedback:
        status, message = feedback
        if status == "error":
            st.error(message)
        else:
            st.success(message)


# -----------------------------------
# CHECKLIST RESULTS
# -----------------------------------


st.divider()

if st.session_state.rows:

    rows = sort_rows(st.session_state.rows)

    st.write(
        f"**Date:** {st.session_state.extraction_date}"
    )

    st.metric("Total LPNs", len(rows))

    st.caption(
        "All uploaded and manually entered stops, cities, "
        "and LPNs appear together in one printable table."
    )

    preview = [
        {
            "Stop ID": r["Stop ID"],
            "City": r["City"],
            "LPN": r["LPN"],
            "Pallet": "☐",
            "Box": "☐",
            "Pipe": "☐",
            "Bundle": "☐"
        }
        for r in rows
    ]

    st.dataframe(
        preview,
        hide_index=True,
        use_container_width=True
    )

    # -----------------------------------
    # LPN BARCODE SLIDESHOW
    # -----------------------------------

    st.divider()

    st.subheader("🏷️ LPN Barcode Slideshow")

    st.caption(
        "Scan each barcode with your warehouse gun. "
        "Click inside the slideshow and use the "
        "left/right arrow keys to navigate."
    )

    show_barcode_slideshow(rows)


    # PDF download requires Transporter and Name
    if transporter.strip() and name.strip():

        pdf_bytes = create_print_pdf(
            rows,
            date=st.session_state.extraction_date,
            transporter=transporter.strip(),
            name=name.strip()
        )

        st.download_button(
            "🖨️ Download printable PDF",
            pdf_bytes,
            "packing_slip_checklist.pdf",
            mime="application/pdf",
            type="primary"
        )

    else:
        st.warning(
            "Enter Transporter and Name "
            "to enable PDF download."
        )

    st.info(
        "Open the downloaded PDF and choose Print. "
        "The date, transporter and name will be filled "
        "automatically. Trailer ID and container type "
        "cells remain blank."
    )

    if st.button("🗑️ Clear imported packing slips"):

        st.session_state.rows = []
        st.session_state.processed = set()
        st.session_state.extraction_date = None

        st.rerun()

else:
    st.info(
        "Upload PDFs or manually add packing slips to begin."
    )

