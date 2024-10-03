import telebot
import os
import google.generativeai as genai
from telebot.types import ReplyKeyboardMarkup

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel(model_name="gemini-1.5-flash")
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def start(message):
    keyboard = ReplyKeyboardMarkup(
        input_field_placeholder="Selecione la asignatura", resize_keyboard=True
    )
    keyboard.add(
        "/Álgebra",
        "/Lógica",
        "/Análisis Matemático 1",
        "/Análisis Matematico 2",
        "/Programación C#",
        "/Programación Python",
    )
    bot.reply_to(message, "bienvenidos al proyecto turing", reply_markup=keyboard)


@bot.message_handler(commands=["Análisis Matemático 1"])
def AM1(message):
    keyboard_AM1 = ReplyKeyboardMarkup(
        input_field_placeholder="Análisis Matemático 1", resize_keyboard=True
    )
    keyboard_AM1.add("libros")


@bot.message_handler(commands=["Análisis Matemático 2"])
def AM2(message):
    pass


@bot.message_handler(commands=["Álgebra"])
def AL(message):
    bot.send_message(message.chat.id, "hola bienvenido a Álgebra")


@bot.message_handler(commands=["Lógica"])
def L(message):
    pass


@bot.message_handler(commands=["Programación C#"])
def ProCsharp(message):
    pass


@bot.message_handler(commands=["Programación Python"])
def ProPython(message):
    pass


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
