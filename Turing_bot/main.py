import os
import telebot
from telebot.types import ReplyKeyboardMarkup
from telebot.apihelper import ApiException

# Importaciones personalizadas
from config import TOKEN
from constants import ASIGNATURAS, EXAMENES, MATES, USER_DATA_FILE
from data_processing.data_processing import (
    procesar_libros,
    search_similar_chunks_sklearn,
)
from utils.utils import (
    enviar_doc,
    enviar_doc_mat,
    dic,
    buscar,
    load_data,
    save_data,
    register_handlers,
)
from ai.ai import (
    generate_answer,
    evaluar_trivialidad,
    respuesta_amable_api,
    embed_question,
)
from logger import bot_logger

# Inicializar el logger
bot_logger.info("Iniciando el bot...")

# Inicializar el bot de Telegram con el token proporcionado
bot = telebot.TeleBot(TOKEN)

register_handlers(bot)

# Cargar datos de usuarios si el archivo existe
if os.path.exists(USER_DATA_FILE):
    dic.update(load_data(USER_DATA_FILE))


@bot.message_handler(commands=["start"])
def start(message):
    """
    Maneja el comando /start. Presenta un teclado con opciones de asignaturas
    si el chat es privado. Guarda los datos del usuario.
    """
    try:
        if message.chat.type != "private":
            bot.reply_to(
                message, "El comando /start solo está disponible en el chat privado."
            )
            return

        # Crear teclado con asignaturas
        keyboard = ReplyKeyboardMarkup(
            input_field_placeholder="Seleccione la asignatura", resize_keyboard=True
        )
        keyboard.add("Álgebra", "Lógica", "AM1", "AM2", "C#", "python", "Matemática")

        # Inicializar datos del usuario si no existen
        if message.chat.id not in dic:
            dic[message.chat.id] = {}
            bot.reply_to(
                message,
                """🎉Bienvenido al Proyecto Turing🎉\n🤖 Soy tu nuevo tutor virtual, creado por los propios estudiantes y una muestra de lo que podrás hacer en poco tiempo. Mi misión es ayudarte a triunfar (sobrevivir) en las asignaturas de MATCOM. Puedes preguntarme sobre los temas que te están volviendo loco, y yo buscaré la información en los libros de texto, te explicaré paso a paso y te diré en qué página puedes leer más si quieres profundizar. ✍️\n\n⚡️ Además, iré mejorando con el tiempo: pronto podrás descargar libros📚, encontrar canales de YouTube🌐 recomendados y hasta ver películas🎬 relacionadas con la carrera.\n\nMi uso no está reconocido oficialmente por la facultad de Matemática y Computación, pero igual todos usamos ChatGPT😉 y tampoco está reconocido🤭.\n\nUsa los botones de abajo para buscar bibliografía sobre asignaturas específicas o pregúntame lo que quieras!👇""",
                reply_markup=keyboard,
            )
        else:
            bot.reply_to(
                message,
                "Seleccione otra asignatura o hágame una pregunta",
                reply_markup=keyboard,
            )

        # Guardar datos de usuarios
        save_data(USER_DATA_FILE, dic)

    except Exception as e:
        bot_logger.error(f"Error en el comando /start: {e}")
        bot.reply_to(
            message,
            "Se produjo un error al procesar el comando /start. Por favor, inténtalo de nuevo más tarde.",
        )


@bot.message_handler(commands=["turing", "Turing"])
def handle_turing(message):
    """
    Maneja el comando /turing. Responde de manera amable o académica
    según la evaluación de la pregunta.
    """
    if message.chat.type not in ["group", "supergroup"]:
        bot.reply_to(message, "Este comando solo se puede usar en grupos.")
        return

    partes = message.text.split(" ", 1)
    if len(partes) < 2:
        bot.reply_to(
            message,
            "Por favor, introduce una pregunta después del comando /turing. Ejemplo: /turing ¿Qué es un punto de acumulación?",
        )
        return

    pregunta = partes[1]
    es_trivial = evaluar_trivialidad(pregunta)
    bot.send_chat_action(message.from_user.id, "typing")

    # Determinar el tipo de respuesta basado en la trivialidad
    if "True" in es_trivial:
        respuesta_amable(message, pregunta, bot.reply_to)
    else:
        respuesta_academica(message, pregunta, bot.reply_to)


