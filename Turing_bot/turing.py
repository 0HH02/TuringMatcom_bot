import telebot
import os
import google.generativeai as genai
from telebot.types import ReplyKeyboardMarkup
import PyPDF2
import numpy as np
import pickle
from sklearn.neighbors import NearestNeighbors
import copy

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TOKEN = os.getenv("TOKEN")

if not GOOGLE_API_KEY or not TOKEN:
    raise ValueError(
        "API keys no configuradas correctamente. Asegúrese de configurar GOOGLE_API_KEY y TOKEN como variables de entorno."
    )

# Configurar generative AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Configurar token de Telegram
bot = telebot.TeleBot(TOKEN)
dic = {}

save_index = None
save_chunks = []


# Función para extraer texto del PDF y devolverlo por página
def extract_text_from_pdf(pdf_file):
    # update_or_send_message(chat_id, "Extrayendo texto del PDF...")
    reader = PyPDF2.PdfReader(pdf_file)
    pages_text = []
    for page_number, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_text.append(
                {
                    "page_number": page_number + 1,  # Las páginas comienzan en 1
                    "text": text,
                    "book_title": pdf_file.name,  # Agregar título del libro
                }
            )
    # update_or_send_message(chat_id, "Texto extraído del PDF correctamente.")
    return pages_text


# Dividir el texto en fragmentos para la creación de embeddings
def chunk_text(pages_text, chunk_size=500):
    # update_or_send_message(chat_id, "Dividiendo el texto en fragmentos...")
    chunks = []
    for page in pages_text:
        text = page["text"]
        page_number = page["page_number"]
        book_title = page["book_title"]

        words = text.split()  # Dividir el texto en palabras
        for i in range(0, len(words), chunk_size):
            chunk_text = " ".join(words[i : i + chunk_size])
            chunk = {
                "page_number": page_number,
                "text": chunk_text,
                "book_title": book_title,
            }
            chunks.append(chunk)
    # update_or_send_message(chat_id, "Texto dividido en fragmentos correctamente.")
    return chunks


# Generar embeddings usando la API de Gemini
def generate_embeddings(chunks, model_name="models/embedding-001"):
    """update_or_send_message(
        chat_id, "Generando embeddings para los fragmentos de texto..."
    )"""
    embeddings = []
    for chunk in chunks:
        response = genai.embed_content(
            model=model_name,
            content=chunk["text"],
            task_type="RETRIEVAL_DOCUMENT",
        )
        chunk["embedding"] = response["embedding"]
        embeddings.append(chunk["embedding"])
    # update_or_send_message(chat_id, "Embeddings generados correctamente.")
    return embeddings


# Crear la base de datos vectorial con scikit-learn
def create_vector_store_sklearn(existing_chunks, new_chunks=None):
    # update_or_send_message(chat_id, "Creando la base de datos vectorial...")
    if new_chunks:
        embeddings = np.array(
            [chunk["embedding"] for chunk in existing_chunks + new_chunks]
        )
        chunks = existing_chunks + new_chunks
    else:
        embeddings = np.array([chunk["embedding"] for chunk in existing_chunks])
        chunks = existing_chunks
    nbrs = NearestNeighbors(n_neighbors=5, algorithm="ball_tree").fit(embeddings)
    # update_or_send_message(chat_id, "Base de datos vectorial creada correctamente.")
    return nbrs, chunks


# Guardar y cargar embeddings y modelos a/desde disco
def save_data(file_path, data):
    print(f"Guardando datos en {file_path}...")
    with open(file_path, "wb") as f:
        pickle.dump(data, f)
    print(f"Datos guardados en {file_path} correctamente.")


def load_data(file_path):
    print(f"Cargando datos desde {file_path}...")
    with open(file_path, "rb") as f:
        data = pickle.load(f)
    print(f"Datos cargados desde {file_path} correctamente.")
    return data


