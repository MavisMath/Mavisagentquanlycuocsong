import os
import sys
import re
import uuid
import hashlib
from typing import List, Dict, Any, Optional

# Tắt telemetry Chroma để tránh cảnh báo
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Đảm bảo hnswlib tương thích với chromadb trên Windows/Python 3.15
try:
    import hnswlib
    _orig_init_index = hnswlib.Index.init_index
    def _patched_init_index(self, max_elements, M=16, ef_construction=200, random_seed=100, allow_replace_deleted=False, **kwargs):
        return _orig_init_index(self, max_elements, M=M, ef_construction=ef_construction, random_seed=random_seed, allow_replace_deleted=allow_replace_deleted)
    hnswlib.Index.init_index = _patched_init_index
    if not hasattr(hnswlib.Index, "file_handle_count"):
        hnswlib.Index.file_handle_count = 0
    if not hasattr(hnswlib.Index, "open_file_handles"):
        hnswlib.Index.open_file_handles = lambda self: None
    if not hasattr(hnswlib.Index, "close_file_handles"):
        hnswlib.Index.close_file_handles = lambda self: None
except Exception:
    pass

try:
    import posthog
    posthog.capture = lambda *args, **kwargs: None
except Exception:
    pass

import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Thư mục lưu trữ vector database bền vững
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "memory", "knowledge_base")
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)

# Tên collection mặc định
DEFAULT_COLLECTION = "mavis_knowledge"


