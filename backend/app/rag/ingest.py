# app/rag/ingest.py

import os
from typing import List, Optional, Dict, Any

from app.config import settings
from app.rag.vectorstore import upsert_document_to_namespace

ALLOWED = {".pdf", ".txt", ".md"}


def ingest_folder_to_pinecone(file_list: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    ✅ Smart ingest supported:
    - If file_list is provided → ingest ONLY those files from DATA_DIR
    - Returns structured result for UI
    """
    print("\n🚀 Starting Pinecone ingest...")

    folder = getattr(settings, "DATA_DIR", "")
    namespace = getattr(settings, "PINECONE_NAMESPACE", "global-medical")

    # -------- Checks --------
    if not folder:
        return {"ok": False, "error": "DATA_DIR not set in .env"}

    if not os.path.exists(folder):
        return {"ok": False, "error": f"Folder not found: {folder}"}

    if getattr(settings, "VECTOR_BACKEND", "").lower() != "pinecone":
        return {"ok": True, "message": "VECTOR_BACKEND not pinecone -> skipping ingest", "processed": 0, "skipped": 0, "processed_files": []}

    if not getattr(settings, "PINECONE_API_KEY", ""):
        return {"ok": False, "error": "Pinecone API key missing"}

    print(f"📂 DATA_DIR = {folder}")
    print(f"📌 Namespace = {namespace}")

    processed_files: List[str] = []
    skipped_files: List[str] = []
    failed_files: List[Dict[str, str]] = []

    # Normalize file_list (if given)
    wanted = None
    if file_list:
        wanted = set([os.path.basename(x) for x in file_list])

    for root, _, files in os.walk(folder):
        for fn in files:
            base = os.path.basename(fn)
            ext = os.path.splitext(base)[1].lower()

            if ext not in ALLOWED:
                skipped_files.append(base)
                continue

            # If smart list given, skip others
            if wanted is not None and base not in wanted:
                continue

            path = os.path.join(root, fn)
            try:
                print(f"➡️ Processing: {base}")
                upsert_document_to_namespace(namespace=namespace, filepath=path)
                processed_files.append(base)
                print(f"✅ Indexed: {base}")
            except Exception as e:
                print(f"❌ Failed: {base} | Error: {e}")
                failed_files.append({"file": base, "error": str(e)})

    msg = "Ingest complete"
    if wanted is not None and len(processed_files) == 0 and len(failed_files) == 0:
        msg = "No matching files found to ingest"

    return {
        "ok": True if len(failed_files) == 0 else False,
        "message": msg,
        "namespace": namespace,
        "processed": len(processed_files),
        "skipped": len(skipped_files),
        "processed_files": processed_files,
        "failed": failed_files,
    }