# Buscar fragmentos similares usando scikit-learn
def search_similar_chunks_sklearn(
    chat_id,
    question,
    index_model,
    chunks,
    embedding_model="models/embedding-001",
    top_k=5,
):
    update_or_send_message(chat_id, "Buscando fragmentos similares...")
    response = genai.embed_content(
        model=embedding_model,
        content=question,
        task_type="RETRIEVAL_QUERY",
    )
    question_embedding = response["embedding"]
    question_embedding = np.array(question_embedding).reshape(1, -1)
    distances, indices = index_model.kneighbors(question_embedding, n_neighbors=top_k)
    results = [chunks[idx] for idx in indices[0]]
    update_or_send_message(chat_id, "Fragmentos similares encontrados correctamente.")
    return results


# Generar respuesta usando el modelo generativo de Gemini
def generate_answer(
    chat_id, question, context_chunks, generation_model="gemini-1.5-flash"
):
    update_or_send_message(chat_id, "Generando respuesta a la pregunta...")
    context_text = "\n".join([chunk["text"] for chunk in context_chunks])
    book_references = ", ".join(set([chunk["book_title"] for chunk in context_chunks]))
    prompt = (
        f"Eres un profesor de la Universidad de La Habana con conocimientos en Matemática, Ciencia de la Computación y Ciencia de Datos. Siempre respondes usando primero una información objetiva y luego intentas explicarlo de manera intuitiva poniendo ejemplos prácticos. Tienes en cuenta que estás escribiendo por telegram, por lo que usas el formato Markdown para dar formato a tu respuesta. Utilizando el siguiente contexto, responde la pregunta e indica de qué libro se obtuvo cada fragmento.\n\n"
        f"Contexto:\n{context_text}\n\n"
        f"Pages:\n{get_pages_from_chunks(context_chunks)}\n\n"
        f"Book references:\n{book_references}\n\n"
        f"Pregunta: {question}\nRespuesta:"
    )
    gen_model = genai.GenerativeModel(model_name=generation_model)
    response = gen_model.generate_content({"role": "user", "parts": [prompt]})
    update_or_send_message(chat_id, "Respuesta generada correctamente.")
    return response.text, get_pages_from_chunks(context_chunks), book_references


# Obtener números de páginas a partir de los fragmentos de contexto
def get_pages_from_chunks(chunks):
    pages = set(chunk["page_number"] for chunk in chunks)
    return sorted(pages)


# Ruta para guardar archivos de embeddings e índice
EMBEDDINGS_FILE = "embeddings_data.pkl"
INDEX_FILE = "vector_index.pkl"


# Procesar libros al iniciar el bot
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
                existing_chunks, index = load_data(EMBEDDINGS_FILE), load_data(
                    INDEX_FILE
                )
                new_chunks = []
                processed_files = set(chunk["book_title"] for chunk in existing_chunks)
                for pdf_file_path in pdf_files:
                    if pdf_file_path not in processed_files:
                        print(f"Procesando nuevo archivo PDF: {pdf_file_path}...")
                        with open(pdf_file_path, "rb") as pdf_file:
                            pages_text = extract_text_from_pdf(pdf_file)
                            new_chunks.extend(chunk_text(pages_text))

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
                        pages_text = extract_text_from_pdf(pdf_file)
                        all_pages_text.extend(pages_text)
                if all_pages_text:
                    chunks = chunk_text(all_pages_text)
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


def evaluar_trivialidad(question=None, generation_model="gemini-1.5-flash"):
    if question:
        prompt = (
            f"Evalúa si la pregunta es trivial o académica. Si es trivial responde: True, si es académica responde: False. Ejemplo:"
            f"Pregunta1: Hola!"
            f"Respuesta1: True"
            f"Pregutna2: ¿Cómo se define un límite?"
            f"Respuesta2: False"
            f"Pregunta3: ¿Quién o qué eres?"
            f"Respuesta3: True"
            f"Pregunta4: ¿Qué es la fórmula de Gauss?"
            f"Respuesta4: False"
            f"Pregunta: {question}"
        )
        gen_model = genai.GenerativeModel(model_name=generation_model)
        response = gen_model.generate_content({"role": "user", "parts": [prompt]})
        return response.text


