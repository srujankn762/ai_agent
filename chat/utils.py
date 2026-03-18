from pypdf import PdfReader


def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks