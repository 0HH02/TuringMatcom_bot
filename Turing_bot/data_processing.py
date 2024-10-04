# data_processing.py
import PyPDF2
from sklearn.neighbors import NearestNeighbors
import numpy as np
import os
import copy
from tqdm import tqdm

from utils import update_or_send_message, load_data, save_data
from ai import generate_embeddings

EMBEDDINGS_FILE = "embeddings_data.pkl"
INDEX_FILE = "vector_index.pkl"


def extract_text_from_pdf(pdf_file):
    print("Extrayendo texto del PDF...")
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
    print("Texto extraído del PDF correctamente.")
    return pages_text


def chunk_text(chat_id, pages_text, chunk_size=500):
    print("Dividiendo el texto en fragmentos...")
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
    print("Texto dividido en fragmentos correctamente.")
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


def load_existing_data():
    if os.path.exists(EMBEDDINGS_FILE) and os.path.exists(INDEX_FILE):
        print("Cargando datos existentes...")
        existing_chunks = load_data(EMBEDDINGS_FILE)
        index = load_data(INDEX_FILE)
        return existing_chunks, index
    return None, None


def read_pdf_file(pdf_file_path):
    with open(pdf_file_path, "rb") as pdf_file:
        return extract_text_from_pdf(pdf_file)


def procesar_libros():
    libros_folder = "Libros"
    if os.path.exists(libros_folder):
        print("Buscando archivos PDF en la carpeta 'Libros'...")
        pdf_files = [
            os.path.join(root, f)
            for root, _, files in os.walk(libros_folder)
            for f in files
            if f.endswith(".pdf")
        ]
        if pdf_files:
            existing_chunks, index = load_existing_data()
            if existing_chunks is not None and index is not None:
                new_chunks = []
                processed_files = set(chunk["book_title"] for chunk in existing_chunks)
                for pdf_file_path in pdf_files:
                    if pdf_file_path not in processed_files:
                        print(f"Procesando nuevo archivo PDF: {pdf_file_path}...")
                        pages_text = read_pdf_file(pdf_file_path)
                        new_chunks.extend(chunk_text(None, pages_text))  # Igual aquí
                if new_chunks:
                    print("Generando embeddings para los nuevos fragmentos...")
                    for chunk in tqdm(
                        new_chunks, desc="Generando embeddings", unit="fragmento"
                    ):
                        generate_embeddings([chunk])
                    index, chunks = create_vector_store_sklearn(
                        existing_chunks, new_chunks=new_chunks
                    )
                    save_data(EMBEDDINGS_FILE, chunks)
                    save_data(INDEX_FILE, index)
                    return copy.deepcopy(index), chunks.copy()
                else:
                    return copy.deepcopy(index), existing_chunks.copy()
            else:
                print("Procesando todos los archivos PDF...")
                all_pages_text = []
                for pdf_file_path in pdf_files:
                    pages_text = read_pdf_file(pdf_file_path)
                    all_pages_text.extend(pages_text)
                if all_pages_text:
                    chunks = chunk_text(None, all_pages_text)
                    for chunk in tqdm(
                        new_chunks, desc="Generando embeddings", unit="fragmento"
                    ):
                        generate_embeddings([chunk])
                    index, chunks = create_vector_store_sklearn(chunks)
                    save_data(EMBEDDINGS_FILE, chunks)
                    save_data(INDEX_FILE, index)
                    return copy.deepcopy(index), chunks.copy()
        else:
            print("No se encontraron archivos PDF en la carpeta 'Libros'.")
    else:
        print(
            "La carpeta 'Libros' no existe. Por favor, asegúrate de que la carpeta esté creada y contenga archivos PDF."
        )
