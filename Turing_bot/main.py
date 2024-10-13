import telebot
from telebot.types import ReplyKeyboardMarkup
import os

from data_processing import (
    procesar_libros,
    search_similar_chunks_sklearn,
    EMBEDDINGS_FILE,
    INDEX_FILE,
)
from config import TOKEN
from utils import (
    enviar_doc,
    enviar_doc_mat,
    dic,
    update_or_send_message,
    escape_markdown,
    buscar,
    load_data,
    save_data,
    AM1,
    AM2,
    AL,
    L,
    ProCsharp,
    ProPython,
    Mate,
)
from ai import (
    generate_answer,
    evaluar_trivialidad,
    respuesta_amable_api,
    embed_question,
)

bot = telebot.TeleBot(TOKEN)
USER_DATA_FILE = "user_data.pkl"

# Cargar los datos de los usuarios al iniciar el bot
# if os.path.exists(USER_DATA_FILE):
#   dic.update(load_data(USER_DATA_FILE))


@bot.message_handler(commands=["start"])
def start(message):
    if message.chat.type == "private":
        # Crear el teclado solo para el chat privado
        keyboard = ReplyKeyboardMarkup(
            input_field_placeholder="Seleccione la asignatura", resize_keyboard=True
        )
        keyboard.add("Álgebra", "Lógica", "AM1", "AM2", "C#", "python", "Matemática")
        if message.chat.id not in dic:
            dic[message.chat.id] = {}
            bot.reply_to(
                message,
                """ """,
                reply_markup=keyboard,
            )
            # Guardar los datos de los usuarios cada vez que se ejecuta el comando /start
        # save_data(USER_DATA_FILE, dic)
        else:
            bot.reply_to(
                message,
                "Seleccione otra asignatura o hágame una pregunta",
                reply_markup=keyboard,
            )

    else:
        bot.reply_to(
            message, "El comando /start solo está disponible en el chat privado."
        )


@bot.message_handler(commands=["turing", "Turing"])
def handle_turing(message):
    # Si el comando se usa en un grupo
    if message.chat.type in ["group", "supergroup"]:
        # Extraer el texto después del comando /turing
        # El formato esperado es /turing <mensaje>
        if len(message.text.split()) > 1:
            # Eliminar el comando y dejar solo el mensaje como argumento
            pregunta = message.text.split(" ", 1)[1]
            # Evaluar la pregunta para decidir el tipo de respuesta
            es_trivial = evaluar_trivialidad(pregunta)
            bot.send_chat_action(message.from_user.id, "typing")
            if "True" in es_trivial:
                respuesta_amable(message, pregunta, bot.reply_to)
            else:
                respuesta_academica(message, pregunta, bot.reply_to)
        else:
            bot.reply_to(
                message,
                "Por favor, introduce una pregunta después del comando /turing. Ejemplo: /turing ¿Qué es un punto de acumulación?",
            )
    else:
        bot.reply_to(message, "Este comando solo se puede usar en grupos.")


_reservadas = {
    "AM1": AM1,
    "AM2": AM2,
    "Álgebra": AL,
    "Lógica": L,
    "C#": ProCsharp,
    "python": ProPython,
    "Matemática": Mate,
}
_examen = [
    "TC1",
    "TC2",
    "TC3",
    "Mundiales",
    "Ordinarios",
    "Extras",
    "Libros",
    "Youtube",
]
_mates = ["IAM", "IA", "GA", "IM", "FVR", "AL"]


@bot.message_handler(content_types=["text"])
def text_handler(message):
    # Verificar si el bot está en un grupo

    print(message.text)
    if message.chat.type == "private":
        # Comportamiento estándar en chat privado
        if message.text.startswith("/"):
            bot.send_message(message.chat.id, "Comando no disponible")
        elif message.text in _reservadas.keys():
            _reservadas[message.text](bot, message)
        elif message.text == "🔙":
            start(message)
        elif message.text in _examen and len(dic[message.chat.id]) != 0:
            indice = buscar(_examen, message.text)
            enviar_doc(bot, _examen[indice], message)
        elif (
            message.text in _mates
            and not (message.text in _examen)
            and len(dic[message.chat.id]) != 0
        ):
            indice = buscar(_mates, message.text)
            enviar_doc_mat(bot, _mates[indice], message)
        else:
            es_trivial = evaluar_trivialidad(message.text)
            bot.send_chat_action(message.chat.id, "typing")
            if "True" in es_trivial:
                respuesta_amable(message.chat.id, message.text, bot.send_message)
            else:
                respuesta_academica(message, message.text, bot.send_message)

        # Guardar el inicio de seccion para que no tenga que siempre empezar con start, cada vez que se maneja un mensaje de texto
        # save_data(USER_DATA_FILE, dic)


def respuesta_academica(message, question, answer_form):
    if question:
        try:
            update_or_send_message(
                bot, message.chat.id, "Buscando respuesta a la pregunta..."
            )
            question_embedding = embed_question(question)
            update_or_send_message(
                bot, message.chat.id, "Buscando fragmentos similares..."
            )
            bot.send_chat_action(message.chat.id, "typing")
            similar_chunks = search_similar_chunks_sklearn(
                question_embedding=question_embedding,
                index_model=save_index,
                chunks=save_chunks,
            )
            if not similar_chunks:
                update_or_send_message(
                    bot,
                    message.from_user.id,
                    "No se encontraron resultados relevantes.",
                )
            else:
                answer, pages, book_references = generate_answer(
                    question, similar_chunks
                )
                # Extraer los nombres de los libros y separarlos por puntos en markdown
                book_names = [
                    "\n- " + os.path.basename(ref).replace("_", " ").replace(".pdf", "")
                    for ref in book_references.split(", ")
                ]
                book_references_formatted = "\n\n".join(book_names)
                response = (
                    f"{answer}\n\n"
                    f"**Páginas relacionadas:** {pages}\n\n"
                    f"**Referencias de libros:** {book_references_formatted}"
                )
                try:
                    if answer_form == bot.reply_to:
                        answer_form(message, response, parse_mode="Markdown")
                    else:
                        answer_form(message.chat.id, response, parse_mode="Markdown")

                except Exception as e:
                    print(book_references_formatted)
                    if answer_form == bot.reply_to:
                        answer_form(message, response)
                    else:
                        answer_form(message.chat.id, response)

        except Exception as e:
            bot.send_message(message.chat.id, f"Se produjo un error: {str(e)}")


def respuesta_amable(chat_id, message, answer_form):
    answer_form(
        chat_id,
        respuesta_amable_api(message),
        parse_mode="Markdown",
    )


save_index, save_chunks = procesar_libros()

# Iniciar el bot
bot.infinity_polling()
