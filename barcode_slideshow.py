
"""Interactive LPN barcode slideshow."""

import base64
import io
import json
import html

import streamlit as st
import streamlit.components.v1 as components

from barcode.codex import Code128
from barcode.writer import SVGWriter


def generate_barcode(lpn):
    """Generate a Code 128 barcode as an SVG data URL."""

    code = Code128(
    str(lpn),
    writer=SVGWriter()
    )

    output = io.BytesIO()

    code.write(
        output,
        options={
            "module_width": 0.32,
            "module_height": 20,
            "quiet_zone": 6.5,
            "write_text": False
        }
    )

    encoded = base64.b64encode(
        output.getvalue()
    ).decode("ascii")

    return f"data:image/svg+xml;base64,{encoded}"


def show_barcode_slideshow(rows):
    """Display one LPN barcode at a time."""

    slides = []

    for row in rows:
        lpn = str(row.get("LPN", "")).strip()

        if not lpn:
            continue

        slides.append({
            "city": str(row.get("City", "")),
            "lpn": lpn,
            "stop": str(row.get("Stop ID", "")),
            "barcode": generate_barcode(lpn)
        })

    if not slides:
        st.info("No LPNs available.")
        return

    slides_json = json.dumps(slides).replace(
        "<", "\\u003c"
    )

    page = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">

    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 8px;
            background: #ffffff;
            color: #111827;
        }

        .viewer {
            border: 1px solid #d1d5db;
            border-radius: 14px;
            padding: 24px;
            text-align: center;
            outline: none;
        }

        .city {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 14px;
        }

        .barcode {
            width: 100%;
            max-width: 600px;
            height: 190px;
            object-fit: contain;
        }

        .lpn {
            font-size: 30px;
            font-weight: bold;
            margin-top: 12px;
        }

        .stop {
            font-size: 15px;
            color: #6b7280;
            margin-top: 8px;
        }

        .controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-top: 24px;
        }

        button {
            background: #17324f;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }

        button:disabled {
            opacity: 0.35;
            cursor: not-allowed;
        }

        .counter {
            font-weight: bold;
            font-size: 17px;
        }

        .hint {
            font-size: 13px;
            color: #6b7280;
            margin-top: 18px;
        }
    </style>
    </head>

    <body>
        <div class="viewer" id="viewer" tabindex="0">

            <div class="city" id="city"></div>

            <img class="barcode" id="barcode"
                 alt="LPN Barcode">

            <div class="lpn" id="lpn"></div>

            <div class="stop" id="stop"></div>

            <div class="controls">
                <button id="prev" onclick="previous()">
                    &#8592; Previous
                </button>

                <span class="counter" id="counter"></span>

                <button id="next" onclick="next()">
                    Next &#8594;
                </button>
            </div>

            <div class="hint">
                Click inside the viewer, then use
                &#8592; and &#8594; arrow keys.
            </div>
        </div>

        <script>
            const slides = __SLIDES__;
            let index = 0;

            function render() {
                const slide = slides[index];

                document.getElementById("city")
                    .textContent = slide.city;

                document.getElementById("lpn")
                    .textContent = slide.lpn;

                document.getElementById("stop")
                    .textContent = "Stop ID: " + slide.stop;

                document.getElementById("barcode")
                    .src = slide.barcode;

                document.getElementById("counter")
                    .textContent =
                    (index + 1) + " / " + slides.length;

                document.getElementById("prev")
                    .disabled = index === 0;

                document.getElementById("next")
                    .disabled = index === slides.length - 1;
            }

            function next() {
                if (index < slides.length - 1) {
                    index++;
                    render();
                }
            }

            function previous() {
                if (index > 0) {
                    index--;
                    render();
                }
            }

            document.addEventListener("keydown", function(e) {
                if (e.key === "ArrowRight") {
                    e.preventDefault();
                    next();
                }

                if (e.key === "ArrowLeft") {
                    e.preventDefault();
                    previous();
                }
            });

            render();
        </script>
    </body>
    </html>
    """

    page = page.replace("__SLIDES__", slides_json)

    components.html(
        page,
        height=510,
        scrolling=False
    )
