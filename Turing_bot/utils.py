# utils.py
from telebot.types import ReplyKeyboardMarkup
import pickle

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
        "Volver",
    )
    return botones


def enviar_doc(bot, chat_id, doc, asignatura):
    try:
        if doc == "Libros":
            ruta = f"Libros/{asignatura}"
        else:
            ruta = f"Examenes/{asignatura}/{doc}"
        lista_archivos = os.listdir(ruta)
        if lista_archivos:
            for archivo in lista_archivos:
                with open(os.path.join(ruta, archivo), "rb") as a:
                    bot.send_chat_action(chat_id, "upload_document")
                    bot.send_document(chat_id, a)
        else:
            bot.send_message(chat_id, "Aún no están disponibles estos documentos")
    except Exception as e:
        bot.send_message(chat_id, f"Error al enviar el documento: {str(e)}")