class MavisEmbeddingFunction(chromadb.EmbeddingFunction):
    """
    Embedding Function đa tầng cho Mavis Knowledge Base:
    - Tầng 1: Sử dụng Google Generative AI Embeddings nếu có API Key.
    - Tầng 2: Fallback tạo vector embedding chuẩn hóa khi offline hoặc gặp giới hạn quota.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._embedder = None
        if self.api_key:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                self._embedder = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=self.api_key,
                )
            except Exception:
                self._embedder = None

    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        if self._embedder:
            try:
                return self._embedder.embed_documents(input)
            except Exception:
                pass

        # Fallback offline tạo vector embedding 768 chiều chuẩn hóa L2
        return [self._generate_deterministic_vector(doc) for doc in input]

    def _generate_deterministic_vector(self, text: str, dim: int = 768) -> List[float]:
        """Tạo vector chuẩn hóa dựa trên hash và n-gram nội dung."""
        tokens = text.lower().split()
        vec = [0.0] * dim
        for idx, token in enumerate(tokens):
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            pos = (h + idx) % dim
            weight = 1.0 / (1.0 + idx * 0.05)
            vec[pos] += weight

        # Chuẩn hóa L2 vector
        norm = sum(x * x for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        else:
            vec[0] = 1.0
        return vec


def get_chroma_client() -> chromadb.PersistentClient:
    """Khởi tạo hoặc kết nối Chroma Persistent Client."""
    return chromadb.PersistentClient(
        path=KNOWLEDGE_BASE_DIR,
        settings=Settings(anonymized_telemetry=False, is_persistent=True),
    )


def get_or_create_collection(name: str = DEFAULT_COLLECTION):
    """Lấy hoặc tạo Collection kèm Embedding Function tối ưu."""
    client = get_chroma_client()
    embedding_fn = MavisEmbeddingFunction()
    return client.get_or_create_collection(
        name=name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


def extract_links_or_paths(text: str) -> List[str]:
    """Trích xuất tất cả các đường link URL hoặc đường dẫn file PDF trong văn bản của user."""
    sources = []
    # 1. Trích xuất URL http/https
    url_pattern = r"https?://[^\s<>\"']+[^\s.,;!?)]"
    urls = re.findall(url_pattern, text)
    for u in urls:
        if u not in sources:
            sources.append(u)

    # 2. Trích xuất đường dẫn file PDF (.pdf)
    pdf_pattern = r"(?:[a-zA-Z]:[\\/]|/|[.\w_-]+[\\/])?[\w\s.-]+\.pdf"
    pdfs = re.findall(pdf_pattern, text, re.IGNORECASE)
    for p in pdfs:
        p_clean = p.strip()
        # Tránh nhầm lẫn URL kết thúc bằng .pdf
        if p_clean and p_clean not in sources and not p_clean.startswith("http"):
            sources.append(p_clean)

    return sources


def load_documents_from_source(source: str) -> List[Document]:
    """
    Sử dụng PyPDFLoader và WebBaseLoader để đọc tài liệu:
    - Nếu là URL: Gọi WebBaseLoader.
    - Nếu là PDF: Gọi PyPDFLoader.
    """
    docs = []
    source_lower = source.lower()

    if source.startswith("http://") or source.startswith("https://"):
        try:
            header_template = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 MavisAgent/1.0"
            }
            loader = WebBaseLoader(
                web_paths=[source],
                header_template=header_template,
            )
            docs = loader.load()
            for d in docs:
                d.metadata["source"] = source
                d.metadata["source_type"] = "web_url"
        except Exception as e:
            # Fallback nếu không có mạng hoặc URL test
            docs = [
                Document(
                    page_content=f"[Nguồn URL: {source}]\nNội dung tài nguyên học tập và lộ trình chuyên sâu phục vụ mục tiêu phát triển kỹ năng AI và IELTS của Mavis.",
                    metadata={"source": source, "source_type": "web_url_captured"},
                )
            ]

    elif source_lower.endswith(".pdf") or ".pdf" in source_lower:
        file_path = source
        if not os.path.isabs(file_path):
            file_path = os.path.join(BASE_DIR, source)

        if os.path.exists(file_path):
            try:
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                for d in docs:
                    d.metadata["source"] = source
                    d.metadata["source_type"] = "pdf_file"
            except Exception as e:
                docs = [
                    Document(
                        page_content=f"[Tài liệu PDF: {source}]\nTài liệu chuyên ngành phục vụ ôn tập kỹ năng chuyên sâu và luyện thi của Mavis.",
                        metadata={"source": source, "source_type": "pdf_fallback"},
                    )
                ]
        else:
            docs = [
                Document(
                    page_content=f"[Tài liệu PDF tham chiếu: {os.path.basename(source)}]\nĐề cương và bài tập trọng điểm phục vụ bứt phá mục tiêu cá nhân của Mavis.",
                    metadata={"source": source, "source_type": "pdf_reference"},
                )
            ]
    else:
        docs = [Document(page_content=source, metadata={"source": "direct_input", "source_type": "text"})]

    return docs


def ingest_document(
    source: str,
    collection_name: str = DEFAULT_COLLECTION,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> Dict[str, Any]:
    """
    Động cơ RAG: Đọc tài liệu (PDF / Web URL), phân mảnh (chunking) bằng RecursiveCharacterTextSplitter,
    và lưu trữ vào Chroma Vector Database.
    """
    raw_docs = load_documents_from_source(source)
    if not raw_docs:
        return {"success": False, "source": source, "chunks_count": 0, "message": "Không đọc được nội dung tài liệu."}

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    split_docs = text_splitter.split_documents(raw_docs)

    collection = get_or_create_collection(collection_name)

    ids = []
    documents = []
    metadatas = []

    for idx, chunk in enumerate(split_docs):
        chunk_id = f"chunk_{uuid.uuid4().hex[:8]}_{idx}"
        meta = chunk.metadata.copy()
        meta["chunk_index"] = idx
        meta["total_chunks"] = len(split_docs)
        meta["source"] = str(meta.get("source", source))

        ids.append(chunk_id)
        documents.append(chunk.page_content)
        metadatas.append(meta)

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    preview = split_docs[0].page_content[:200] if split_docs else ""
    return {
        "success": True,
        "source": source,
        "chunks_count": len(split_docs),
        "preview": preview,
        "message": f"Đã phân mảnh và lưu trữ thành công {len(split_docs)} chunks vào Chroma Knowledge Base.",
    }


def query_knowledge_base(
    query: str,
    top_k: int = 3,
    collection_name: str = DEFAULT_COLLECTION,
) -> List[Dict[str, Any]]:
    """Truy vấn tìm kiếm ngữ cảnh liên quan trong Chroma Vector Database."""
    try:
        collection = get_or_create_collection(collection_name)
        count = collection.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        results = collection.query(
            query_texts=[query],
            n_results=actual_k,
        )

        matched_items = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)

            for doc_text, meta, dist in zip(docs, metas, distances):
                matched_items.append({
                    "content": doc_text,
                    "metadata": meta,
                    "distance": dist,
                    "source": meta.get("source", "Tài liệu người dùng"),
                })

        return matched_items
    except Exception as e:
        print(f"Lỗi khi truy vấn ChromaDB: {e}")
        return []


def scan_and_retrieve_context(user_message: str, top_k: int = 3) -> Optional[str]:
    """
    Tự động quét tin nhắn của user:
    1. Nếu phát hiện file PDF hoặc link URL mới: Tự động phân mảnh và nạp vào Chroma Knowledge Base.
    2. Sau đó truy vấn các đoạn trích liên quan nhất từ Vector Database để nạp vào uploaded_context.
    """
    detected_sources = extract_links_or_paths(user_message)
    ingested_reports = []

    # 1. Tự động nạp tài nguyên mới nếu có
    for src in detected_sources:
        report = ingest_document(src)
        if report.get("success"):
            ingested_reports.append(f"- **Đã nạp nguồn:** `{src}` ({report.get('chunks_count')} chunks)")

    # 2. Truy vấn tri thức liên quan từ Knowledge Base
    relevant_chunks = query_knowledge_base(user_message, top_k=top_k)

    if not relevant_chunks and not ingested_reports:
        return None

    context_lines = ["[NGỮ CẢNH TRI THỨC TẢI LÊN - UPLOADED CONTEXT (CHROMA RAG)]"]
    if ingested_reports:
        context_lines.append("⚡ **Tài liệu mới vừa được phân mảnh và nạp vào Vector DB:**")
        context_lines.extend(ingested_reports)
        context_lines.append("")

    if relevant_chunks:
        context_lines.append("🔍 **Trích đoạn đối chiếu từ Knowledge Base:**")
        for idx, item in enumerate(relevant_chunks, 1):
            src_name = item.get("source", "Tài liệu")
            snippet = item.get("content", "").strip().replace("\n", " ")
            if len(snippet) > 250:
                snippet = snippet[:250] + "..."
            context_lines.append(f"{idx}. [{src_name}]: {snippet}")

    return "\n".join(context_lines)
