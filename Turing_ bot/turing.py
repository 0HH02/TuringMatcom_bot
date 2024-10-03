import telebot
import os
import google.generativeai as genai


genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

model = genai.GenerativeModel(model_name="gemini-1.5-flash")


TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "bienvenidos al proyecto turing")
    bot.send_message(
        message.chat.id,
        """
    Con los siguientes comandos puede acceder a cada asignatura:\n
    /pro -> Programación\n
    /AM1 -> Análisis Matematico1\n
    /AM2 -> Análisis Matematico2\n
    /AL1 -> Álgebra\n
    /L -> Lógica
    """,
    )


@bot.message_handler(commands=["AM1"])
def AM1(message):
    examen = open("Examenes/Mundial_Álgebra.pdf", "rb")
    bot.send_document(message.chat.id, examen)


@bot.message_handler(commands=["AM2"])
def AM2(message):
    pass


@bot.message_handler(commands=["AL1"])
def AL(message):
    bot.send_message(message.chat.id, "hola bienvenido a Álgebra")


@bot.message_handler(commands=["L"])
def L(message):
    pass


@bot.message_handler(commands=["Pro"])
def Pro(message):
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
