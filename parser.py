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
    Extract LPNs from the final Container List.

    Supports formats such as:
        SH0003812
        SH58812
        R-133FEWFW
        ABC-12345
        R_2026_001
        123456789

    Preserves original values and removes duplicates.
    """

    # Find the final Container List section.
    matches = list(re.finditer(
        r"Container\s+List\s*:",
        text,
        re.IGNORECASE
    ))

    if not matches:
        return []

    # Use the last Container List occurrence.
    container_section = text[matches[-1].end():]

    # Stop at the footer or totals section.
    container_section = re.split(
        r"Total\s+Weight|"
        r"Poids\s+Total|"
        r"Total\s+Containers|"
        r"Conteneurs\s+Total",
        container_section,
        maxsplit=1,
        flags=re.IGNORECASE
    )[0]

    lpns = []

    for line in container_section.splitlines():
        line = line.strip()

        if not line:
            continue

        # Skip common headings.
        if re.match(
            r"^(LPN|Container|Container\s+ID|Type|Quantity|Qty)\s*$",
            line,
            re.IGNORECASE
        ):
            continue

        # Extract possible LPN identifiers.
        candidates = re.findall(
            r"\b[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*\b",
            line
        )

        for candidate in candidates:
            candidate = candidate.upper()

            # Require at least one digit to avoid ordinary words.
            if not any(char.isdigit() for char in candidate):
                continue

            # Skip isolated small quantities.
            if candidate.isdigit() and len(candidate) < 5:
                continue

            lpns.append(candidate)

    return list(dict.fromkeys(lpns))


def extract_lpns(text):
    """
    Extract supported LPN formats from the final Container List.

    Supports:
        SH0003812
        SH58812
        R-133FEWFW
    """

    matches = list(re.finditer(
        r"Container\s+List\s*:",
        text,
        re.IGNORECASE
    ))

    if not matches:
        return []

    # Use the final Container List.
    container_section = text[matches[-1].end():]

    # Stop at the end of the container section.
    container_section = re.split(
        r"Total\s+Weight|"
        r"Poids\s+Total|"
        r"Total\s+Containers|"
        r"Conteneurs\s+Total",
        container_section,
        maxsplit=1,
        flags=re.IGNORECASE
    )[0]

    # Recognize SH LPNs and the R- format.
    lpns = re.findall(
        r"(?<![A-Za-z0-9_-])(?:SH\d+|R-[A-Za-z0-9]+)(?![A-Za-z0-9_-])",
        container_section,
        re.IGNORECASE
    )

    return list(dict.fromkeys(lpn.upper() for lpn in lpns))


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
