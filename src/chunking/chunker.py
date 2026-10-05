import os
import re
import json
import tiktoken
from typing import List, Dict, Any, Optional

class MarkdownSemanticChunker:
    """
    Markdown Header & Table-Aware Semantic Chunker for LIC Policy Documents.
    
    Preserves section hierarchy (Header Context Inheritance), preserves markdown tables unbroken,
    targets 500-1000 tokens per chunk with ~100 token overlap for narrative prose, and builds
    structured metadata JSON payloads.
    """
    def __init__(
        self,
        target_chunk_size: int = 750,
        max_chunk_size: int = 1000,
        overlap_tokens: int = 100,
        encoding_name: str = "cl100k_base"
    ):
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_tokens = overlap_tokens
        self.tokenizer = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def clean_text(self, text: str) -> str:
        """Removes excessive HTML tag clutter while keeping readable text."""
        cleaned = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"</?(?:mark|u|b|i|em|strong|span)[^>]*>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    def extract_policy_metadata(self, text: str, default_name: str) -> Dict[str, str]:
        """Extract policy UIN and canonical policy name from text."""
        uin_match = re.search(r"512N\d{3}V\d{2}", text)
        policy_uin = uin_match.group(0) if uin_match else "UNKNOWN_UIN"

        # Attempt to extract clean policy name
        name_match = re.search(r"(LIC(?:’|')?s?\s+[A-Za-z0-9\s\-–]+?(?:Plan|Umang|Shree|Money Back|Labh|Utsav|Amritbaal|Pension|Anand|Akshay|Bima|Endowment)[A-Za-z0-9\s\-–]*?)(?:\(|\n|UIN|$)", text, re.IGNORECASE)
        if name_match:
            policy_name = self.clean_text(name_match.group(1)).replace("**", "").replace("#", "").strip()
        else:
            # Fallback based on file name
            clean_name = os.path.splitext(os.path.basename(default_name))[0]
            clean_name = re.sub(r"^\d+\s*", "", clean_name)
            policy_name = clean_name.replace("_", " ").strip()

        return {
            "policy_uin": policy_uin,
            "policy_name": policy_name
        }

    def _slugify(self, text: str) -> str:
        slug = text.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
        return slug or "policy"

    def parse_blocks(self, text: str, default_policy_name: str) -> List[Dict[str, Any]]:
        """
        Parses document into block structures (headings, narrative text, tables)
        with associated header path context.
        """
        lines = text.split("\n")
        blocks = []
        
        heading_stack: Dict[int, str] = {}
        heading_stack[1] = default_policy_name

        current_table_lines: List[str] = []
        current_text_lines: List[str] = []

        def get_header_path() -> str:
            sorted_levels = sorted(heading_stack.keys())
            headers = [heading_stack[lvl] for lvl in sorted_levels if heading_stack[lvl]]
            return " > ".join(headers) if headers else default_policy_name

        def flush_text_block():
            if current_text_lines:
                raw_block = "\n".join(current_text_lines).strip()
                if raw_block:
                    blocks.append({
                        "type": "text",
                        "content": raw_block,
                        "header_path": get_header_path(),
                        "is_table": False
                    })
                current_text_lines.clear()

        def flush_table_block():
            if current_table_lines:
                table_str = "\n".join(current_table_lines).strip()
                if table_str:
                    blocks.append({
                        "type": "table",
                        "content": table_str,
                        "header_path": get_header_path(),
                        "is_table": True
                    })
                current_table_lines.clear()

        for line in lines:
            stripped = line.strip()
            clean_line = self.clean_text(stripped)

            # Check for Table row
            if stripped.startswith("|") or (len(current_table_lines) > 0 and stripped.startswith("|")):
                flush_text_block()
                current_table_lines.append(stripped)
                continue
            elif current_table_lines:
                # Table ended
                flush_table_block()

            # Check for Heading line
            heading_match = re.match(r"^(#{1,6})\s+(.*)", stripped)
            section_number_match = re.match(r"^(?:<mark>|\*\*)*(\d+\.\s+[A-Z\s]{4,})(?:</mark>|\*\*)*", stripped)

            if heading_match:
                flush_text_block()
                level = len(heading_match.group(1))
                h_title = self.clean_text(heading_match.group(2)).replace("**", "").replace("_", "").strip()

                # Update heading stack
                for lvl in list(heading_stack.keys()):
                    if lvl >= level:
                        del heading_stack[lvl]
                heading_stack[level] = h_title
                continue
            elif section_number_match and len(stripped) < 120:
                flush_text_block()
                level = 2
                h_title = self.clean_text(section_number_match.group(1)).replace("**", "").replace("_", "").strip()

                for lvl in list(heading_stack.keys()):
                    if lvl >= level:
                        del heading_stack[lvl]
                heading_stack[level] = h_title
                continue

            # Regular text
            if stripped:
                current_text_lines.append(stripped)

        flush_text_block()
        flush_table_block()

        return blocks

    def chunk_text(self, text: str, file_name: str = "document.md") -> List[Dict[str, Any]]:
        meta = self.extract_policy_metadata(text, file_name)
        policy_uin = meta["policy_uin"]
        policy_name = meta["policy_name"]
        policy_slug = self._slugify(policy_name)

        blocks = self.parse_blocks(text, policy_name)

        chunks: List[Dict[str, Any]] = []
        current_blocks: List[Dict[str, Any]] = []
        current_tokens = 0
        current_header_path = policy_name
        current_has_table = False

        chunk_idx = 1

        def emit_chunk(overlap_seed_blocks: List[Dict[str, Any]] = None):
            nonlocal chunk_idx, current_blocks, current_tokens, current_has_table, current_header_path
            if not current_blocks:
                return

            # Combine block contents
            combined_body = "\n\n".join(b["content"] for b in current_blocks)
            header_prefix = f"[{current_header_path}]"
            full_content = f"{header_prefix}\n{combined_body}"
            token_cnt = self.count_tokens(full_content)

            chunk_id = f"{policy_slug}-chunk-{chunk_idx}"

            chunks.append({
                "chunk_id": chunk_id,
                "parent_chunk_id": f"{policy_slug}-parent-sec-{chunk_idx}",
                "policy_uin": policy_uin,
                "policy_name": policy_name,
                "header_path": current_header_path,
                "content": full_content,
                "contains_table": current_has_table,
                "token_count": token_cnt,
                "metadata": {
                    "policy_uin": policy_uin,
                    "policy_name": policy_name,
                    "header_path": current_header_path,
                    "has_table": current_has_table
                }
            })

            chunk_idx += 1
            current_blocks = []
            current_tokens = 0
            current_has_table = False

            # Add overlap seed blocks if provided
            if overlap_seed_blocks:
                for ob in overlap_seed_blocks:
                    current_blocks.append(ob)
                    current_tokens += self.count_tokens(ob["content"])
                    if ob["is_table"]:
                        current_has_table = True
                    current_header_path = ob["header_path"]

        for block in blocks:
            block_content = block["content"]
            block_tokens = self.count_tokens(block_content)
            block_is_table = block["is_table"]
            block_header_path = block["header_path"]

            # If block is a table
            if block_is_table:
                # If adding table exceeds max_chunk_size, emit current chunk first
                if current_blocks and (current_tokens + block_tokens > self.max_chunk_size):
                    emit_chunk()

                current_header_path = block_header_path
                current_blocks.append(block)
                current_tokens += block_tokens
                current_has_table = True

                # If table itself brings chunk near target size, emit chunk immediately to keep table pristine
                if current_tokens >= self.target_chunk_size:
                    emit_chunk()
                continue

            # If narrative block
            if current_blocks and (current_tokens + block_tokens > self.max_chunk_size):
                # Prepare overlap seed blocks (last narrative blocks up to overlap_tokens)
                overlap_seed: List[Dict[str, Any]] = []
                acc_overlap_tokens = 0
                for prev_b in reversed(current_blocks):
                    if prev_b["is_table"]:
                        continue
                    ptok = self.count_tokens(prev_b["content"])
                    if acc_overlap_tokens + ptok <= self.overlap_tokens:
                        overlap_seed.insert(0, prev_b)
                        acc_overlap_tokens += ptok
                    else:
                        break

                emit_chunk(overlap_seed_blocks=overlap_seed)

            if not current_blocks:
                current_header_path = block_header_path

            current_blocks.append(block)
            current_tokens += block_tokens
            if block_is_table:
                current_has_table = True

            if current_tokens >= self.target_chunk_size:
                # Check if we reached target chunk size
                overlap_seed: List[Dict[str, Any]] = []
                acc_overlap_tokens = 0
                for prev_b in reversed(current_blocks):
                    if prev_b["is_table"]:
                        continue
                    ptok = self.count_tokens(prev_b["content"])
                    if acc_overlap_tokens + ptok <= self.overlap_tokens:
                        overlap_seed.insert(0, prev_b)
                        acc_overlap_tokens += ptok
                    else:
                        break
                emit_chunk(overlap_seed_blocks=overlap_seed)

        # Flush remaining blocks
        if current_blocks:
            emit_chunk()

        return chunks

    def process_directory(self, input_dir: str, output_dir: str) -> List[Dict[str, Any]]:
        """Processes all .md files in input_dir and saves combined JSON output."""
        os.makedirs(output_dir, exist_ok=True)
        all_chunks: List[Dict[str, Any]] = []

        md_files = [f for f in os.listdir(input_dir) if f.endswith(".md")]
        for f in md_files:
            file_path = os.path.join(input_dir, f)
            with open(file_path, "r", encoding="utf-8") as rf:
                content = rf.read()

            file_chunks = self.chunk_text(content, file_name=f)
            all_chunks.extend(file_chunks)

            # Save individual policy chunk JSON
            policy_slug = self._slugify(f.replace(".md", ""))
            individual_out = os.path.join(output_dir, f"{policy_slug}_chunks.json")
            with open(individual_out, "w", encoding="utf-8") as wf:
                json.dump(file_chunks, wf, indent=2, ensure_ascii=False)

        # Save master parsed_chunks.json
        master_out = os.path.join(output_dir, "parsed_chunks.json")
        with open(master_out, "w", encoding="utf-8") as wf:
            json.dump(all_chunks, wf, indent=2, ensure_ascii=False)

        return all_chunks
