# AI Research Assistant - Backend Terminal Test
# Make sure the server is running before executing this script.

import httpx
import json
import os
import sys

BASE_URL = "http://127.0.0.1:8000"
DIVIDER = "=" * 60

def print_section(title):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)

def print_result(response):
    print(f"  Status Code : {response.status_code}")
    try:
        data = response.json()
        print(f"  Response    :\n{json.dumps(data, indent=4)}")
    except Exception:
        print(f"  Response    : {response.text}")

def find_any_pdf():
    """Find any PDF on desktop or downloads to use for testing."""
    search_dirs = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Documents"),
    ]
    for d in search_dirs:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.lower().endswith(".pdf"):
                    return os.path.join(d, f)
    return None

def run():
    print("\n" + DIVIDER)
    print("  AI Research Assistant — Backend Terminal Test")
    print(DIVIDER)

    # ── TEST 1: Health Check ──────────────────────────────────
    print_section("TEST 1: Health Check  →  GET /health")
    try:
        r = httpx.get(f"{BASE_URL}/health")
        print_result(r)
    except Exception as e:
        print(f"  ERROR: Could not reach server. Is it running?\n  {e}")
        sys.exit(1)

    # ── TEST 2: API Version Health ────────────────────────────
    print_section("TEST 2: API Health  →  GET /api/v1/health")
    r = httpx.get(f"{BASE_URL}/api/v1/health")
    print_result(r)

    # ── TEST 3: List Documents (should be empty or have docs) ─
    print_section("TEST 3: List All Documents  →  GET /api/v1/documents/")
    r = httpx.get(f"{BASE_URL}/api/v1/documents/")
    print_result(r)
    existing_docs = r.json()

    # ── TEST 4: Upload a PDF ──────────────────────────────────
    print_section("TEST 4: Upload PDF  →  POST /api/v1/documents/upload")

    # Try to find a PDF automatically
    pdf_path = find_any_pdf()

    if not pdf_path:
        print("  No PDF found automatically on Desktop/Downloads/Documents.")
        pdf_path = input("  Enter full path to a PDF file: ").strip().strip('"')

    if not os.path.exists(pdf_path):
        print(f"  ERROR: File not found: {pdf_path}")
        sys.exit(1)

    print(f"  Using PDF: {pdf_path}")
    doc_id = None

    with open(pdf_path, "rb") as f:
        files = {"file": (os.path.basename(pdf_path), f, "application/pdf")}
        r = httpx.post(f"{BASE_URL}/api/v1/documents/upload", files=files, timeout=30)

    print_result(r)

    if r.status_code == 201:
        doc_id = r.json()["document_id"]
        print(f"\n  ✅ Upload successful! Document ID: {doc_id}")
    elif r.status_code == 409:
        doc_id = r.json().get("existing_doc_id")
        print(f"\n  ⚠️  Duplicate detected. Using existing Document ID: {doc_id}")
    else:
        print("  ❌ Upload failed.")
        sys.exit(1)

    # ── TEST 5: Duplicate Upload ──────────────────────────────
    print_section("TEST 5: Upload Same PDF Again (Duplicate Check)")
    with open(pdf_path, "rb") as f:
        files = {"file": (os.path.basename(pdf_path), f, "application/pdf")}
        r = httpx.post(f"{BASE_URL}/api/v1/documents/upload", files=files, timeout=30)
    print_result(r)
    if r.status_code == 409:
        print("  ✅ Duplicate correctly rejected with 409 Conflict!")

    # ── TEST 6: Get Document Metadata ─────────────────────────
    print_section(f"TEST 6: Get Document Metadata  →  GET /api/v1/documents/{doc_id}")
    r = httpx.get(f"{BASE_URL}/api/v1/documents/{doc_id}")
    print_result(r)

    # ── TEST 7: Get All Chunks ────────────────────────────────
    print_section(f"TEST 7: Get All Chunks  →  GET /api/v1/documents/{doc_id}/chunks")
    r = httpx.get(f"{BASE_URL}/api/v1/documents/{doc_id}/chunks")
    data = r.json()
    print(f"  Status Code  : {r.status_code}")
    print(f"  Total Chunks : {data['total_chunks']}")
    print()
    for chunk in data["chunks"]:
        print(f"  --- Chunk {chunk['chunk_index']} ---")
        print(f"  Page         : {chunk['page_number']}")
        print(f"  Section      : {chunk['section_title'] or 'N/A'}")
        print(f"  Char Count   : {chunk['char_count']}")
        print(f"  Text Preview : {chunk['text'][:120]}...")
        print()

    # ── TEST 8: Get Single Chunk ──────────────────────────────
    first_chunk_id = data["chunks"][0]["chunk_id"]
    print_section(f"TEST 8: Get Single Chunk  →  GET /api/v1/documents/{doc_id}/chunks/{first_chunk_id}")
    r = httpx.get(f"{BASE_URL}/api/v1/documents/{doc_id}/chunks/{first_chunk_id}")
    print_result(r)

    # ── TEST 9: Delete Document ───────────────────────────────
    print_section(f"TEST 9: Delete Document  →  DELETE /api/v1/documents/{doc_id}")
    confirm = input("\n  Delete this document from DB and disk? (y/n): ").strip().lower()
    if confirm == "y":
        r = httpx.delete(f"{BASE_URL}/api/v1/documents/{doc_id}")
        print_result(r)
        if r.status_code == 200:
            print("  ✅ Document deleted successfully!")
    else:
        print("  Skipped deletion.")

    # ── DONE ──────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("  ALL TESTS COMPLETE ✅")
    print(DIVIDER + "\n")

if __name__ == "__main__":
    run()
