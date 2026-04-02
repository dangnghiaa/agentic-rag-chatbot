
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os


def load_and_split():
    docs = []
    for file_name in os.listdir("../data"):
        if file_name.lower().endswith(".txt"):
            file_path = os.path.join("../data", file_name)
            loader = TextLoader(file_path, encoding="utf-8")
            docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(docs)