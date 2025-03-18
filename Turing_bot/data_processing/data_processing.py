# data_processing.py

import PyPDF2
from sklearn.neighbors import NearestNeighbors
import numpy as np
import os
import copy

from logger import data_logger
from utils.utils import load_data, save_data
from ai.ai import generate_embeddings, ocr_pdf, summarize_text_literal_llm, fragments_with_llm
from constants import EMBEDDINGS_FILE, INDEX_FILE, LIBROS_FOLDER


def extract_text_from_pdf(pdf_file):
    """
    Extrae el texto de un archivo PDF.

    Args:
        pdf_file (file object): Objeto de archivo PDF abierto en modo binario.

    Returns:
        list[dict]: Lista de diccionarios con el número de página, el texto y el título del libro.
    """
    data_logger.info("Extrayendo texto del PDF...")
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        pages_text = []
        total_text = 0
        for page_number, page in enumerate(reader.pages):
            text = page.extract_text()
            total_text += len(text)
            if text:
                pages_text.append(
                    {
                        "page_number": page_number + 1,
                        "text": text,
                        "book_title": pdf_file.name,
                    }
                )
        if total_text < 500:
            data_logger.info("Texto demasiado corto, usando OCR...")
            ocr_response = ocr_pdf(pdf_file.name)
            for page in ocr_response.pages:
                pages_text.append(
                    {
                        "page_number": page.index,
                        "text": page.markdown,
                        "book_title": pdf_file.name,
                    }
                )
        data_logger.info("Texto extraído del PDF correctamente.")
        return pages_text
    except Exception as e:
        data_logger.error(f"Error al extraer texto: {e}")
        raise


def chunk_text2(pages_text, max_tokens=2000):
    """
    Divide el texto de las páginas en fragmentos más pequeños.

    Args:
        pages_text (list[dict]): Lista de diccionarios con el texto de cada página.
        max_tokens (int, optional): Máximo de tokens/palabras por fragmento. Defaults to 2000.

    Returns:
        list[dict]: Lista de fragmentos de texto.
    """
    data_logger.info("Dividiendo el texto en fragmentos de forma inteligente...")
    chunks = []
    total_pages = len(pages_text)

    for idx, page in enumerate(pages_text, start=1):
        page_text = page["text"]
        page_number = page["page_number"]
        book_title = page["book_title"]

        # Dividir la página en párrafos
        paragraphs = fragments_with_llm(page_text)

        for i in range(len(paragraphs)):
            paragraph = paragraphs[i]
            estimated_chunk_size = len(paragraph.split())
            if estimated_chunk_size > max_tokens:
                data_logger.warning(f"La idea en la página {page_number} excede {max_tokens} palabras ({estimated_chunk_size}). Resumiendo párrafo.")
                paragraph = summarize_text_literal_llm(paragraph, max_tokens) # Implementar esta función con LLM
                paragraph_words_resumido = len(paragraph.split())
                if paragraph_words_resumido > max_tokens:
                    data_logger.error(f"¡Resumen de párrafo en página {page_number} aún excede {max_tokens} palabras ({paragraph_words_resumido})!  Considera reducir aún más o revisar el proceso de resumen.")
                    # Manejar si el resumen sigue siendo demasiado largo.  Aquí optamos por truncar, pero podrías tener otra estrategia.
                    paragraph_words_truncado = max_tokens - 15 # Dejar algo de margen
                    paragraph = " ".join(paragraph.split()[:paragraph_words_truncado])
                    paragraph += " ... (Texto truncado después del resumen por exceso de tamaño)"
            # El chunk actual está lleno, guarda y comienza uno nuevo
            chunks.append({
                "page_number": page_number,
                "text": paragraph,
                "book_title": book_title,
            })

        # Registro de progreso por página
        data_logger.debug(
            f"Fragmentada página {idx} de {total_pages} en '{book_title}'."
        )

    data_logger.info("Texto dividido en fragmentos correctamente (versión mejorada).")
    return chunks

def chunk_text(pages_text):
    """
    Divide el texto de las páginas en fragmentos más pequeños.

    Args:
        pages_text (list[dict]): Lista de diccionarios con el texto de cada página.

    Returns:
        list[dict]: Lista de fragmentos de texto.
    """
    data_logger.info("Dividiendo el texto en fragmentos de forma inteligente...")
    chunks = []
    total_pages = len(pages_text)

    for idx, page in enumerate(pages_text, start=1):
        page_text = page["text"]
        page_number = page["page_number"]
        book_title = page["book_title"]

        # Dividir la página en párrafos
        paragraphs = page_text.split("\n")
        current_chunk = ""
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= 2000: 
                current_chunk += paragraph + "\n"
            else:
                chunks.append({
                    "page_number": page_number,
                    "text": current_chunk,
                    "book_title": book_title,
                })
                current_chunk = paragraph + "\n"

        # Registro de progreso por página
        data_logger.debug(
            f"Fragmentada página {idx} de {total_pages} en '{book_title}'."
        )

    data_logger.info("Texto dividido en fragmentos correctamente (versión mejorada).")
    return chunks


def create_vector_store_sklearn(existing_chunks, new_chunks=None):
    """
    Crea un modelo de vecinos más cercanos usando sklearn.

    Args:
        existing_chunks (list[dict]): Fragmentos de texto existentes.
        new_chunks (list[dict], optional): Nuevos fragmentos de texto. Defaults to None.

    Returns:
        tuple: Modelo de vecinos más cercanos y la lista actualizada de fragmentos.
    """
    if new_chunks:
        embeddings = np.array(
            [chunk["embedding"] for chunk in existing_chunks + new_chunks]
        )
        chunks = existing_chunks + new_chunks
    else:
        embeddings = np.array([chunk["embedding"] for chunk in existing_chunks])
        chunks = existing_chunks
    nbrs = NearestNeighbors(n_neighbors=10, algorithm="ball_tree").fit(embeddings)
    return nbrs, chunks


