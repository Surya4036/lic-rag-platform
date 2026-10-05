import os
import pymupdf4llm

PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_pdfs")

def check_tables():
    pdfs = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    for pdf_path in pdfs:
        filename = os.path.basename(pdf_path)
        md = pymupdf4llm.to_markdown(pdf_path)
        lines = md.split("\n")
        table_lines = [line for line in lines if "|" in line]
        print(f"\n==========================================")
        print(f"File: {filename}")
        print(f"Total Markdown Lines: {len(lines)}, Markdown Table Lines: {len(table_lines)}")
        print("Sample Table Output:")
        print("\n".join(table_lines[:20]))

if __name__ == "__main__":
    check_tables()
