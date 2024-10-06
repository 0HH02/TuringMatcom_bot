# ai.py
import google.generativeai as genai
import time

from config import GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")


def generate_embeddings(chunks, model_name="models/embedding-001"):
    embeddings = []
    for chunk in chunks:
        response = genai.embed_content(
            model=model_name,
            content=chunk["text"],
            task_type="RETRIEVAL_DOCUMENT",
        )
        chunk["embedding"] = response["embedding"]
        embeddings.append(chunk["embedding"])
    return embeddings


def generate_answer(question, context_chunks, generation_model="gemini-1.5-flash"):
    context_text = "\n".join([chunk["text"] for chunk in context_chunks])
    book_references = ", ".join(set([chunk["book_title"] for chunk in context_chunks]))
    book_names = [
        "\n- " + os.path.basename(ref).replace("_", " ").replace(".pdf", "")
        for ref in book_references.split(", ")
    ]
    book_references_formatted = "\n\n".join(book_names)
    prompt = (
        f"Eres un profesor de la Universidad de La Habana con conocimientos en Matemática, Ciencia de la Computación y Ciencia de Datos. "
        f"Siempre respondes usando primero una información objetiva y luego intentas explicarlo de manera intuitiva poniendo ejemplos prácticos. "
        f"Tienes en cuenta que estás escribiendo por telegram, por lo que usas el formato Markdown para dar formato a tu respuesta. "
        f"Utilizando el siguiente contexto, responde la pregunta e indica de qué libro se obtuvo cada fragmento.\n\n"
        f"Contexto:\n{context_text}\n\n"
        f"Pages:\n{get_pages_from_chunks(context_chunks)}\n\n"
        f"Book references:\n{book_references_formatted}\n\n"
        f"Pregunta: {question}"
    )
    gen_model = genai.GenerativeModel(model_name=generation_model)
    response = gen_model.generate_content({"role": "user", "parts": [prompt]})
    return response.text, get_pages_from_chunks(context_chunks), book_references


def evaluar_trivialidad(question, generation_model="gemini-1.5-flash"):
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
    instruction = f"Eres un tutor virtual creado por estudiantes de MATCOM para ayudar a otros estudiantes en su estudio independientemente. Siempre das respuestas objetivas. Tú objetivo principal es que el estudiante entienda los ejercicios en primer lugar de forma intuitiva y luego algorítmica. Tienes acceso a los libros de las asignaturas y respondes según la documentación. Puedes hablar de cualquier cosa pero te especializas en matemáticas y progración ya que tienes como base de conocimientos todos los libros que utilizan los estudiantes en la carrera. Fuiste creado por Carlos Mario Chang Jardínez de Ciencias de la Computación y Alberto Enrique Marichal Fonseca de Ciencias de Datos en 2 días en octubre del 2024. Pregunta: {message}"
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
