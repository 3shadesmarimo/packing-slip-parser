import re
import pdfplumber

class PackingSlipError(Exception):
    pass

def _find_first(patterns, text):
    """Return the first successful regex match."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()

    return None


def extract_stop_id(text):
    patterns = [
        # English
        r"Stop\s*Number\s*:\s*([^\s]+)",
        r"Packing\s+Slip\s+For\s+Stop\s+Number\s*:\s*([^\s]+)",

        # French
        r"Num[eé]ro\s+d[\'’]?\s*arr[eê]t\s*:\s*([^\s]+)",
        r"Liste\s+de\s+Colisage\s*:\s*([^\s]+)",
    ]

    stop_id = _find_first(patterns, text)

    if stop_id:
        return stop_id.strip().upper()

    return None 


def extract_city(text):
    """
    Extract destination city from English or French packing slips.

    Examples:
        City, State, Zip EDMUNDSTON,NBE3V 3L2
        Ville, État, Zip: STGEORGES,QCG5Y 8G2
    """

    patterns = [
        # English
        r"City\s*,?\s*State\s*,?\s*Zip\s*:?\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿ .'\-]+?)\s*,",

        # French
        r"Ville\s*,?\s*[ÉE]tat\s*,?\s*Zip\s*:?\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿ .'\-]+?)\s*,",
    ]

    city = _find_first(patterns, text)

    if city:
        return city.strip()

    return None




def extract_lpns(text):
    """
    Extract LPNs only from the final Container List.
    Supports single, multiple, numeric and alphanumeric LPNs.
    """

    matches = list(re.finditer(
        r"(?im)^\s*Container\s+List\s*:\s*$",
        text
    ))

    if not matches:
        return []

    container_section = text[matches[-1].end():]

    # Stop before totals or the next PDF page header.
    container_section = re.split(
        r"(?im)^\s*(?:"
        r"Page\s*:\s*\d+\b|"
        r"Total\s+Weight\b|"
        r"Poids\s+Total\b|"
        r"Total\s+Containers\b|"
        r"Conteneurs\s+Total\b|"
        r"Packing\s+Slip\s+For\s+Stop\b|"
        r"Liste\s+de\s+Colisage\s*:"
        r")",
        container_section,
        maxsplit=1
    )[0]

    lpns = []

    for line in container_section.splitlines():
        for item in line.split(","):
            lpn = item.strip()

            # Accept complete identifiers, not random text.
            if re.fullmatch(
                r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*",
                lpn
            ) and any(char.isdigit() for char in lpn):
                lpns.append(lpn.upper())

    return list(dict.fromkeys(lpns))

def parse_packing_slip(pdf_file):
    """
    Parse one packing slip and return a row for each LPN.
    """

    with pdfplumber.open(pdf_file) as pdf:
        pages = []

        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                pages.append(page_text)

    text = "\n".join(pages)

    stop_id = extract_stop_id(text)

    if not stop_id:
        raise ValueError("Stop Number not found.")

    city = extract_city(text)

    if not city:
        raise ValueError("City not found.")

    lpns = extract_lpns(text)

    if not lpns:
        raise ValueError("No LPNs found in Container List.")

    rows = []

    for lpn in lpns:
        rows.append({
            "Stop ID": stop_id,
            "City": city,
            "LPN": lpn,
            "Pallet": "",
            "Box": "",
            "Pipe": "",
            "Bundle": "",
        })

    return rows

def sort_rows(rows):
    """
    Sort all extracted rows:
    City first, then DSD, HOT, then everything else.
    """

    stop_priority = {
        "DSD": 0,
        "HOT": 1,
    }

    def sort_key(row):
        city = row.get("City", "").strip().upper()
        stop_id = row.get("Stop ID", "").strip().upper()
        lpn = row.get("LPN", "").strip().upper()

        prefix = stop_id[:3]
        priority = stop_priority.get(prefix, 99)

        return (city, priority, stop_id, lpn)

    return sorted(rows, key=sort_key)


def parse_pdf(pdf_file):
    try:
        return parse_packing_slip(pdf_file)
    except ValueError as e:
        raise PackingSlipError(str(e))
    except Exception as e:
        raise PackingSlipError(f"Unable to parse PDF: {e}")
