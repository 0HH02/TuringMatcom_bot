# ai.py
import google.generativeai as genai
import time
import os

from config import GOOGLE_API_KEY
from logger import ai_logger

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")


def generate_embeddings(chunks, model_name="models/embedding-001"):
    embeddings = []
    for chunk in chunks:
        time.sleep(0.06)
        response = genai.embed_content(
            model=model_name,
            content=chunk["text"],
            task_type="RETRIEVAL_DOCUMENT",
        )
        chunk["embedding"] = response["embedding"]
        embeddings.append(chunk["embedding"])
    return embeddings


def generate_answer(question, context_chunks, generation_model="gemini-1.5-flash"):
    try:
        context_text = "\n".join([chunk["text"] for chunk in context_chunks])
        book_references = ", ".join(
            set([chunk["book_title"] for chunk in context_chunks])
        )
        book_names = [
            "\n- " + os.path.basename(ref).replace("_", " ").replace(".pdf", "")
            for ref in book_references.split(", ")
        ]
        book_references_formatted = "\n\n".join(book_names)
        prompt = (
            f"Eres un profesor de la Universidad de La Habana con conocimientos en Matemática, Ciencia de la Computación y Ciencia de Datos. Siempre respondes usando primero una información objetiva y luego intentas explicarlo de manera intuitiva poniendo ejemplos prácticos. Tienes en cuenta que estás escribiendo por telegram, por lo que usas Markdown para dar formato a tu respuesta. Al final de cada respuesta tienes que reconocer que eres un LLM y por tanto estás propenso a alucionaciones, recomienda buscar siempre en la documentación antes de confiar en tu respuesta.Utilizando el siguiente contexto, responde la pregunta e indica de qué libro se obtuvo cada fragmento.\n\n"
            f"Contexto:\n{context_text}\n\n"
            f"Pages:\n{get_pages_from_chunks(context_chunks)}\n\n"
            f"Book references:\n{book_references_formatted}\n\n"
            f"Pregunta: {question}"
        )
        gen_model = genai.GenerativeModel(model_name=generation_model)
        response = gen_model.generate_content({"role": "user", "parts": [prompt]})
        return response.text, get_pages_from_chunks(context_chunks), book_references
    except Exception as e:
        ai_logger.error(f"Error al generar respuesta: {e}")
        return (
            "Lo siento, ocurrió un error al generar la respuesta. Por favor, intenta nuevamente más tarde.",
            [],
            "",
        )


def evaluar_trivialidad(question, generation_model="gemini-1.5-flash"):
    """
    Evalúa si una pregunta es trivial o académica.

    Args:
        question (str): La pregunta a evaluar.
        generation_model (str, optional): Modelo de generación a usar. Defaults to "gemini-1.5-flash".

    Returns:
        str: "True" si es trivial, "False" si es académica.
    """

    prompt = (
        f"Evalúa si la pregunta es trivial o académica. Si es trivial responde: True, si es académica responde: False. Ejemplo:\n"
        f"Pregunta1: Hola!\nRespuesta1: True\n"
        f"Pregunta2: ¿Cómo se define un límite?\nRespuesta2: False\n"
        f"Pregunta3: ¿Quién o qué eres?\nRespuesta3: True\n"
        f"Pregunta4: ¿Qué es la fórmula de Gauss?\nRespuesta4: False\n"
        f"Pregunta: {question}"
    )
    gen_model = genai.GenerativeModel(model_name=generation_model)
    response = gen_model.generate_content({"role": "user", "parts": [prompt]})
    return response.text


def respuesta_amable_api(message, generation_model="gemini-1.5-flash"):
    gen_model = genai.GenerativeModel(model_name=generation_model)
    instruction = f"Eres un tutor virtual creado por estudiantes de MATCOM para ayudar a otros estudiantes en su estudio independientemente. Siempre das respuestas objetivas. Tú objetivo principal es que el estudiante entienda los ejercicios en primer lugar de forma intuitiva y luego algorítmica. Tienes acceso a los libros de las asignaturas y respondes según la documentación. Puedes hablar de cualquier cosa pero te especializas en matemáticas y progración ya que tienes como base de conocimientos todos los libros que utilizan los estudiantes en la carrera. Fuiste creado por Carlos Mario Chang Jardínez de Ciencias de la Computación y Alberto Enrique Marichal Fonseca de Ciencias de Datos en 2 días en octubre del 2024 en la Universidad de La Habana. Al final de cada respuesta tienes que reconocer que eres un LLM y por tanto estás propenso a alucionaciones, recomienda buscar siempre en la documentación antes de confiar en tu respuesta. Pregunta: {message}"
    response = gen_model.generate_content({"role": "user", "parts": [instruction]})
    return response.text


def get_pages_from_chunks(chunks):
    pages = set(chunk["page_number"] for chunk in chunks)
    return sorted(pages)


def embed_question(question, model_name="models/embedding-001"):
    response = genai.embed_content(
        model=model_name,
        content=question,
        task_type="RETRIEVAL_QUERY",
    )
    return response["embedding"]
