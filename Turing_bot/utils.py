# utils.py
from telebot.types import ReplyKeyboardMarkup
import pickle
import re
import os

dic = {}


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
        "TC1",
        "TC2",
        "TC3",
        "Mundiales",
        "Extras",
        "Ordinarios",
        "Libros",
        "Youtube",
        "🔙",
    )
    return botones


def enviar_doc(bot, doc, message):
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
