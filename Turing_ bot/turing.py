import telebot
import os
import google.generativeai as genai
from telebot.types import ReplyKeyboardMarkup


genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel(model_name="gemini-1.5-flash")
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)


def enviar_doc(asignatura, doc_pedido):
    pass


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
    keyboard = ReplyKeyboardMarkup(
        input_field_placeholder="Selecione la asignatura", resize_keyboard=True
    )
    keyboard.add(
        "/Álgebra",
        "/Lógica",
        "/AM1",
        "/AM2",
        "/C#",
        "/python",
    )
    bot.reply_to(message, "bienvenidos al proyecto turing", reply_markup=keyboard)


@bot.message_handler(commands=["AM1"])
def AM1(message):
    bot.send_message(message.chat.id, "AM1", reply_markup=buttons())


@bot.message_handler(commands=["AM2"])
def AM2(message):
    bot.send_message(message.chat.id, "AM2", reply_markup=buttons())


@bot.message_handler(commands=["Álgebra"])
def AL(message):
    bot.send_message(
        message.chat.id, "hola bienvenido a Álgebra", reply_markup=buttons()
    )


@bot.message_handler(commands=["Lógica"])
def L(message):
    bot.send_message(message.chat.id, "Lógica", reply_markup=buttons())


@bot.message_handler(commands=["C#"])
def ProCsharp(message):
    bot.send_message(message.chat.id, "Programación_C#", reply_markup=buttons())


@bot.message_handler(commands=["python"])
def ProPython(message):
    bot.send_message(message.chat.id, "Programación_python", reply_markup=buttons())


@bot.message_handler(content_types=["text"])
def text(message):

    if message.text.startswith("/"):
        bot.send_message(message.chat.id, "Comando no disponible")

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
