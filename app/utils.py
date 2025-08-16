import os
from PyPDF2 import PdfReader, PdfWriter

def dividir_pdf(filepath, pages, output_folder):
    reader = PdfReader(filepath)
    writer = PdfWriter()

    page_ranges = []
    for part in pages.split(','):
        if '-' in part:
            start, end = part.split('-')
            page_ranges.extend(range(int(start)-1, int(end)))
        else:
            page_ranges.append(int(part)-1)

    for page_num in page_ranges:
        if 0 <= page_num < len(reader.pages):
            writer.add_page(reader.pages[page_num])

    output_path = os.path.join(output_folder, "dividido.pdf")
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
