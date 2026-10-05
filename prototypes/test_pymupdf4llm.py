import os
import pymupdf4llm

PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_pdfs")

def main():
    pdfs = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    for pdf_path in pdfs:
        filename = os.path.basename(pdf_path)
        print(f"\n==========================================")
        print(f"Converting {filename} via pymupdf4llm")
        print(f"==========================================")
        md_text = pymupdf4llm.to_markdown(pdf_path, pages=[0, 1, 2, 3]) # First 4 pages
        print(f"Markdown preview (first 1000 chars):\n")
        print(md_text[:1000])

if __name__ == "__main__":
    main()
