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
    """
    Supports English and French Wolseley packing slips.
    """

    patterns = [
        # English
        r"Stop\s*Number\s*:\s*(DSD[A-Z0-9]+)",
        r"Packing\s+Slip\s+For\s+Stop\s+Number\s*:\s*(DSD[A-Z0-9]+)",

        # French
        r"Num[eé]ro\s+d[\'’]?\s*arr[eê]t\s*:\s*(DSD[A-Z0-9]+)",
        r"Liste\s+de\s+Colisage\s*:\s*(DSD[A-Z0-9]+)",
    ]

    return _find_first(patterns, text)


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
    Extract SH numbers specifically from the final Container List.

    Handles:
        SH0003812
        SH0003813
        SH0003814

    and shorter numbers such as:
        SH58812
    """

    # Find the final Container List section.
    match = re.search(
        r"Container\s+List\s*:\s*(.*?)(?:"
        r"Total\s+Weight|"
        r"Poids\s+Total|"
        r"Total\s+Containers|"
        r"Conteneurs\s+Total|"
        r"$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return []

    container_section = match.group(1)

    # LPNs can contain different numbers of digits.
    lpns = re.findall(
        r"\bSH\d+\b",
        container_section,
        re.IGNORECASE
    )

    # Normalize to uppercase and remove duplicates while
    # preserving the original order.
    return list(dict.fromkeys(lpn.upper() for lpn in lpns))


def parse_packing_slip(pdf_file):
    """
    Parse one Wolseley packing slip.

    Returns one dictionary for every LPN.
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

def parse_pdf(pdf_file):
    try:
        return parse_packing_slip(pdf_file)
    except ValueError as e:
        raise PackingSlipError(str(e))
    except Exception as e:
        raise PackingSlipError(f"Unable to parse PDF: {e}")