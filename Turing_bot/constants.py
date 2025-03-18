# constants.py

from utils.utils import AM1, AM2, AL, L, ProCsharp, ProPython, Mate

ASIGNATURAS = {
    "Álgebra": AL,
    "Lógica": L,
    "AM1": AM1,
    "AM2": AM2,
    "C#": ProCsharp,
    "python": ProPython,
    "Matemática": Mate,
}

EXAMENES = [
    "TC1",
    "TC2",
    "TC3",
    "Mundiales",
    "Ordinarios",
    "Extras",
    "Libros",
    "Youtube",
]
MATES = ["IAM", "IA", "GA", "IM", "FVR", "AL"]

USER_DATA_FILE = "user_data.pkl"
EMBEDDINGS_FILE = "embeddings_data.pkl"
INDEX_FILE = "vector_index.pkl"
LIBROS_FOLDER = "Libros"
