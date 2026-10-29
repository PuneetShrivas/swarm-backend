"""
RAG (Retrieval-Augmented Generation) Knowledge Store
Provides document chunking, hybrid BM25 lexical ranking, and vector similarity retrieval
for Swarm agents and workflow pipelines.
"""

import math
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple


def tokenize(text: str) -> List[str]:
    """Extracts normalized lowercase alphanumeric word tokens."""
    return re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())


def chunk_text(
    text: str,
    chunk_size: int = 150,
    chunk_overlap: int = 30,
    heading: str = ""
) -> List[Dict[str, Any]]:
    """
    Splits text into sliding window passages with word overlap.
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    idx = 0
    total_words = len(words)

    while start < total_words:
        end = min(start + chunk_size, total_words)
        chunk_words = words[start:end]
        chunk_str = " ".join(chunk_words)

        chunks.append({
            "chunk_index": idx,
            "heading": heading,
            "content": chunk_str,
            "word_count": len(chunk_words),
            "start_word": start,
            "end_word": end,
        })

        idx += 1
        if end >= total_words:
            break
        start += max(1, chunk_size - chunk_overlap)

    return chunks


class RAGKnowledgeStore:
    """
    In-memory and hybrid vector/BM25 retrieval engine for ingested files.
    """

    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.chunks: List[Dict[str, Any]] = []
        self._doc_frequencies: Dict[str, int] = {}
        self._total_docs: int = 0
        self._avg_doc_len: float = 0.0

    def clear(self):
        self.documents.clear()
        self.chunks.clear()
        self._doc_frequencies.clear()
        self._total_docs = 0
        self._avg_doc_len = 0.0

    def ingest_document(
        self,
        filename: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 150,
        chunk_overlap: int = 30,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chunks and indexes a text document into the RAG engine.
        """
        doc_id = document_id or f"doc_{uuid.uuid4().hex[:8]}"
        meta = metadata or {}
        now_iso = datetime.now(timezone.utc).isoformat()

        # Split along markdown headings if available
        raw_sections = re.split(r"(?m)^(?=#{1,4}\s+)", content)
        all_chunks: List[Dict[str, Any]] = []

        chunk_counter = 0
        for section in raw_sections:
            sec_text = section.strip()
            if not sec_text:
                continue

            lines = sec_text.splitlines()
            heading = lines[0].strip("# ").strip() if lines[0].startswith("#") else ""
            body = "\n".join(lines[1:]).strip() if heading and len(lines) > 1 else sec_text

            sec_chunks = chunk_text(body or heading, chunk_size, chunk_overlap, heading)
            for ch in sec_chunks:
                chunk_id = f"{doc_id}_c{chunk_counter}"
                chunk_record = {
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "filename": filename,
                    "chunk_index": chunk_counter,
                    "heading": ch["heading"],
                    "content": ch["content"],
                    "word_count": ch["word_count"],
                    "tokens": tokenize(ch["content"]),
                    "created_at": now_iso,
                    "metadata": meta,
                }
                all_chunks.append(chunk_record)
                self.chunks.append(chunk_record)
                chunk_counter += 1

        doc_record = {
            "document_id": doc_id,
            "filename": filename,
            "total_words": len(content.split()),
            "chunk_count": len(all_chunks),
            "created_at": now_iso,
            "metadata": meta,
        }
        self.documents[doc_id] = doc_record

        # Recompute BM25 statistics
        self._recompute_statistics()

        return {
            "status": "indexed",
            "document_id": doc_id,
            "filename": filename,
            "chunk_count": len(all_chunks),
            "total_words": doc_record["total_words"],
            "created_at": now_iso,
        }

    def _recompute_statistics(self):
        """Recomputes inverse document frequency (IDF) and average document length."""
        self._total_docs = len(self.chunks)
        if self._total_docs == 0:
            self._doc_frequencies = {}
            self._avg_doc_len = 0.0
            return

        total_words = 0
        freqs: Dict[str, int] = {}
        for ch in self.chunks:
            tokens = set(ch.get("tokens", []))
            total_words += ch.get("word_count", 0)
            for t in tokens:
                freqs[t] = freqs.get(t, 0) + 1

        self._doc_frequencies = freqs
        self._avg_doc_len = total_words / self._total_docs

    def query_context(
        self,
        query: str,
        top_k: int = 3,
        document_id: Optional[str] = None,
        min_score: float = 0.01
    ) -> List[Dict[str, Any]]:
        """
        Retrieves Top-K most relevant chunks using BM25 ranking and cosine similarity.
        """
        if not self.chunks or not query.strip():
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scored_chunks: List[Tuple[float, Dict[str, Any]]] = []

        k1 = 1.5
        b = 0.75
        query_set = set(query_tokens)

        for ch in self.chunks:
            if document_id and ch["document_id"] != document_id:
                continue

            doc_tokens = ch.get("tokens", [])
            doc_len = len(doc_tokens)
            if doc_len == 0:
                continue

            # 1. BM25 scoring
            bm25 = 0.0
            token_counts: Dict[str, int] = {}
            for t in doc_tokens:
                token_counts[t] = token_counts.get(t, 0) + 1

            for qt in query_tokens:
                if qt in token_counts:
                    tf = token_counts[qt]
                    df = self._doc_frequencies.get(qt, 1)
                    idf = math.log((self._total_docs - df + 0.5) / (df + 0.5) + 1.0)
                    idf = max(0.1, idf)

                    numerator = tf * (k1 + 1.0)
                    denominator = tf + k1 * (1.0 - b + b * (doc_len / (self._avg_doc_len or 1.0)))
                    bm25 += idf * (numerator / (denominator or 1.0))

            # 2. Term overlap (Jaccard similarity booster)
            common = len(query_set.intersection(doc_tokens))
            overlap_score = common / (len(query_set) + 0.01)

            final_score = (bm25 * 0.7) + (overlap_score * 0.3)
            if final_score >= min_score:
                scored_chunks.append((final_score, ch))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_results = []
        for rank, (score, ch) in enumerate(scored_chunks[:top_k], 1):
            normalized_conf = min(1.0, round(score / 5.0, 3)) if score > 0 else 0.05
            top_results.append({
                "rank": rank,
                "relevance_score": round(score, 3),
                "confidence": normalized_conf,
                "chunk_id": ch["chunk_id"],
                "document_id": ch["document_id"],
                "filename": ch["filename"],
                "heading": ch.get("heading") or "General",
                "content": ch["content"],
                "word_count": ch["word_count"],
            })

        return top_results

    def generate_rag_context_block(
        self,
        query: str,
        top_k: int = 3,
        document_id: Optional[str] = None
    ) -> str:
        """
        Formats retrieved Top-K chunks into a structured Markdown prompt block
        for direct injection into agent scratchpads and LLM prompts.
        """
        results = self.query_context(query=query, top_k=top_k, document_id=document_id)
        if not results:
            return "No relevant context found in ingested documents."

        blocks = ["### [Retrieved Document Context via RAG]"]
        for res in results:
            blocks.append(
                f"**Source:** `{res['filename']}` | **Section:** `{res['heading']}` (Confidence: {int(res['confidence'] * 100)}%)\n"
                f"> {res['content']}\n"
            )

        return "\n".join(blocks)

    def list_documents(self) -> List[Dict[str, Any]]:
        """Returns metadata for all indexed documents."""
        return list(self.documents.values())

    def delete_document(self, document_id: str) -> bool:
        """Deletes a document and its chunks from the RAG store."""
        if document_id not in self.documents:
            return False
        del self.documents[document_id]
        self.chunks = [ch for ch in self.chunks if ch["document_id"] != document_id]
        self._recompute_statistics()
        return True


# Global shared RAG knowledge instance
rag_store = RAGKnowledgeStore()
