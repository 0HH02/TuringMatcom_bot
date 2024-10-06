# main.py
import telebot
from telebot.types import ReplyKeyboardMarkup
import os

from data_processing import (
    procesar_libros,
    search_similar_chunks_sklearn,
    EMBEDDINGS_FILE,
    INDEX_FILE,
)
from config import TOKEN
from utils import (
    buttons,
    buttons_mat,
    enviar_doc,
    dic,
    update_or_send_message,
    escape_markdown,
    buscar,
)
from ai import (
    generate_answer,
    evaluar_trivialidad,
    respuesta_amable_api,
    embed_question,
)

bot = telebot.TeleBot(TOKEN, parse_mode="markdown")


@bot.message_handler(commands=["start"])
def start(message):
    keyboard = ReplyKeyboardMarkup(
        input_field_placeholder="Seleccione la asignatura", resize_keyboard=True
    )
    keyboard.add("Álgebra", "Lógica", "AM1", "AM2", "C#", "python", "Matemática")
    if message.chat.id not in dic:
        dic[message.chat.id] = {}
        bot.reply_to(
            message,
            """🎉Bienvenido al Proyecto Turing🎉 
🤖 Soy tu nuevo tutor virtual, creado por los propios estudiantes y una muestra de lo que podrás hacer en poco tiempo. Mi misión es ayudarte a sobrevivir (y triunfar) en las asignaturas de MATCOM. Puedes preguntarme sobre los temas que te están volviendo loco, y yo buscaré la información en los libros de texto, te explicaré paso a paso y te diré en qué página puedes leer más si quieres profundizar. ✍️

⚡️ Además, iré mejorando con el tiempo: pronto podrás descargar libros📚, encontrar canales de YouTube🌐 recomendados y hasta ver películas🎬 relacionadas con la carrera.

Usa los botones de abajo para buscar bibliografía sobre asignaturas específicas o pregúntame lo que quieras!👇""",
            reply_markup=keyboard,
        )
    else:
        bot.reply_to(
            message,
            "Seleccione otra asignatura o hágame una pregunta",
            reply_markup=keyboard,
        )


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


def Mate(message):
    dic[message.chat.id]["asignatura"] = "Mat"
    bot.send_message(message.chat.id, "matemática", reply_markup=buttons_mat())


_reservadas = {
    "AM1": AM1,
    "AM2": AM2,
    "Álgebra": AL,
    "Lógica": L,
    "C#": ProCsharp,
    "python": ProPython,
    "Matemática": Mate,
    "🔙": start,
}
_examen = [
    "TC1",
    "TC2",
    "TC3",
    "Mundiales",
    "Ordinarios",
    "Extras",
    "Libros",
    "Youtube",
]
_mates = ["IAM", "IA", "GA", "IM", "FVR", "AL", "Libros", "Youtube", "🔙"]


@bot.message_handler(content_types=["text"])
def text_handler(message):
    if message.text.startswith("/"):
        bot.send_message(message.chat.id, "Comando no disponible")
    if message.text in _reservadas.keys():
        _reservadas[message.text](message)

    elif message.text in _examen and len(dic[message.chat.id]) != 0:
        indice = buscar(_examen, message.text)
        enviar_doc(bot, _examen[indice], message)
    elif (
        message.text in _mates
        and not (message.text in _examen)
        and len(dic[message.chat.id]) != 0
    ):
        indice = buscar(_mates, message.text)
        enviar_doc_mat(bot, _mates[indice], message)
    else:
        es_trivial = evaluar_trivialidad(message.text)
        bot.send_chat_action(message.chat.id, "typing")
        if "True" in es_trivial:
            respuesta_amable(message.chat.id, message.text)
        else:
            respuesta_academica(message.chat.id, message.text)


def respuesta_academica(chat_id, question):
    if question:
        try:
            update_or_send_message(bot, chat_id, "Buscando respuesta a la pregunta...")
            question_embedding = embed_question(question)
            update_or_send_message(bot, chat_id, "Buscando fragmentos similares...")
            bot.send_chat_action(chat_id, "typing")
            similar_chunks = search_similar_chunks_sklearn(
                question_embedding=question_embedding,
                index_model=save_index,
                chunks=save_chunks,
            )
            if not similar_chunks:
                update_or_send_message(
                    bot, chat_id, "No se encontraron resultados relevantes."
                )
            else:
                answer, pages, book_references = generate_answer(
                    question, similar_chunks
                )
                # Extraer los nombres de los libros y separarlos por puntos en markdown
                book_names = [
                    "\n- " + os.path.basename(ref).replace("_", " ").replace(".pdf", "")
                    for ref in book_references.split(", ")
                ]
                book_references_formatted = ". ".join(book_names)
                response = f"{answer} \nPáginas relacionadas: {pages} \n\nReferencias de libros: {book_references_formatted}"
                try:
                    bot.send_message(chat_id, response, parse_mode="Markdown")
                except Exception as e:
                    print(book_references_formatted)
                    bot.send_message(chat_id, response)

        except Exception as e:
            bot.send_message(chat_id, f"Se produjo un error: {str(e)}")


def respuesta_amable(chat_id, message):
    bot.send_message(
        chat_id,
        respuesta_amable_api(message),
        parse_mode="Markdown",
    )


save_index, save_chunks = procesar_libros()

bot.infinity_polling()