def api_answer(chat_id, question=None):
    if question:
        update_or_send_message(chat_id, "Buscando respuesta a la pregunta...")
        similar_chunks = search_similar_chunks_sklearn(
            chat_id, question, save_index, save_chunks
        )
        if not similar_chunks:
            update_or_send_message(chat_id, "No se encontraron resultados relevantes.")
            return "No se encontraron resultados relevantes."
        else:
            answer, pages, book_references = generate_answer(
                chat_id, question, similar_chunks
            )
            return f"Respuesta: {answer} \nPáginas relacionadas: {pages} \nReferencias de libros: {book_references}"


# Función para actualizar o enviar mensaje
def update_or_send_message(chat_id, text):
    if "last_message_id" in dic.get(chat_id, {}):
        try:
            bot.send_chat_action(chat_id, "typing")
            bot.edit_message_text(
                chat_id=chat_id, message_id=dic[chat_id]["last_message_id"], text=text
            )
        except:
            bot.send_chat_action(chat_id, "typing")
            msg = bot.send_message(chat_id, text)
            dic[chat_id]["last_message_id"] = msg.message_id
    else:
        bot.send_chat_action(chat_id, "typing")
        msg = bot.send_message(chat_id, text)
        dic.setdefault(chat_id, {})["last_message_id"] = msg.message_id


def respuesta_academica(chat_id, message):
    bot.send_chat_action(chat_id, "typing")
    bot.send_message(
        chat_id,
        api_answer(chat_id, message),
        parse_mode="Markdown",
    )


def respuesta_amable(chat_id, message, generation_model="gemini-1.5-flash"):
    gen_model = genai.GenerativeModel(model_name=generation_model)
    instruction = f"Eres un tutor virtual creado por estudiantes de MATCOM para ayudar a otros estudiantes en su estudio independientemente. Siempre das respuestas objetivas. Tú objetivo principal es que el estudiante entienda los ejercicios en primer lugar de forma intuitiva y luego algorítmica. Tienes acceso a los libros de las asignaturas y respondes según la documentación. Puedes hablar de cualquier cosa pero te especializas en matemáticas y progración ya que tienes como base de conocimientos todos los libros que utilizan los estudiantes en la carrera. Pregunta: {message}"
    response = gen_model.generate_content({"role": "user", "parts": [instruction]})
    bot.send_chat_action(chat_id, "typing")
    bot.send_message(
        chat_id,
        response.text,
        parse_mode="Markdown",
    )


def enviar_doc(doc, message):
    ruta = ""
    if doc == "Libros":
        ruta += "Libros/" + dic[message.chat.id]["asignatura"]
        lista_lib = os.listdir(ruta)
        if len(lista_lib) != 0:
            for i in lista_lib:
                with open(ruta + "/" + f"{i}", "rb") as a:
                    try:
                        bot.send_chat_action(message.chat.id, "upload_document")
                        bot.send_document(message.chat.id, a)
                    except Exception as e:
                        bot.send_message(
                            message.chat.id, f"Error al enviar el documento: {str(e)}"
                        )
        else:
            bot.send_message(
                message.chat.id, "Aún no están disponibles estos documentos"
            )
    else:
        ruta += "Examenes/" + dic[message.chat.id]["asignatura"] + "/" + doc
        lista_exa = os.listdir(ruta)
        if len(lista_exa) != 0:
            for i in lista_exa:
                with open(ruta + "/" + f"{i}", "rb") as a:
                    try:
                        bot.send_chat_action(message.chat.id, "upload_document")
                        bot.send_document(message.chat.id, a)
                    except Exception as e:
                        bot.send_message(
                            message.chat.id, f"Error al enviar el documento: {str(e)}"
                        )
        else:
            bot.send_message(
                message.chat.id, "Aún no están disponibles estos documentos"
            )


