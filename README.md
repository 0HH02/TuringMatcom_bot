# TuringMatcom_bot

Este es un proyecto OpenSource para los estudiantes de la facultad de Matemática y Computación de la Universidad de La Habana con la idea de utilizar las últimas herramientas de IA para elevar la calidad de la educación.

## Cómo correr el bot?:
python Turing_bot/main.py

## Cómo añadir contenido?:

- Añadir canales de Youtube para cada asignatura. Para eso dirigirse a la carpeta de Youtube dentro de la carpeta Exámenes y añadir el nombre del canal y el link en el json siguiendo el mismo formato que tiene.

- Añadir más libros y exámenes de cada asignatura. Para añadir libros deben entrar en la carpeta Libros, añadir el libro dentro de la asignatura correspondiente, el libro debe estar en formato PDF y el nombre del archivo debe ser el mismo que el título del libro. Para añadir exámenes debe repetir el mismo proceso pero entrando en la carpeta de Exámenes.


## Por implementar:

- Peliculas de la carrera de Matemática, Ciencias de la Computación y Ciencia de Datos. Todavía falta implementar la lógica.

- Hacer un resumen de cada libro para que los usuarios puedan preguntar qué libros deben leer si quieren aprender alguna nueva habilidad.

- Hacer un etiquetado de los ejercicios de cada examen para que los usuarios puedan preguntar qué ejercicios deben hacer si quieren aprender alguna nueva habilidad.

- Hacer un resumen de los canales de cada asignatura para que los usuarios puedan preguntar qué videos deben ver si quieren aprender alguna nueva habilidad.

- Si no encuentra contenido relevante en el contexto de la conversación debe decir que no encontró información relevante así que va a dar una respuesta más general y no tan específica(No debe mostrar el contexto).

## Estadísticas a implementar:
- Asignaturas por las cuales se utiliza el bot.
- Horarios en los que se usa.
- Número de usuarios.
- Número de mensajes recibidos.
- Número de mensajes enviados por usuario.

## No se deben guardar mensajes ni datos personales que puedan comprometer la privacidad de los usuarios.