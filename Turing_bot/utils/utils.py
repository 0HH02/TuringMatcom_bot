# utils.py
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup
import pickle
import os
import json

from logger import bot_logger

dic = {}


def buscar(lista, target):
    """
    Busca el índice de 'target' en 'lista'.

    Args:
        lista (List[str]): Lista donde buscar.
        target (str): Elemento a buscar.

    Returns:
        int: Índice del elemento o -1 si no se encuentra.
    """
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


def crear_botones_yt(ruta_archivo):
    m = InlineKeyboardMarkup()
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        for item in datos:
            nombre = item.get("nombre")
            url = item.get("link")
            if not nombre or not url:
                print(f"Objeto incompleto: {item}")
                continue
            if not (url.startswith("http://") or url.startswith("https://")):
                print(f"URL inválida en el objeto: {item}")
                continue
            boton = InlineKeyboardButton(nombre, url=url)
            m.add(boton)
    except FileNotFoundError:
        print(f"El archivo {ruta_archivo} no se encontró.")
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    return m


def buscar_en_archivo(ruta, data):
    for dirpath, dirnames, filenames in os.walk(ruta):
        if data in filenames:
            return os.path.join(dirpath, data)
    return False


def download(bot, data: str, message):
    user_id = message.chat.id
    rutas = ["Examenes", "Libros", "Mat"]
    for carpeta in rutas:
        ruta = buscar_en_archivo(carpeta, data)
        if ruta:
            try:
                with open(ruta, "rb") as abrir:
                    bot.send_chat_action(user_id, "upload_document")
                    bot.send_document(user_id, abrir)
                return
            except Exception as e:
                bot_logger.error(f"Error al enviar documento {ruta}: {e}")
                bot.send_message(
                    message.chat.id, "Error al enviar el documento solicitado."
                )
    bot.send_message(message.chat.id, "Documento no encontrado.")


def enviar_doc(bot, doc, message):

    if doc == "Youtube":
        ruta = os.path.join("Examenes", dic[message.chat.id]["asignatura"], doc)
        print(ruta)
        lista = os.listdir(ruta)
        if len(lista) != 0:
            b = crear_botones_yt(os.path.join(ruta, "yt.json"))
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
        print(os.listdir(ruta))
        try:
            lista = os.listdir(ruta)

            print(len(lista))
            if len(lista) != 0:
                documentos = crear_botones(lista)
                bot.send_chat_action(message.chat.id, "typing")
                bot.send_message(
                    message.chat.id,
                    f"Estos son los {doc} de la asignatura {dic[message.chat.id]['asignatura']}",
                    reply_markup=documentos,
                )
        except Exception as e:
            bot.send_chat_action(message.chat.id, "typing")
            bot.send_message(
                message.chat.id,
                f"Aún no contamos con los {doc} para {dic[message.chat.id]['asignatura']}",
            )


def set_asignatura(bot, message, asignatura, descripcion, botones_func):
    dic[message.chat.id]["asignatura"] = asignatura
    bot.send_message(
        message.chat.id,
        descripcion,
        reply_markup=botones_func(),
    )


def AM1(bot, message):
    set_asignatura(
        bot,
        message,
        "AM1",
        "Hola, acá encontrará lo relacionado con la asignatura Análisis Matemático1",
        buttons,
    )


def AM2(bot, message):
    set_asignatura(
        bot,
        message,
        "AM2",
        "Hola, acá encontrará lo relacionado con la asignatura Análisis Matemático2",
        buttons,
    )


def AL(bot, message):
    set_asignatura(
        bot,
        message,
        "AL",
        "Hola, acá encontrará lo relacionado con la asignatura Álgebra",
        buttons,
    )


def L(bot, message):
    set_asignatura(
        bot,
        message,
        "L",
        "Hola, acá encontrará lo relacionado con la asignatura Lógica",
        buttons,
    )


def ProCsharp(bot, message):
    set_asignatura(
        bot,
        message,
        "C#",
        "Hola, acá encontrará contenido de C#",
        buttons,
    )


def ProPython(bot, message):
    set_asignatura(
        bot,
        message,
        "py",
        "Hola, acá encontrará contenido de Python",
        buttons,
    )


def Mate(bot, message):
    set_asignatura(
        bot,
        message,
        "Mat",
        "Hola, acá encontrará lo relacionado con la asignatura Matemática",
        buttons_mat,
    )


def handle_query(call, bot):
    data = call.data
    # Puedes usar call.message si necesitas información del mensaje original
    download(bot, data, call.message)


def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        handle_query(call, bot)
