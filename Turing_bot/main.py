# main.py
from bot_handlers import bot
from data_processing import (
    extract_text_from_pdf,
    chunk_text,
    create_vector_store_sklearn,
)
from ai import generate_embeddings
from utils import save_data, load_data
import os
import copy

save_index = None
save_chunks = []
EMBEDDINGS_FILE = "embeddings_data.pkl"
INDEX_FILE = "vector_index.pkl"


def procesar_libros():
    global save_index, save_chunks
    libros_folder = "Libros"
    if os.path.exists(libros_folder):
        print("Buscando archivos PDF en la carpeta 'Libros'...")
        pdf_files = [
            os.path.join(libros_folder, f)
            for f in os.listdir(libros_folder)
            if f.endswith(".pdf")
        ]
        if pdf_files:
            if os.path.exists(EMBEDDINGS_FILE) and os.path.exists(INDEX_FILE):
                print("Cargando datos existentes...")
                existing_chunks = load_data(EMBEDDINGS_FILE)
                index = load_data(INDEX_FILE)
                new_chunks = []
                processed_files = set(chunk["book_title"] for chunk in existing_chunks)
                for pdf_file_path in pdf_files:
                    if pdf_file_path not in processed_files:
                        print(f"Procesando nuevo archivo PDF: {pdf_file_path}...")
                        with open(pdf_file_path, "rb") as pdf_file:
                            pages_text = extract_text_from_pdf(
                                None, pdf_file
                            )  # Deberías pasar chat_id si es necesario
                            new_chunks.extend(
                                chunk_text(None, pages_text)
                            )  # Igual aquí
                if new_chunks:
                    print("Generando embeddings para los nuevos fragmentos...")
                    generate_embeddings(new_chunks)
                    index, chunks = create_vector_store_sklearn(
                        existing_chunks, new_chunks=new_chunks
                    )
                    save_data(EMBEDDINGS_FILE, chunks)
                    save_data(INDEX_FILE, index)
                    save_index = copy.deepcopy(index)
                    save_chunks = chunks.copy()
                else:
                    chunks = existing_chunks
                    save_index = copy.deepcopy(index)
                    save_chunks = chunks.copy()
            else:
                print("Procesando todos los archivos PDF...")
                all_pages_text = []
                for pdf_file_path in pdf_files:
                    with open(pdf_file_path, "rb") as pdf_file:
                        pages_text = extract_text_from_pdf(
                            None, pdf_file
                        )  # Pasar chat_id si aplica
                        all_pages_text.extend(pages_text)
                if all_pages_text:
                    chunks = chunk_text(None, all_pages_text)
                    generate_embeddings(chunks)
                    index, chunks = create_vector_store_sklearn(chunks)
                    save_data(EMBEDDINGS_FILE, chunks)
                    save_data(INDEX_FILE, index)
                    save_index = copy.deepcopy(index)
                    save_chunks = chunks.copy()
        else:
            print("No se encontraron archivos PDF en la carpeta 'Libros'.")
    else:
        print(
            "La carpeta 'Libros' no existe. Por favor, asegúrate de que la carpeta esté creada y contenga archivos PDF."
        )


if __name__ == "__main__":
    procesar_libros()
    bot.infinity_polling()
