# utils.py
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup
import pickle
import re
import os

dic = {}
global docu


def buscar(lista, target):
    for i, j in enumerate(lista):
        if j == target:
            return i
    return 0


def save_data(file_path, data):
    with open(file_path, "wb") as f:
        pickle.dump(data, f)


def load_data(file_path):
    with open(file_path, "rb") as f:
        data = pickle.load(f)
    return data


def update_or_send_message(bot, chat_id, text):
    if "last_message_id" in dic.get(chat_id, {}):
        try:
            bot.edit_message_text(
                chat_id=chat_id, message_id=dic[chat_id]["last_message_id"], text=text
            )
        except:
            msg = bot.send_message(chat_id, text)
            dic[chat_id]["last_message_id"] = msg.message_id
    else:
        msg = bot.send_message(chat_id, text)
        dic.setdefault(chat_id, {})["last_message_id"] = msg.message_id


def buttons():
    botones = ReplyKeyboardMarkup(
        input_field_placeholder="Seleccione la asignatura", resize_keyboard=True
    )
    botones.add(
        KeyboardButton("TC1"),
        KeyboardButton("TC2"),
        KeyboardButton("TC3"),
        KeyboardButton("Mundiales"),
        KeyboardButton("Extras"),
        KeyboardButton("Ordinarios"),
        KeyboardButton("Libros"),
        KeyboardButton("Youtube"),
        KeyboardButton("🔙"),
    )
    return botones


def buttons_mat():
    botones = ReplyKeyboardMarkup(
        input_field_placeholder="Seleccione la asignatura", resize_keyboard=True
    )
    botones.add(
        KeyboardButton("IAM"),
        KeyboardButton("IA"),
        KeyboardButton("GA"),
        KeyboardButton("IM"),
        KeyboardButton("FVR"),
        KeyboardButton("AL"),
        KeyboardButton("Libros"),
        KeyboardButton("Youtube"),
        KeyboardButton("🔙"),
    )
    return botones


def crear_botones(lista):
    m = InlineKeyboardMarkup()
    for i in lista:
        if i != ".DS_Store":
            boton = InlineKeyboardButton(str(i), callback_data=str(i))
            m.add(boton)
    return m


def enviar_doc_mat(bot, doc, message):
    ruta = "Mat/" + doc
    lista_mat = os.listdir(ruta)
    if len(lista_mat) != 0:
        botones_mat = crear_botones(lista_mat)
        bot.send_message(
            message.chat.id,
            f"Conferencias y clases prácticas",
            reply_markup=botones_mat,
        )
    else:
        bot.send_message(message.chat.id, "No hay documentos disponibles")


def enviar_doc(bot, doc, message):

    ruta = (
        "Libros/" + dic[message.chat.id]["asignatura"]
        if doc == "Libros"
        else "Examenes/" + dic[message.chat.id]["asignatura"] + "/" + doc
    )

    lista = os.listdir(ruta)
    docu = lista

    """#### esta es la función que hay que modificar para que cuando toquen se descargue el correcto
    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        indice = buscar(docu, call.data)
        a = open(
            (
                (
                    "Libros/"
                    + dic[message.chat.id]["asignatura"]
                    + "/"
                    + str(docu[indice])
                )
                if doc == "Libros"
                else (
                    "Examenes/"
                    + dic[message.chat.id]["asignatura"]
                    + "/"
                    + doc
                    + "/"
                    + str(docu[indice])
                )
            ),
            "rb",
        )
        bot.send_chat_action(call.message.chat.id, "upload_document")
        bot.send_document(call.message.chat.id, a)"""

    if len(lista) != 0:
        documentos = crear_botones(lista)
        bot.send_message(
            message.chat.id,
            f"Estos son los {doc} de la asignatura {dic[message.chat.id]['asignatura']}",
            reply_markup=documentos,
        )
    else:
        bot.send_message(
            message.chat.id,
            f"No contamos con los {doc} solicitados para {dic[message.chat.id]['asignatura']}",
        )


def escape_markdown(text):
    """
    Escapa todos los caracteres especiales de Markdown en el texto de entrada.

    Telegram Markdown permite escapar caracteres con el símbolo de barra invertida (\).
    Esta función escapa todos los caracteres que se deben escapar según la especificación de Markdown.

    Caracteres especiales en Markdown:
    - `_`, `*`, `[`, `]`, `(`, `)`, `~`, `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.`, `!`

    Args:
        text (str): El texto de entrada que debe ser escapado.

    Returns:
        str: El texto con todos los caracteres especiales de Markdown escapados.
    """
    # Lista de caracteres especiales que deben ser escapados
    special_characters = r"([_*\[\]()~`>#+\-=|{}.!])"

    # Escapar todos los caracteres especiales con una barra invertida (\)
    return re.sub(special_characters, r"\\\1", text)
