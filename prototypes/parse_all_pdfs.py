import os
import pymupdf4llm

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_pdfs")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "parsed_markdown")

def parse_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".pdf")]
    
    print(f"Starting parsing of {len(pdf_files)} PDF files...", flush=True)
    for f in pdf_files:
        pdf_path = os.path.join(RAW_DIR, f)
        base_name = os.path.splitext(f)[0]
        out_path = os.path.join(OUTPUT_DIR, f"{base_name}.md")
        
        print(f"Parsing '{f}' -> '{base_name}.md'...", flush=True)
        md_content = pymupdf4llm.to_markdown(pdf_path)
        
        with open(out_path, "w", encoding="utf-8") as out_file:
            out_file.write(md_content)
            
        print(f"Saved {len(md_content)} chars to {out_path}", flush=True)

if __name__ == "__main__":
    parse_all()
