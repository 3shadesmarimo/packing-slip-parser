"""Extract one row per SH LPN from the final Container List of packing slips."""
import re
import pdfplumber

COLUMNS = ['Stop ID', 'City', 'LPN', 'Pallet', 'Box', 'Pipe', 'Bundle']

class PackingSlipError(ValueError):
    pass


def parse_pdf(file):
    """Accept a path or binary file-like object. Return extracted rows."""
    with pdfplumber.open(file) as pdf:
        text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
    if not text.strip():
        raise PackingSlipError('No selectable text found. This may be a scanned PDF requiring OCR.')
    # Anchor the stop number to its field; avoid incidental order numbers.
    stop = re.search(r'\bStop Number\s*:\s*([A-Z0-9-]+)', text, re.I)
    # Destination is on the "To" side of the slip. Capture only text before "From".
    dest = re.search(r'\bTo\s*:\s*(.*?)\bFrom\s*:', text, re.I | re.S)
    city = None
    if dest:
        # City often appears on a later line; find the first destination City, State, Zip
        match = re.search(r'City\s*,\s*State\s*,\s*Zip\s+(.+)', dest.group(1), re.I)
        if match:
            city = re.split(r',', match.group(1), 1)[0].strip()
    if not city:
        # Text extraction can rearrange columns. Use the first City, State, Zip line
        match = re.search(r'City\s*,\s*State\s*,\s*Zip\s+([A-Za-zÀ-ÿ .\-]+)\s*,', text, re.I)
        if match:
            city = match.group(1).strip()
    # Some layouts combine destination and source on one line. Extract from first
    # City field, stopping at province comma, which is present in supplied format.
    sections = list(re.finditer(r'\bContainer\s+List\s*:', text, re.I))
    if not stop:
        raise PackingSlipError('Stop Number not found.')
    if not city:
        raise PackingSlipError('Destination City not found. Check the PDF layout.')
    if not sections:
        raise PackingSlipError('Final Container List not found. Individual item rows were intentionally ignored.')
    tail = text[sections[-1].end():]
    tail = re.split(r'\bTotal\s+(?:Weight\s+of\s+Stop|Containers)\s*:', tail, maxsplit=1, flags=re.I)[0]
    lpns = list(dict.fromkeys(re.findall(r'\bSH\s*\d+\b', tail, re.I)))
    lpns = [re.sub(r'\s+', '', x).upper() for x in lpns]
    lpns = list(dict.fromkeys(lpns))
    if not lpns:
        raise PackingSlipError('Container List found, but no SH LPNs were present.')
    return [dict(zip(COLUMNS, [stop.group(1).upper(), city.title(), lpn, None, None, None, None])) for lpn in lpns]
