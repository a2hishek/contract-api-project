from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.tools import tool
import getpass
import os
import json
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

vector_store = Chroma(
        collection_name="my_collection",
        embedding_function=embeddings,
        persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
    )


def pdf_loader(file_path: str):

    loader = PyPDFLoader(Path(file_path))

    docs = loader.load()

    return docs

# print(len(docs))
# print(f"{docs[0].page_content[:200]}\n")

def split_document(docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
    )
    doc_splits = text_splitter.split_documents(docs)

    return doc_splits

# print(len(all_splits))

# vector_1 = embeddings.embed_query(all_splits[0].page_content)
# vector_2 = embeddings.embed_query(all_splits[1].page_content)

# assert len(vector_1) == len(vector_2)
# print(f"Generated vectors of length {len(vector_1)}\n")
# print(vector_1[:10])

# def create_embeddings(doc_splits):
    

#     ids = vector_store.add_documents(documents=doc_splits)

#     return ids

# Note that providers implement different scores; the score here
# is a distance metric that varies inversely with similarity.

# results = vector_store.similarity_search_with_score("The agreement is held between?")
# doc, score = results[0]
# print(f"Score: {score}\n")
# print(doc)

# def retrieve(query: str):
#     retriever = vector_store.as_retriever(
#         search_type="similarity",
#         search_kwargs={"k": 1},
#     )

#     results = retriever.invoke(query)

#     return results[0].page_content


def create_vector_store(file_path: str):
    
    docs = pdf_loader(file_path=file_path)
    doc_splits = split_document(docs=docs)

    ids = vector_store.add_documents(documents=doc_splits)

    return ids


# pdf_files = list(Path("docs").glob("*.pdf"))
# # latest uploaded pdf file
# if pdf_files:
#     file_path = str(max(pdf_files, key=os.path.getctime))    
if os.path.exists("docs/uploaded_files.json"):
    with open("docs/uploaded_files.json", "r") as f:
        data = json.load(f)
        file_path = data.get("current_file", "")

else:
    file_path = ""

# print(file_path)

@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2, filter={"source": file_path})
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

# sample_docs = vector_store.similarity_search("who are the signing parties in the contract ", k=1, filter={"source": "docs\\Contract_document.pdf"})
# if sample_docs:
#     print("Sample metadata source:", sample_docs[0].metadata.get("source"))
#     print("Type:", type(sample_docs[0].metadata.get("source")))
#     print(sample_docs[0].page_content)