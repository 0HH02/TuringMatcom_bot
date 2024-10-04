# bot_handlers.py
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup

from config import TOKEN
from utils import buttons, enviar_doc, dic, update_or_send_message
from ai import generate_answer, evaluar_trivialidad, respuesta_amable_api
from data_processing import search_similar_chunks_sklearn

bot = TeleBot(TOKEN)

# Definir otras variables globales si es necesario
save_index = None
save_chunks = []
EMBEDDINGS_FILE = "embeddings_data.pkl"
INDEX_FILE = "vector_index.pkl"


@bot.message_handler(commands=["start"])
def start(message):
    keyboard = ReplyKeyboardMarkup(
        input_field_placeholder="Seleccione la asignatura", resize_keyboard=True
    )
    keyboard.add("Álgebra", "Lógica", "AM1", "AM2", "C#", "python")
    if message.chat.id not in dic:
        dic[message.chat.id] = {}
        bot.reply_to(message, "Bienvenidos al proyecto turing", reply_markup=keyboard)
    else:
        bot.reply_to(message, "Seleccione otra asignatura", reply_markup=keyboard)


@bot.message_handler(content_types=["text"])
def text_handler(message):
    if message.text.startswith("/"):
        bot.send_message(message.chat.id, "Comando no disponible")
    elif message.text in ["AM1", "AM2", "Álgebra", "Lógica", "C#", "python", "Volver"]:
        asignaturas = {
            "AM1": "AM1",
            "AM2": "AM2",
            "Álgebra": "AL",
            "Lógica": "L",
            "C#": "C#",
            "python": "py",
        }
        if message.text == "Volver":
            start(message)
        else:
            asignatura = asignaturas.get(message.text)
            dic[message.chat.id]["asignatura"] = asignatura
            bot.send_message(
                message.chat.id,
                message.text if message.text != "AL" else "hola bienvenido a Álgebra",
                reply_markup=buttons(),
            )
    elif message.text in [
        "TC1",
        "TC2",
        "TC3",
        "Mundiales",
        "Ordinarios",
        "Extras",
        "Libros",
        "Youtube",
    ]:
        if "asignatura" in dic.get(message.chat.id, {}):
            enviar_doc(
                bot, message.chat.id, message.text, dic[message.chat.id]["asignatura"]
            )
        else:
            bot.send_message(
                message.chat.id, "Por favor, selecciona una asignatura primero."
            )
    else:
        es_trivial = evaluar_trivialidad(message.text)
        if "True" in es_trivial:
            respuesta_amable(message.chat.id, message.text)
        else:
            respuesta_academica(message.chat.id, message.text)


def respuesta_academica(chat_id, question):
    similar_chunks = search_similar_chunks_sklearn(
        question_embedding=[],  # Debes pasar el embedding real aquí
        index_model=None,  # Debes pasar el modelo real aquí
        chunks=[],  # Debes pasar los chunks reales aquí
    )
    if not similar_chunks:
        update_or_send_message(bot, chat_id, "No se encontraron resultados relevantes.")
        return "No se encontraron resultados relevantes."
    else:
        answer, pages, book_references = generate_answer(question, similar_chunks)
        response = f"Respuesta: {answer} \nPáginas relacionadas: {pages} \nReferencias de libros: {book_references}"
        update_or_send_message(bot, chat_id, response)


def respuesta_amable(chat_id, message):
    bot.send_message(
        chat_id,
        message,
        parse_mode="Markdown",
    )


# Otros manejadores y funciones específicas pueden ser añadidos aquí
