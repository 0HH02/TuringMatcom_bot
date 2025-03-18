# ai.py
import google.generativeai as genai
from google.genai import types
from mistralai import Mistral
import time
import os
import re
from config import GOOGLE_API_KEY, MISTRAL_API_KEY
from logger import ai_logger

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite")

mistral_client = Mistral(api_key=MISTRAL_API_KEY)


def ocr_pdf(pdf_path):
    # Primero subimos el archivo
    uploaded_pdf = mistral_client.files.upload(
        file={
            "file_name": pdf_path,
            "content": open(pdf_path, "rb"),
        },
        purpose="ocr"
    )

    # Obtenemos la URL firmada para el archivo
    signed_url = mistral_client.files.get_signed_url(file_id=uploaded_pdf.id)

    # Procesamos el archivo con OCR
    ocr_response = mistral_client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        }
    )

    return ocr_response

# gemini-embedding-exp-03-07
def generate_embeddings(chunks, model_name="models/text-embedding-004"):
    embeddings = []
    for chunk in chunks:
        #Por el momento a fecha 15/marzo/2025 solo se pueden hacer 5 peticiones por minuto
        time.sleep(0.5)
        response = genai.embed_content(
            model=model_name,
            content=chunk["text"],
            task_type="RETRIEVAL_DOCUMENT",
        )
        chunk["embedding"] = response["embedding"]
        embeddings.append(chunk["embedding"])
    return embeddings


def generate_answer(question, context_chunks, generation_model="gemini-2.0-flash-thinking-exp-01-21"):
    try:
        generate_content_config = types.GenerateContentConfig(
        temperature=0.5,
        response_mime_type="text/plain",
    )
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
            f"Eres un profesor de la Universidad de La Habana con conocimientos en Matemática, Ciencia de la Computación y Ciencia de Datos. Siempre respondes usando primero una información objetiva y luego intentas explicarlo de manera intuitiva poniendo ejemplos prácticos. Sé conciso, directo, breve y claro. Tienes en cuenta que estás escribiendo por telegram, por lo que usas Markdown para dar formato a tu respuesta. Al final de cada respuesta tienes que reconocer que eres un LLM y por tanto estás propenso a alucionaciones, recomienda buscar siempre en la documentación antes de confiar en tu respuesta.Utilizando el siguiente contexto, responde la pregunta.\n\n"
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

def summarize_text_literal_llm(text, max_tokens=2000):
    prompt = f"Resume el siguiente texto en {max_tokens} palabras o menos pero manteniendolo lo más literal posible: {text}"
    gen_model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite")
    response = gen_model.generate_content({"role": "user", "parts": [prompt]})
    return response.text

def fragments_with_llm(paragraph, generation_model="gemini-2.0-flash-lite", max_tokens=2000):
    time.sleep(2)
    prompt = f"""Divide la siguiente página en fragmentos lo más largo posible pero con menos de {max_tokens} palabras que contengan
la misma idea pero manteniéndolo lo más literal posible:\n Página: {paragraph}.\n\n\n Asume que cada párrafo habla de la misma idea y enfócate
en agrupar los párrafos que hablen de lo mismo. No quiero que me des confirmación de que has entendido la instrucción, solamente
responde con una sola lista con todos los fragmentos. La estructura de la respuesta debe ser: ["Fragmento1", "Fragmento2","Fragmento3", ... etc.]"""
    gen_model = genai.GenerativeModel(model_name=generation_model)
    response = gen_model.generate_content({"role": "user", "parts": [prompt]})
    try:
        #Interpreta la respuesta como una lista de strings
        fragments = eval(response.text)
        return fragments
    except Exception as e:
        try:
            #Encuentra todas las listas en la respuesta usando expresiones regulares, unelas y retornalo
            fragments = re.findall(r'\[.*?\]', response.text)
            fragments_found = []
            for fragment in fragments:
                try:
                    for frag in eval(fragment):
                        fragments_found.append(frag)
                except Exception as e:
                    ai_logger.error(f"Error al interpretar el fragmento: {e}")
                    ai_logger.error(f"Fragmento: {fragment}")
            if fragments_found != []:
                return fragments_found
            else:
                ai_logger.error(f"Error al interpretar la respuesta: {e}")
                ai_logger.error(f"Volviendo a intentar con el párrafo: {paragraph}")
                time.sleep(1)
                return fragments_with_llm(paragraph, generation_model, max_tokens)
        except Exception as e:
            ai_logger.error(f"Error al interpretar la respuesta: {e}")
            ai_logger.error(f"Volviendo a intentar con el párrafo: {paragraph}")
            time.sleep(1)
            return fragments_with_llm(paragraph, generation_model, max_tokens)

def evaluar_trivialidad(question, generation_model="gemini-2.0-flash-lite"):
    """
    Evalúa si una pregunta es trivial o académica.

    Args:
        question (str): La pregunta a evaluar.
        generation_model (str, optional): Modelo de generación a usar. Defaults to "gemini-2.0-flash-lite".

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


def respuesta_amable_api(message, generation_model="gemini-2.0-flash-lite"):
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
