# utils.py
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup
import pickle
import re
import os

dic = {}


def buscar(lista, target):
    for i, j in enumerate(lista):
        if j == target:
            return i
    return -1


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
        boton = InlineKeyboardButton(str(i), callback_data=str(i))
        m.add(boton)
    return m


def enviar_doc_mat(bot, doc, message):
    ruta = os.path.join("Mat", doc)
    lista_mat = os.listdir(ruta)
    if len(lista_mat) != 0:
        botones_mat = crear_botones(lista_mat)
        bot.send_chat_action(message.from_user.id, "typing")
        bot.send_message(
            message.from_user.id,
            f"Conferencias y clases prácticas",
            reply_markup=botones_mat,
        )
    else:
        bot.send_chat_action(message.from_user.id, "typing")
        bot.send_message(
            message.from_user.id,
            f"No contamos con los {doc} para {dic[message.chat.id]['asignatura']}",
        )


def crear_botones_yt(yt):
    m = InlineKeyboardMarkup()
    for i in yt:
        a = i[:-1]
        a = a.split(",")
        boton = InlineKeyboardButton(str(a[0]), url=str(a[1]))
        m.add(boton)
    return m


def buscar_en_archivo(ruta, data):
    for dirpath, dirnames, filenames in os.walk(ruta):
        if data in filenames:
            return os.path.join(dirpath, data)
    return False


def download(bot, data, message):
    ruta = buscar_en_archivo("Examenes", data)
    if ruta:
        abrir = open(ruta, "rb")
        bot.send_chat_action(message.from_user.id, "upload_document")
        bot.send_document(message.from_user.id, abrir)
    else:
        ruta = buscar_en_archivo("Libros", data)
        if ruta:
            abrir = open(ruta, "rb")
            bot.send_chat_action(message.from_user.id, "upload_document")
            bot.send_document(message.from_user.id, abrir)
        else:
            ruta = buscar_en_archivo("Mat", data)
            if ruta:
                abrir = open(ruta, "rb")
                bot.send_chat_action(message.from_user.id, "upload_document")
                bot.send_document(message.from_user.id, abrir)


def enviar_doc(bot, doc, message):
    if doc == "Youtube":
        ruta = os.path.join("Examenes", dic[message.chat.id]["asignatura"], doc)
        lista = os.listdir(ruta)
        if len(lista) != 0:
            yt = open(os.path.join(ruta, "yt.txt"))
            b = crear_botones_yt(yt)
            bot.send_chat_action(message.chat.id, "typing")
            bot.send_message(
                message.chat.id,
                f"Estos son los videos {doc} de la asignatura {dic[message.chat.id]['asignatura']}",
                reply_markup=b,
            )
        else:
            bot.send_chat_action(message.chat.id, "typing")
            bot.send_message(
                message.chat.id,
                f"No contamos con videos de {doc} para {dic[message.chat.id]['asignatura']}",
            )

    else:

        ruta = (
            os.path.join("Libros", dic[message.chat.id]["asignatura"])
            if doc == "Libros"
            else os.path.join("Examenes", dic[message.chat.id]["asignatura"], doc)
        )

        lista = os.listdir(ruta)

        @bot.callback_query_handler(func=lambda call: True)
        def handle_query(call):
            download(bot, call.data, message)

        if len(lista) != 0:
            documentos = crear_botones(lista)
            bot.send_chat_action(message.chat.id, "typing")
            bot.send_message(
                message.chat.id,
                f"Estos son los {doc} de la asignatura {dic[message.chat.id]['asignatura']}",
                reply_markup=documentos,
            )

        else:
            bot.send_chat_action(message.chat.id, "typing")
            bot.send_message(
                message.chat.id,
                f"No contamos con los {doc} para {dic[message.chat.id]['asignatura']}",
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


def AM1(bot, message):
    dic[message.chat.id]["asignatura"] = "AM1"
    bot.send_message(
        message.chat.id,
        "hola, acá encontrará lo relacionado con la asignatura Análisis Matemático1",
        reply_markup=buttons(),
    )


def AM2(bot, message):
    dic[message.chat.id]["asignatura"] = "AM2"
    bot.send_message(
        message.chat.id,
        "hola, acá encontrará lo relacionado con la asignatura Análisis Matemático2",
        reply_markup=buttons(),
    )


def AL(bot, message):
    dic[message.chat.id]["asignatura"] = "AL"
    bot.send_message(
        message.chat.id,
        "hola, acá encontrará lo relacionado con la asignatura Álgebra",
        reply_markup=buttons(),
    )


def L(bot, message):
    dic[message.chat.id]["asignatura"] = "L"
    bot.send_message(
        message.chat.id,
        "hola, acá encontrará lo relacionado con la asignatura Lógica",
        reply_markup=buttons(),
    )


def ProCsharp(bot, message):
    dic[message.chat.id]["asignatura"] = "C#"
    bot.send_message(
        message.chat.id,
        "hola, acá encontrará lo relacionado con la asignatura Programación_C#",
        reply_markup=buttons(),
    )


def ProPython(bot, message):
    dic[message.chat.id]["asignatura"] = "py"
    bot.send_message(
        message.chat.id,
        "hola, acá encontrará lo relacionado con la asignatura Programación_python",
        reply_markup=buttons(),
    )


def Mate(bot, message):
    dic[message.chat.id]["asignatura"] = "Mat"
    bot.send_message(
        message.chat.id,
        "hola, acá encontrará el contenido de la carrera de matemática",
        reply_markup=buttons_mat(),
    )
