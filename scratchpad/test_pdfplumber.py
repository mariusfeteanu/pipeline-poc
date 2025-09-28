import pdfplumber

# Path to your PDF file
pdf_path = "../.data/papers/physics.pop-ph/pdf/1705.01467v1.pdf"

# Open the PDF
with pdfplumber.open(pdf_path) as pdf:
    text = ""
    for page in pdf.pages:
        text += page.extract_text() + "\n"

print(text)
