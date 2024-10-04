# main.py
import telebot
from telebot.types import ReplyKeyboardMarkup
import streamlit as st

from data_processing import (
    procesar_libros,
    search_similar_chunks_sklearn,
    EMBEDDINGS_FILE,
    INDEX_FILE,
)
from config import TOKEN
from utils import buttons, enviar_doc, dic, update_or_send_message, escape_markdown
from ai import (
    generate_answer,
    evaluar_trivialidad,
    respuesta_amable_api,
    embed_question,
)

bot = telebot.TeleBot(TOKEN)
st.title("TEST del bot")


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


@bot.message_handler(content_types=["text"])
def text_handler(message):
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
    elif message.text == "🔙":
        start(message)
    elif message.text == "TC1" and len(dic[message.chat.id]) != 0:
        enviar_doc(bot, "TC1", message)
    elif message.text == "TC2" and len(dic[message.chat.id]) != 0:
        enviar_doc(bot, "TC2", message)
    elif message.text == "TC3" and len(dic[message.chat.id]) != 0:
        enviar_doc(bot, "TC3", message)
    elif message.text == "Mundiales" and len(dic[message.chat.id]) != 0:
        enviar_doc(bot, "Mundiales", message)
    elif message.text == "Ordinarios" and len(dic[message.chat.id]) != 0:
        enviar_doc(bot, "Ordinarios", message)
    elif message.text == "Extras" and len(dic[message.chat.id]) != 0:
        enviar_doc(bot, "Extras", message)
    elif message.text == "Libros" and len(dic[message.chat.id]) != 0:
        enviar_doc(bot, "Libros", message)
    elif message.text == "Youtube" and len(dic[message.chat.id]) != 0:
        enviar_doc(bot, "Youtube", message)
    else:
        es_trivial = evaluar_trivialidad(message.text)
        bot.send_chat_action(message.chat.id, "typing")
        if "True" in es_trivial:
            respuesta_amable(message.chat.id, message.text)
        else:
            respuesta_academica(message.chat.id, message.text)


def respuesta_academica(chat_id, question):
    if question:
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
            answer, pages, book_references = generate_answer(question, similar_chunks)
            response = f"Respuesta: {answer} \nPáginas relacionadas: {pages} \nReferencias de libros: {book_references}"
            try:
                bot.send_message(chat_id, response, parse_mode="Markdown")
            except:
                bot.send_message(chat_id, response)


def respuesta_amable(chat_id, message):
    bot.send_message(
        chat_id,
        respuesta_amable_api(message),
        parse_mode="Markdown",
    )


save_index, save_chunks = procesar_libros()

bot.infinity_polling()