def buttons():
    botones = ReplyKeyboardMarkup(
        input_field_placeholder="Seleccione la asignatura", resize_keyboard=True
    )
    botones.add(
        "TC1",
        "TC2",
        "TC3",
        "Mundiales",
        "Extras",
        "Ordinarios",
        "Libros",
        "Youtube",
        "Volver",
    )
    return botones


@bot.message_handler(commands=["start"])
def start(message):
    keyboard = ReplyKeyboardMarkup(
        input_field_placeholder="Seleccione la asignatura", resize_keyboard=True
    )
    keyboard.add(
        "Álgebra",
        "Lógica",
        "AM1",
        "AM2",
        "C#",
        "python",
    )
    if message.chat.id not in dic:
        dic[message.chat.id] = {}
        bot.reply_to(message, "Bienvenidos al proyecto turing", reply_markup=keyboard)
    else:
        bot.reply_to(message, "Seleccione otra asignatura", reply_markup=keyboard)


def AM1(message):
    dic[message.chat.id]["asignatura"] = "AM1"
    bot.send_message(message.chat.id, "AM1", reply_markup=buttons())


def AM2(message):
    dic[message.chat.id]["asignatura"] = "AM2"
    bot.send_message(message.chat.id, "AM2", reply_markup=buttons())


def AL(message):
    dic[message.chat.id]["asignatura"] = "AL"
    bot.send_message(
        message.chat.id, "hola bienvenido a Álgebra", reply_markup=buttons()
    )


def L(message):
    dic[message.chat.id]["asignatura"] = "L"
    bot.send_message(message.chat.id, "Lógica", reply_markup=buttons())


def ProCsharp(message):
    dic[message.chat.id]["asignatura"] = "C#"
    bot.send_message(message.chat.id, "Programación_C#", reply_markup=buttons())


def ProPython(message):
    dic[message.chat.id]["asignatura"] = "py"
    bot.send_message(message.chat.id, "Programación_python", reply_markup=buttons())


@bot.message_handler(content_types=["text"])
def text(message):
    if message.text.startswith("/"):
        bot.send_message(message.chat.id, "Comando no disponible")
    elif message.text == "AM1":
        AM1(message)
    elif message.text == "AM2":
        AM2(message)
    elif message.text == "Álgebra":
        AL(message)
    elif message.text == "Lógica":
        L(message)
    elif message.text == "C#":
        ProCsharp(message)
    elif message.text == "python":
        ProPython(message)
    elif message.text == "Volver":
        start(message)
    elif message.text == "TC1" and len(dic[message.chat.id]) != 0:
        enviar_doc("TC1", message)
    elif message.text == "TC2" and len(dic[message.chat.id]) != 0:
        enviar_doc("TC2", message)
    elif message.text == "TC3" and len(dic[message.chat.id]) != 0:
        enviar_doc("TC3", message)
    elif message.text == "Mundiales" and len(dic[message.chat.id]) != 0:
        enviar_doc("Mundiales", message)
    elif message.text == "Ordinarios" and len(dic[message.chat.id]) != 0:
        enviar_doc("Ordinarios", message)
    elif message.text == "Extras" and len(dic[message.chat.id]) != 0:
        enviar_doc("Extras", message)
    elif message.text == "Libros" and len(dic[message.chat.id]) != 0:
        enviar_doc("Libros", message)
    elif message.text == "Youtube" and len(dic[message.chat.id]) != 0:
        enviar_doc("Youtube", message)
    else:
        es_trivial = evaluar_trivialidad(message.text)
        if "True" in es_trivial:
            respuesta_amable(message.chat.id, message.text)
        else:
            respuesta_academica(message.chat.id, message.text)


if __name__ == "__main__":
    procesar_libros()
    bot.infinity_polling()
