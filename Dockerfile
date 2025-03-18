# Usa una imagen base de Python
FROM python:3.10-slim

# Configura el directorio de trabajo
WORKDIR /app

# Copia el archivo de requerimientos y lo instala
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --default-timeout=10000 --trusted-host mirrors.aliyun.com -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt


# Copia todo el código del proyecto en el contenedor
COPY . .

# Exponer el puerto si tu aplicación escucha en uno (por ejemplo, 5000)
EXPOSE 5000

# Ejecuta el script principal al iniciar el contenedor
CMD ["python", "Turing_bot/main.py"]
