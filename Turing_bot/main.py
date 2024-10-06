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
    buttons,
    buttons_mat,
    enviar_doc,
    enviar_doc_mat,
    dic,
    update_or_send_message,
    escape_markdown,
    buscar,
    load_data,
    save_data,
)
from ai import (
    generate_answer,
    evaluar_trivialidad,
    respuesta_amable_api,
    embed_question,
)

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
USER_DATA_FILE = "user_data.pkl"

# Cargar los datos de los usuarios al iniciar el bot
if os.path.exists(USER_DATA_FILE):
    dic.update(load_data(USER_DATA_FILE))


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
                """🎉Bienvenido al Proyecto Turing🎉 
🤖 Soy tu nuevo tutor virtual, creado por los propios estudiantes y una muestra de lo que podrás hacer en poco tiempo. Mi misión es ayudarte a sobrevivir (y triunfar) en las asignaturas de MATCOM. Puedes preguntarme sobre los temas que te están volviendo loco, y yo buscaré la información en los libros de texto, te explicaré paso a paso y te diré en qué página puedes leer más si quieres profundizar. ✍️

⚡️ Además, iré mejorando con el tiempo: pronto podrás descargar libros📚, encontrar canales de YouTube🌐 recomendados y hasta ver películas🎬 relacionadas con la carrera.

Usa los botones de abajo para buscar bibliografía sobre asignaturas específicas o pregúntame lo que quieras!👇""",
                reply_markup=keyboard,
            )
        else:
            bot.reply_to(
                message,
                "Seleccione otra asignatura o hágame una pregunta",
                reply_markup=keyboard,
            )

        # Guardar los datos de los usuarios cada vez que se ejecuta el comando /start
        save_data(USER_DATA_FILE, dic)
    else:
        bot.reply_to(
            message, "El comando /start solo está disponible en el chat privado."
        )


@bot.message_handler(commands=["turing"])
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
            bot.send_chat_action(message.chat.id, "typing")
            if "True" in es_trivial:
                respuesta_amable(message.chat.id, pregunta)
            else:
                respuesta_academica(message.chat.id, pregunta)
        else:
            bot.reply_to(
                message,
                "Por favor, introduce una pregunta después del comando /turing. Ejemplo: /turing ¿Qué es un punto de acumulación?",
            )
    else:
        bot.reply_to(message, "Este comando solo se puede usar en grupos.")


@bot.message_handler(content_types=["text"])
def text_handler(message):
    # Verificar si el bot está en un grupo
    if message.chat.type == "private":
        # Comportamiento estándar en chat privado
        if message.text.startswith("/"):
            bot.send_message(message.chat.id, "Comando no disponible")
        elif message.text in _reservadas.keys():
            _reservadas[message.text](message)
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
                respuesta_amable(message.chat.id, message.text)
            else:
                respuesta_academica(message.chat.id, message.text)

        # Guardar los datos de los usuarios cada vez que se maneja un mensaje de texto
        save_data(USER_DATA_FILE, dic)


def respuesta_academica(chat_id, question):
    if question:
        try:
            update_or_send_message(bot, chat_id, "Buscando respuesta a la pregunta...")
            question_embedding = embed_question(question)
            update_or_send_message(bot, chat_id, "Buscando fragmentos similares...")
            bot.send_chat_action(chat_id, "typing")
            similar_chunks = search_similar_chunks_sklearn(
                question_embedding=question_embedding,
                index_model=save_index,
                chunks=save_chunks,
            )
            if not similar_chunks:
                update_or_send_message(
                    bot, chat_id, "No se encontraron resultados relevantes."
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
                    bot.send_message(chat_id, response, parse_mode="Markdown")
                except Exception as e:
                    print(book_references_formatted)
                    bot.send_message(chat_id, response)

        except Exception as e:
            bot.send_message(chat_id, f"Se produjo un error: {str(e)}")


def respuesta_amable(chat_id, message):
    bot.send_message(
        chat_id,
        respuesta_amable_api(message),
        parse_mode="Markdown",
    )


# Iniciar el bot
bot.infinity_polling()