def search_similar_chunks_sklearn(question_embedding, index_model, chunks, top_k=10):
    """
    Busca los fragmentos de texto más similares a una pregunta dada.

    Args:
        question_embedding (list or np.array): Embedding de la pregunta.
        index_model (NearestNeighbors): Modelo de vecinos más cercanos.
        chunks (list[dict]): Lista de fragmentos de texto.
        top_k (int, optional): Número de fragmentos a retornar. Defaults to 5.

    Returns:
        list[dict]: Lista de fragmentos similares.
    """
    question_embedding = np.array(question_embedding).reshape(1, -1)
    distances, indices = index_model.kneighbors(question_embedding, n_neighbors=top_k)
    results = [chunks[idx] for idx in indices[0]]
    return results


def load_existing_data():
    """
    Carga datos existentes de embeddings e índice si existen.

    Returns:
        tuple: Lista de fragmentos existentes y el modelo de índice, o (None, None) si no existen.
    """
    if os.path.exists(EMBEDDINGS_FILE) and os.path.exists(INDEX_FILE):
        data_logger.info("Cargando datos existentes...")
        existing_chunks = load_data(EMBEDDINGS_FILE)
        index = load_data(INDEX_FILE)
        return existing_chunks, index
    return None, None


def read_pdf_file(pdf_file_path):
    """
    Lee un archivo PDF y extrae su texto.

    Args:
        pdf_file_path (str): Ruta al archivo PDF.

    Returns:
        list[dict]: Lista de diccionarios con el texto extraído.
    """
    with open(pdf_file_path, "rb") as pdf_file:
        return extract_text_from_pdf(pdf_file)


def procesar_libros():
    """
    Procesa todos los libros en la carpeta especificada, extrayendo texto, creando fragmentos,
    generando embeddings y actualizando el índice.

    Returns:
        tuple: Modelo de índice actualizado y lista de fragmentos.
    """
    if not os.path.exists(LIBROS_FOLDER):
        data_logger.error(f"La carpeta '{LIBROS_FOLDER}' no existe.")
        return None, None

    data_logger.info("Buscando archivos PDF en la carpeta 'Libros'...")
    pdf_files = find_pdf_files(LIBROS_FOLDER)
    total_files = len(pdf_files)
    if not pdf_files:
        data_logger.warning("No se encontraron archivos PDF en la carpeta 'Libros'.")
        return None, None

    data_logger.info(f"Se encontraron {total_files} archivos PDF.")
    print(f"Total de libros encontrados: {total_files}")
    existing_chunks, index = load_existing_data()
    new_chunks = get_new_chunks(pdf_files, existing_chunks)

    if new_chunks:
        data_logger.info(
            f"Generando embeddings para {len(new_chunks)} nuevos fragmentos..."
        )
        generate_embeddings(new_chunks)
        index, updated_chunks = create_vector_store_sklearn(
            existing_chunks if existing_chunks != None else [], new_chunks=new_chunks
        )
        save_data(EMBEDDINGS_FILE, updated_chunks)
        save_data(INDEX_FILE, index)
        data_logger.info("Procesamiento completado con nuevos archivos.")
        data_logger.info("¡Se ha completado el proceso de datos!")
        print("¡Se ha completado el proceso de datos!")
        return copy.deepcopy(index), updated_chunks.copy()
    else:
        data_logger.info("No hay nuevos archivos para procesar.")
        data_logger.info("¡Se ha completado el proceso de datos!")
        print("¡Se ha completado el proceso de datos!")
        return copy.deepcopy(index), existing_chunks.copy()


def find_pdf_files(folder: str) -> list[str]:
    """
    Encuentra todos los archivos PDF en una carpeta y sus subcarpetas.

    Args:
        folder (str): Ruta a la carpeta donde buscar archivos PDF.

    Returns:
        list[str]: Lista de rutas completas a los archivos PDF encontrados.
    """
    return [
        os.path.join(root, f)
        for root, _, files in os.walk(folder)
        for f in files
        if f.lower().endswith(".pdf")
    ]


def get_new_chunks(
    pdf_files: list[str], existing_chunks: list[dict[str, any]]
) -> list[dict[str, any]]:
    """
    Identifica y procesa nuevos archivos PDF que no han sido procesados anteriormente.

    Args:
        pdf_files (list[str]): Lista de rutas a archivos PDF.
        existing_chunks (list[dict[str, any]]): Lista de fragmentos ya existentes.

    Returns:
        list[dict]: Lista de nuevos fragmentos de texto.
    """
    processed_files = (
        set(chunk["book_title"] for chunk in existing_chunks)
        if existing_chunks
        else set()
    )
    new_chunks = []
    total_files = len(pdf_files)
    for idx, pdf_file_path in enumerate(pdf_files, start=1):
        file_name = os.path.basename(pdf_file_path)
        for processed_file in processed_files:
            if file_name in processed_file:
                data_logger.debug(
                    f"El archivo '{file_name}' ya ha sido procesado. Saltando..."
                )
                break
        else:
            data_logger.info(
                f"Procesando nuevo archivo PDF ({idx}/{total_files}): {file_name}..."
            )
            pages_text = read_pdf_file(pdf_file_path)
            if not pages_text:
                data_logger.warning(f"No se encontraron páginas en {pdf_file_path}")
                continue
            # chunks = chunk_text2(pages_text)
            chunks = chunk_text(pages_text)

            new_chunks.extend(chunks)
            data_logger.info(
                f"Archivo '{file_name}' procesado y fragmentado correctamente."
            )

    return new_chunks
