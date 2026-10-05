import sys
import os
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.chunking.chunker import MarkdownSemanticChunker

SAMPLE_MARKDOWN = """# **LIC's Jeevan Umang (UIN: 512N312V03)**

LIC's Jeevan Umang is a Par, Non-Linked, Life, Individual, Savings, Whole Life Insurance plan.

## **1. ELIGIBILITY CONDITIONS AND OTHER RESTRICTION**

- Minimum Basic Sum Assured: Rs. 2,00,000
- Maximum Basic Sum Assured: No limit

|Basic Sum Assured Range|Sum Assured multiple|
|---|---|
|From Rs. 2,00,000 to Rs. 4,50,000|Rs. 25,000/-|
|Above Rs. 4,50,000|Rs. 50,000/-|

## **2. BENEFITS**

### **a) Death Benefit:**

On death of the Life Assured during the policy term, provided the policy is in-force, Death Benefit payable shall be Sum Assured on Death.
"""

def test_header_context_inheritance():
    chunker = MarkdownSemanticChunker(target_chunk_size=200, max_chunk_size=300)
    chunks = chunker.chunk_text(SAMPLE_MARKDOWN, file_name="745 LIC_Jeevan Umang_Eng _141025.md")
    
    assert len(chunks) > 0
    # Verify header path context prefix in chunk content
    for chunk in chunks:
        assert "header_path" in chunk
        assert len(chunk["header_path"]) > 0
        assert f"[{chunk['header_path']}]" in chunk["content"]

def test_unbroken_table_preservation():
    chunker = MarkdownSemanticChunker(target_chunk_size=200, max_chunk_size=300)
    chunks = chunker.chunk_text(SAMPLE_MARKDOWN, file_name="745 LIC_Jeevan Umang_Eng _141025.md")
    
    # Find chunk containing table
    table_chunks = [c for c in chunks if c["contains_table"]]
    assert len(table_chunks) >= 1
    
    for tc in table_chunks:
        # Verify complete table header and rows exist together
        assert "|Basic Sum Assured Range|Sum Assured multiple|" in tc["content"]
        assert "|From Rs. 2,00,000 to Rs. 4,50,000|Rs. 25,000/-|" in tc["content"]
        assert "|Above Rs. 4,50,000|Rs. 50,000/-|" in tc["content"]

def test_metadata_payload():
    chunker = MarkdownSemanticChunker(target_chunk_size=200, max_chunk_size=300)
    chunks = chunker.chunk_text(SAMPLE_MARKDOWN, file_name="745 LIC_Jeevan Umang_Eng _141025.md")
    
    for chunk in chunks:
        assert "chunk_id" in chunk
        assert "policy_uin" in chunk
        assert "policy_name" in chunk
        assert "header_path" in chunk
        assert "content" in chunk
        assert "contains_table" in chunk
        assert "token_count" in chunk
        
        assert chunk["policy_uin"] == "512N312V03"
        assert "Jeevan Umang" in chunk["policy_name"]

def test_chunk_all_markdown_files():
    parsed_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "parsed_markdown")
    if not os.path.exists(parsed_dir):
        pytest.skip("parsed_markdown directory does not exist")
        
    chunker = MarkdownSemanticChunker(target_chunk_size=500, max_chunk_size=1000, overlap_tokens=100)
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chunks")
    all_chunks = chunker.process_directory(parsed_dir, output_dir=output_dir)
    
    assert len(all_chunks) > 0
    assert os.path.exists(os.path.join(output_dir, "parsed_chunks.json"))
