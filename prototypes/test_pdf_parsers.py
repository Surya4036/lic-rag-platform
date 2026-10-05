import os
import pymupdf  # PyMuPDF
import pdfplumber
from pypdf import PdfReader

PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_pdfs")

def benchmark_pymupdf(pdf_path):
    print(f"\n==========================================")
    print(f"PyMuPDF for {os.path.basename(pdf_path)}")
    print(f"==========================================")
    doc = pymupdf.open(pdf_path)
    print(f"Total pages: {len(doc)}")
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()
        finder = page.find_tables()
        tables = finder.tables
        if len(tables) > 0 or "table" in text.lower() or "eligibility" in text.lower():
            print(f"\n--- Page {i+1} ---")
            print(f"Text snippet:\n{text[:300]}...")
            print(f"Tables found: {len(tables)}")
            for tbl_idx, tbl in enumerate(tables):
                extracted = tbl.extract()
                print(f"  Table {tbl_idx+1} ({len(extracted)} rows):")
                for row in extracted[:4]:
                    print(f"    {row}")

def benchmark_pdfplumber(pdf_path):
    print(f"\n==========================================")
    print(f"pdfplumber for {os.path.basename(pdf_path)}")
    print(f"==========================================")
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if len(tables) > 0:
                print(f"\n--- Page {i+1} ---")
                print(f"Tables found: {len(tables)}")
                for tbl in tables:
                    print(f"  Table sample ({len(tbl)} rows):")
                    for row in tbl[:3]:
                        print(f"    {row}")

def main():
    pdfs = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    print(f"Found {len(pdfs)} PDFs in {PDF_DIR}")
    for pdf in pdfs:
        benchmark_pymupdf(pdf)
        benchmark_pdfplumber(pdf)

if __name__ == "__main__":
    main()
