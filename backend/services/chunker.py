import re
import uuid
from typing import List, TypedDict, Dict, Any, Optional, Tuple
from backend.services.pdf_parser import PageData
from backend.utils.logger import setup_logger

logger = setup_logger("chunker")

class ChunkData(TypedDict):
    chunk_id: str
    text: str
    page_number: int
    source_filename: str
    section_title: str
    char_count: int
    chunk_index: int

def count_tokens(text: str) -> int:
    """Counts the number of tokens (words) in the text.

    Args:
        text: Input text string.

    Returns:
        Word token count.
    """
    return len(text.split())

def recursive_split_large_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Recursively splits text into blocks of size <= chunk_size tokens with overlap.

    Splits prioritizing paragraph breaks, line breaks, semicolons, commas, and finally spaces.

    Args:
        text: Raw text that exceeds chunk_size tokens.
        chunk_size: Maximum tokens per chunk.
        overlap: Token overlap between consecutive chunks.

    Returns:
        A list of split text strings.
    """
    tokens = text.split()
    if len(tokens) <= chunk_size:
        return [text]

    # Attempt to split on logical boundaries in order of preference
    separators = ["\n\n", "\n", "; ", ", ", " "]
    for sep in separators:
        if sep in text:
            parts = text.split(sep)
            chunks: List[str] = []
            current_parts: List[str] = []
            
            for part in parts:
                part_clean = part.strip()
                if not part_clean:
                    continue
                
                part_tokens = part_clean.split()
                if len(part_tokens) > chunk_size:
                    # If a single part is still too large, flush current accumulator and recurse
                    if current_parts:
                        chunks.append(sep.join(current_parts))
                        current_parts = []
                    sub_chunks = recursive_split_large_text(part_clean, chunk_size, overlap)
                    chunks.extend(sub_chunks)
                else:
                    # Check if adding this part exceeds max size
                    current_tokens_count = sum(len(p.split()) for p in current_parts)
                    if not current_parts or (current_tokens_count + len(part_tokens) <= chunk_size):
                        current_parts.append(part_clean)
                    else:
                        # Flush current accumulator
                        chunks.append(sep.join(current_parts))
                        
                        # Accumulate parts for overlap
                        overlap_parts = []
                        overlap_tokens_accumulated = 0
                        for p in reversed(current_parts):
                            p_toks = len(p.split())
                            if overlap_tokens_accumulated + p_toks <= overlap:
                                overlap_parts.insert(0, p)
                                overlap_tokens_accumulated += p_toks
                            else:
                                if not overlap_parts:
                                    overlap_parts.insert(0, p)
                                break
                        current_parts = overlap_parts + [part_clean]
            
            if current_parts:
                chunks.append(sep.join(current_parts))
                
            # Filter out any empty chunks
            return [c for c in chunks if c.strip()]

    # Absolute fallback: split strictly by token boundaries
    chunks = []
    i = 0
    step = chunk_size - overlap
    if step <= 0:
        step = max(1, chunk_size // 2)
        
    while i < len(tokens):
        chunk_tokens = tokens[i : i + chunk_size]
        chunks.append(" ".join(chunk_tokens))
        i += step
        
    return chunks

def chunk_document(
    pages: List[PageData],
    filename: str,
    chunk_size: int = 512,
    overlap: int = 50
) -> List[ChunkData]:
    """Processes a document's extracted pages into semantic, metadata-aware chunks.

    Pipeline logic:
    1. Sentence-aware splitting using regex boundaries (. ! ?) to avoid cutting mid-sentence.
    2. Large sentences exceeding chunk_size are recursively split using smaller delimiters.
    3. Sentences are associated with the closest active heading based on page offsets.
    4. Sentences are aggregated into chunks of maximum token size `chunk_size` while carrying
       over a token overlap of up to `overlap`.
    5. Indexes, character counts, and UUIDs are assigned to each chunk.

    Args:
        pages: List of PageData containing page numbers, text, and headings.
        filename: Original source filename.
        chunk_size: Maximum tokens per chunk.
        overlap: Token overlap between chunks.

    Returns:
        List of ChunkData dicts.
    """
    logger.info(f"Chunking document '{filename}' with chunk_size={chunk_size}, overlap={overlap}")
    sentence_items: List[Dict[str, Any]] = []
    sentence_endings = re.compile(r'(?<=[.!?])\s+')

    for page in pages:
        page_text = page["text"]
        page_num = page["page_number"]
        headings = page.get("headings", [])

        # Find character offsets of headings on this page to assign headings to sentences
        headings_with_positions: List[Tuple[str, int]] = []
        search_start = 0
        for heading in headings:
            pos = page_text.find(heading, search_start)
            if pos != -1:
                headings_with_positions.append((heading, pos))
                search_start = pos + len(heading)
            else:
                # Fallback case-insensitive match
                pos = page_text.lower().find(heading.lower())
                if pos != -1:
                    headings_with_positions.append((heading, pos))
                    
        # Sort headings by their start position
        headings_with_positions.sort(key=lambda x: x[1])

        # Step 1: Sentence splitting
        raw_sentences = sentence_endings.split(page_text)
        current_pos = 0

        for sent in raw_sentences:
            sent_clean = sent.strip()
            if not sent_clean:
                continue

            # Locate sentence index in page text
            pos = page_text.find(sent_clean, current_pos)
            if pos != -1:
                current_pos = pos + len(sent_clean)
            else:
                pos = current_pos

            # Find active heading preceding this sentence
            active_heading = ""
            for heading, h_pos in headings_with_positions:
                if h_pos <= pos:
                    active_heading = heading
                else:
                    break

            # Calculate token length of sentence
            sent_tokens = count_tokens(sent_clean)

            # Step 2: Recursive split if single sentence exceeds chunk_size
            if sent_tokens > chunk_size:
                sub_sentences = recursive_split_large_text(sent_clean, chunk_size, overlap)
                for sub_s in sub_sentences:
                    sentence_items.append({
                        "text": sub_s,
                        "page_number": page_num,
                        "section_title": active_heading,
                        "token_count": count_tokens(sub_s)
                    })
            else:
                sentence_items.append({
                    "text": sent_clean,
                    "page_number": page_num,
                    "section_title": active_heading,
                    "token_count": sent_tokens
                })

    # Step 3 & 4: Aggregate sentences into chunks with sliding-window overlap
    chunks: List[List[Dict[str, Any]]] = []
    current_chunk: List[Dict[str, Any]] = []
    current_tokens = 0

    i = 0
    while i < len(sentence_items):
        item = sentence_items[i]
        
        # Safe fallback in case token count is somehow still larger than chunk_size
        if item["token_count"] > chunk_size:
            sub_parts = recursive_split_large_text(item["text"], chunk_size, overlap)
            sentence_items[i:i+1] = [
                {
                    "text": sp,
                    "page_number": item["page_number"],
                    "section_title": item["section_title"],
                    "token_count": count_tokens(sp)
                }
                for sp in sub_parts
            ]
            continue

        if not current_chunk:
            current_chunk.append(item)
            current_tokens = item["token_count"]
            i += 1
        elif current_tokens + item["token_count"] <= chunk_size:
            current_chunk.append(item)
            current_tokens += item["token_count"]
            i += 1
        else:
            # Save the completed chunk
            chunks.append(current_chunk)

            # Compute overlap sentences
            overlap_tokens = 0
            overlap_sentences = []
            for sent in reversed(current_chunk):
                if overlap_tokens + sent["token_count"] <= overlap:
                    overlap_sentences.insert(0, sent)
                    overlap_tokens += sent["token_count"]
                else:
                    break

            # Prevent infinite loop: if overlap + next item exceeds chunk_size, drop oldest overlap sentence
            while overlap_sentences and (sum(s["token_count"] for s in overlap_sentences) + item["token_count"] > chunk_size):
                overlap_sentences.pop(0)

            current_chunk = overlap_sentences
            current_chunk.append(item)
            current_tokens = sum(s["token_count"] for s in current_chunk)
            i += 1

    if current_chunk:
        chunks.append(current_chunk)

    # Step 5 & 6: Finalize ChunkData schema and mapping
    chunk_datas: List[ChunkData] = []
    for idx, chunk_group in enumerate(chunks):
        chunk_text = " ".join(s["text"] for s in chunk_group)
        
        # Primary page number is the first sentence's page
        page_number = chunk_group[0]["page_number"]
        
        # Find first non-empty section title in the chunk group
        section_title = ""
        for s in chunk_group:
            if s["section_title"]:
                section_title = s["section_title"]
                break

        chunk_datas.append({
            "chunk_id": str(uuid.uuid4()),
            "text": chunk_text,
            "page_number": page_number,
            "source_filename": filename,
            "section_title": section_title,
            "char_count": len(chunk_text),
            "chunk_index": idx
        })

    logger.info(f"Chunking pipeline complete. Generated {len(chunk_datas)} chunks from PDF.")
    return chunk_datas
