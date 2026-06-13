import re
import unicodedata
from typing import List, TypedDict, Optional, Dict, Any
import fitz  # PyMuPDF
import pdfplumber
from backend.utils.logger import setup_logger

logger = setup_logger("pdf_parser")

class PageData(TypedDict):
    page_number: int
    text: str
    headings: List[str]

def clean_text(text: str) -> str:
    """Cleans noisy text by removing null bytes, normalizing unicode, and stripping whitespace.

    Args:
        text: Raw text extracted from the PDF page.

    Returns:
        Cleaned and normalized text.
    """
    if not text:
        return ""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Normalize unicode representation
    text = unicodedata.normalize("NFKC", text)
    # Remove carriage returns and split into lines
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        # Strip extra spaces inside the line
        line = re.sub(r'[ \t]+', ' ', line).strip()
        if line:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def clean_heading(heading: str) -> str:
    """Cleans a detected heading candidate.

    Args:
        heading: Raw heading text.

    Returns:
        Cleaned heading or empty string if invalid.
    """
    cleaned = re.sub(r'[ \t\r\n]+', ' ', heading).strip()
    # Remove common page number artifacts or dots
    cleaned = cleaned.rstrip(".")
    # Avoid too short or too long headings
    if len(cleaned) < 3 or len(cleaned) > 150:
        return ""
    # Filter out pure numbers (like page numbers)
    if cleaned.isdigit():
        return ""
    return cleaned

def extract_page_with_pdfplumber(file_path: str, page_number: int) -> PageData:
    """Fallback text and heading extractor using pdfplumber for a specific page.

    Args:
        file_path: Path to the PDF file.
        page_number: The 1-based page number to extract.

    Returns:
        PageData containing extracted text and headings.
    """
    logger.info(f"pdfplumber fallback initiated for page {page_number}")
    with pdfplumber.open(file_path) as pdf:
        if page_number - 1 >= len(pdf.pages):
            logger.warning(f"Page number {page_number} is out of bounds for pdfplumber.")
            return {"page_number": page_number, "text": "", "headings": []}
        
        page = pdf.pages[page_number - 1]
        text = page.extract_text() or ""
        cleaned_text = clean_text(text)
        
        headings = []
        # Fallback heading detection using characters metadata
        current_heading_chars = []
        for char in page.chars:
            fontname = char.get("fontname", "").lower()
            size = char.get("size", 0)
            is_bold = "bold" in fontname or "black" in fontname
            is_heading = size > 14 or is_bold
            
            if is_heading:
                current_heading_chars.append(char.get("text", ""))
            else:
                if current_heading_chars:
                    heading_str = "".join(current_heading_chars)
                    cleaned_h = clean_heading(heading_str)
                    if cleaned_h and cleaned_h not in headings:
                        headings.append(cleaned_h)
                    current_heading_chars = []
        
        # Check if a heading was left unfinished
        if current_heading_chars:
            heading_str = "".join(current_heading_chars)
            cleaned_h = clean_heading(heading_str)
            if cleaned_h and cleaned_h not in headings:
                headings.append(cleaned_h)

        return {
            "page_number": page_number,
            "text": cleaned_text,
            "headings": headings
        }

def extract_text_from_pdf(file_path: str) -> List[PageData]:
    """Extracts text and headings page by page from a PDF.

    Uses PyMuPDF (fitz) as the primary engine and falls back to pdfplumber
    at the page level if PyMuPDF fails to extract text or throws an exception.

    Args:
        file_path: Path to the PDF file.

    Returns:
        A list of PageData dicts.
    """
    logger.info(f"Starting PDF text extraction for: {file_path}")
    pages_data: List[PageData] = []
    
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        logger.error(f"PyMuPDF failed to open PDF {file_path}: {str(e)}. Attempting full pdfplumber fallback.")
        # Fallback to pdfplumber for the entire document
        try:
            with pdfplumber.open(file_path) as pdf:
                for idx, page in enumerate(pdf.pages):
                    page_num = idx + 1
                    pages_data.append(extract_page_with_pdfplumber(file_path, page_num))
            return pages_data
        except Exception as pe:
            logger.error(f"Full pdfplumber fallback failed as well: {str(pe)}")
            raise RuntimeError(f"Failed to parse PDF using both PyMuPDF and pdfplumber: {str(pe)}")

    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        try:
            text_blocks: List[str] = []
            headings: List[str] = []
            
            # Extract structured text using dict format to find font sizes and flags
            page_dict = page.get_text("dict")
            
            for block in page_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    block_lines = []
                    for line in block.get("lines", []):
                        line_text_parts = []
                        for span in line.get("spans", []):
                            span_text = span.get("text", "")
                            if not span_text.strip():
                                continue
                            
                            font_size = span.get("size", 0)
                            font_flags = span.get("flags", 0)
                            font_name = span.get("font", "").lower()
                            
                            # Bold checking: PyMuPDF flags bit 1 is Italic, bit 2 is Bold
                            is_bold = (font_flags & 2) != 0 or "bold" in font_name or "black" in font_name
                            is_heading = font_size > 14 or is_bold
                            
                            # Clean unicode and check if it qualifies as heading
                            if is_heading:
                                cleaned_h = clean_heading(span_text)
                                if cleaned_h and cleaned_h not in headings:
                                    headings.append(cleaned_h)
                                    
                            line_text_parts.append(span_text)
                            
                        if line_text_parts:
                            line_str = "".join(line_text_parts)
                            block_lines.append(line_str)
                            
                    if block_lines:
                        # Join lines within a block with a space
                        block_text = " ".join(block_lines)
                        text_blocks.append(block_text)
            
            page_text = "\n\n".join(text_blocks)
            cleaned_text = clean_text(page_text)
            
            # If PyMuPDF returned little or no text, trigger pdfplumber fallback for the page
            if len(cleaned_text.strip()) < 10:
                logger.warning(f"Extracted text from page {page_num} is too short ({len(cleaned_text)} chars). Falling back to pdfplumber.")
                pages_data.append(extract_page_with_pdfplumber(file_path, page_num))
            else:
                pages_data.append({
                    "page_number": page_num,
                    "text": cleaned_text,
                    "headings": headings
                })
                
        except Exception as ex:
            logger.error(f"PyMuPDF failed to process page {page_num}: {str(ex)}. Falling back to pdfplumber.")
            try:
                pages_data.append(extract_page_with_pdfplumber(file_path, page_num))
            except Exception as fallback_ex:
                logger.error(f"pdfplumber fallback also failed for page {page_num}: {str(fallback_ex)}")
                # Append whatever fitz got, or empty page
                pages_data.append({
                    "page_number": page_num,
                    "text": "",
                    "headings": []
                })

    doc.close()
    logger.info(f"Successfully extracted {len(pages_data)} pages from PDF.")
    return pages_data