@bot.message_handler(content_types=["text"])
def text_handler(message):
    """
    Maneja todos los mensajes de texto. Dependiendo del contenido,
    responde con documentos, maneja comandos no disponibles o genera
    
    respuestas académicas/amables.
    """
    if message.chat.type != "private":
        return  # Ignorar mensajes que no sean privados

    texto = message.text.strip()
    if texto.startswith("/"):
        bot.send_message(message.chat.id, "Comando no disponible")
    elif texto in ASIGNATURAS:
        ASIGNATURAS[texto](bot, message)  # Ejecutar función asociada a la asignatura
    elif texto in EXAMENES and dic.get(message.chat.id):
        enviar_doc(bot, EXAMENES[buscar(EXAMENES, texto)], message)
    elif texto == "🔙":
        start(message)
    elif texto in MATES and texto not in EXAMENES and dic.get(message.chat.id):
        enviar_doc_mat(bot, MATES[buscar(MATES, texto)], message)
    else:
        procesar_mensaje_texto(message)

    # Guardar datos de usuarios tras procesar el mensaje
    save_data(USER_DATA_FILE, dic)


def procesar_mensaje_texto(message):
    """
    Procesa mensajes de texto que no corresponden a comandos o documentos.
    Decide si la respuesta debe ser amable o académica.
    """
    texto = message.text
    es_trivial = evaluar_trivialidad(texto)
    bot.send_chat_action(message.chat.id, "typing")

    if "True" in es_trivial:
        respuesta_amable(message.chat.id, texto, bot.send_message)
    else:
        respuesta_academica(message, texto, bot.send_message)


def respuesta_academica(message, pregunta, metodo_respuesta):
    """
    Genera una respuesta académica basada en la pregunta del usuario.
    Busca fragmentos similares y genera una respuesta detallada.
    """
    try:
        bot.send_chat_action(message.chat.id, "typing")
        pregunta_embebida = embed_question(pregunta)
        fragmentos_similares = search_similar_chunks_sklearn(
            question_embedding=pregunta_embebida,
            index_model=save_index,
            chunks=save_chunks,
        )

        if not fragmentos_similares:
            metodo_respuesta(
                message.chat.id if metodo_respuesta != bot.reply_to else message,
                "No se encontraron resultados relevantes.",
            )
            return

        respuesta, paginas, referencias_libros = generate_answer(
            pregunta, fragmentos_similares
        )

        # Formatear referencias de libros
        nombres_libros = [
            f"\n- {os.path.basename(ref).replace('_', ' ').replace('.pdf', '')}"
            for ref in referencias_libros.split(", ")
        ]
        referencias_formateadas = "\n\n".join(nombres_libros)

        respuesta_formateada = (
            f"{respuesta}\n\n"
            f"**Páginas relacionadas:** {paginas}\n\n"
            f"**Referencias de libros:** {referencias_formateadas}"
        )

        metodo_respuesta(
            message.chat.id if metodo_respuesta != bot.reply_to else message,
            respuesta_formateada,
            parse_mode="Markdown",
        )
    except Exception as e:
        # Manejar errores específicos de la API de Telegram
        error_description = str(e).lower()
        bot_logger.warning(f"APIException al generar respuesta académica: {str(e)}")

        if "can't parse entities" in error_description:
            bot_logger.warning(
                "Error de parseo de entidades Markdown. Enviando sin formato."
            )
            metodo_respuesta(
                message.chat.id if metodo_respuesta != bot.reply_to else message,
                respuesta_formateada,
            )
            return
        bot_logger.error(f"Error al generar respuesta académica: {e}")
        bot.send_message(
            message.chat.id, f"Se produjo un error: {str(e)} \n\nContacte con @HH075"
        )


def respuesta_amable(chat_id, mensaje, metodo_respuesta):
    """
    Genera una respuesta amable utilizando una API.
    """
    respuesta = respuesta_amable_api(mensaje)
    metodo_respuesta(chat_id, respuesta, parse_mode="Markdown")


# Procesar libros y generar índices al iniciar el bot
save_index, save_chunks = procesar_libros()

# Iniciar el bot y mantenerlo en ejecución
bot.infinity_polling()
