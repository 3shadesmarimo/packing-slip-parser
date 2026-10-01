"""Upload packing slips and generate paper checklists for manual inspections."""
import hashlib
import io
import streamlit as st
from parser import parse_pdf, PackingSlipError, sort_rows
from print_report import create_print_pdf

st.set_page_config(page_title='Packing Slip Checklist', page_icon='📦', layout='wide')
st.title('📦 Packing Slip Checklist')
st.write('Upload your packing slips to create a **printable, Letter-sized inspection checklist**. Fill in the date, transporter, trailer ID, name and container types by hand.')

if 'rows' not in st.session_state:
    st.session_state.rows = []
if 'processed' not in st.session_state:
    st.session_state.processed = set()

uploads = st.file_uploader('Upload one or more packing slip PDFs', type=['pdf'], accept_multiple_files=True)
if st.button('Extract LPNs', type='primary', disabled=not uploads):
    successes = 0
    for f in uploads:
        raw = f.getvalue()
        key = (f.name, hashlib.sha256(raw).hexdigest())
        if key in st.session_state.processed:
            st.info(f'{f.name}: already imported this session.')
            continue
        try:
            parsed = parse_pdf(io.BytesIO(raw))
            st.session_state.rows.extend(parsed)
            st.session_state.processed.add(key)
            successes += 1
        except Exception as exc:
            st.error(f'{f.name}: {exc}')
    if successes:
        st.success(f'Imported {successes} packing slip(s).')

if st.session_state.rows:
    rows = st.session_state.rows
    st.metric('LPNs extracted', len(rows))
    st.caption('All uploaded stops, cities, and LPNs appear together in one printable table. Long lists continue onto additional pages.')
    preview = [{'Stop ID': r['Stop ID'], 'City': r['City'], 'LPN': r['LPN'],
                'Pallet': '☐', 'Box': '☐', 'Pipe': '☐', 'Bundle': '☐'} for r in rows]
    st.dataframe(preview, hide_index=True, use_container_width=True)
    pdf_bytes = create_print_pdf(rows)
    st.download_button('🖨️ Download printable PDF', pdf_bytes, 'packing_slip_checklist.pdf',
                       mime='application/pdf', type='primary')
    st.info('Open the downloaded PDF and choose Print. The date, transporter, trailer ID, name and container type cells are intentionally blank.')
    if st.button('Clear imported packing slips'):
        st.session_state.rows = []
        st.session_state.processed = set()
        st.rerun()
else:
    st.info('Upload PDFs and click Extract LPNs to begin.')
st.caption('Supports text-based packing slips with a final “Container List”. Image-only scanned PDFs require OCR.')
