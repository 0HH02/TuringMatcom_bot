# data_processing.py
import PyPDF2
from sklearn.neighbors import NearestNeighbors
import numpy as np

from utils import update_or_send_message


def extract_text_from_pdf(chat_id, pdf_file):
    update_or_send_message(chat_id, "Extrayendo texto del PDF...")
    reader = PyPDF2.PdfReader(pdf_file)
    pages_text = []
    for page_number, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_text.append(
                {
                    "page_number": page_number + 1,
                    "text": text,
                    "book_title": pdf_file.name,
                }
            )
    update_or_send_message(chat_id, "Texto extraído del PDF correctamente.")
    return pages_text


def chunk_text(chat_id, pages_text, chunk_size=500):
    update_or_send_message(chat_id, "Dividiendo el texto en fragmentos...")
    chunks = []
    for page in pages_text:
        words = page["text"].split()
        for i in range(0, len(words), chunk_size):
            chunk_text = " ".join(words[i : i + chunk_size])
            chunk = {
                "page_number": page["page_number"],
                "text": chunk_text,
                "book_title": page["book_title"],
            }
            chunks.append(chunk)
    update_or_send_message(chat_id, "Texto dividido en fragmentos correctamente.")
    return chunks


def create_vector_store_sklearn(existing_chunks, new_chunks=None):
    if new_chunks:
        embeddings = np.array(
            [chunk["embedding"] for chunk in existing_chunks + new_chunks]
        )
        chunks = existing_chunks + new_chunks
    else:
        embeddings = np.array([chunk["embedding"] for chunk in existing_chunks])
        chunks = existing_chunks
    nbrs = NearestNeighbors(n_neighbors=5, algorithm="ball_tree").fit(embeddings)
    return nbrs, chunks


def search_similar_chunks_sklearn(question_embedding, index_model, chunks, top_k=5):
    question_embedding = np.array(question_embedding).reshape(1, -1)
    distances, indices = index_model.kneighbors(question_embedding, n_neighbors=top_k)
    results = [chunks[idx] for idx in indices[0]]
    return results
