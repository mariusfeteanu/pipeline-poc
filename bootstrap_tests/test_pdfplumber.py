import random
import os

import pdfplumber


def test_pdfplumber():
    PDF_DIR = "../.data/papers/physics.pop-ph/pdf/"
    files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    pdf_path = os.path.join(PDF_DIR, random.choice(files))

    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    print(text)
