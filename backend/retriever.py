from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from loader import load_and_split
import os
import warnings

warnings.filterwarnings("ignore")  # Tắt warning

# Embedding model
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

DB_PATH = "../vector_db"


def get_retriever(k: int = 6):
    """
    Trả về retriever với k động (Agentic RAG friendly)

    Args:
        k (int): số lượng document cần retrieve
                 - Câu hỏi thường: 6
                 - Câu hỏi so sánh / cao nhất / thấp nhất: 15–25
    """

    if not os.path.exists(DB_PATH):
        print("📦 Đang tạo vector DB lần đầu...")
        docs = load_and_split()
        db = Chroma.from_documents(
            docs,
            embeddings,
            persist_directory=DB_PATH
        )
        print("✅ Tạo xong vector DB!")
    else:
        db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embeddings
        )

    return db.as_retriever(
        search_kwargs={"k": k}
    )
