import telebot
import os
import google.generativeai as genai
from telebot.types import ReplyKeyboardMarkup


genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel(model_name="gemini-1.5-flash")
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
dic = {}


def enviar_doc(doc, message):
    ruta = ""
    if doc == "Libros":
        ruta += "Libros/" + dic[message.chat.id]["asignatura"]
        lista_lib = os.listdir(ruta)
        for i in lista_lib:
            a = open(ruta + "/" + f"{i}", "rb")
            bot.send_chat_action(message.chat.id, "upload_document")
            bot.send_document(message.chat.id, a)
    else:
        ruta += "Examenes/" + dic[message.chat.id]["asignatura"] + doc
        lista_exa = os.listdir(ruta)


def buttons():
    botones = ReplyKeyboardMarkup(
        input_field_placeholder="Selecione la asignatura", resize_keyboard=True
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
    dic[message.chat.id] = {}
    keyboard = ReplyKeyboardMarkup(
        input_field_placeholder="Selecione la asignatura", resize_keyboard=True
    )
    keyboard.add(
        "Álgebra",
        "Lógica",
        "AM1",
        "AM2",
        "C#",
        "python",
    )
    bot.reply_to(message, "bienvenidos al proyecto turing", reply_markup=keyboard)


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
        del dic[message.chat.id]
        start(message)
    elif message.text == "TC1" and len(dic[message.chat.id]) != 0:
        enviar_doc("TC1", message)
    elif message.text == "TC2" and len(dic[message.chat.id]) != 0:
        enviar_doc("TC2", message)
    elif message.text == "TC3" and len(dic[message.chat.id]) != 0:
        enviar_doc("TC3", message)
    elif message.text == "Mundiales" and len(dic[message.chat.id]) != 0:
        enviar_doc("Mundiales", message)
    elif message.text == "Extras" and len(dic[message.chat.id]) != 0:
        enviar_doc("Extras", message)
    elif message.text == "Libros" and len(dic[message.chat.id]) != 0:
        enviar_doc("Libros", message)
    elif message.text == "Youtube" and len(dic[message.chat.id]) != 0:
        enviar_doc("Youtube", message)
    else:
        response = model.generate_content(
            message.text,
            generation_config=genai.GenerationConfig(
                max_output_tokens=1000,
                temperature=0.1,
            ),
        )
        bot.send_chat_action(message.chat.id, "typing")
        bot.send_message(message.chat.id, response.text)


if __name__ == "__main__":
    bot.infinity_polling()
