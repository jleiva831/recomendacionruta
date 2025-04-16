# Usar una imagen base oficial de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar los archivos necesarios al contenedor
COPY requirements.txt requirements.txt
COPY . .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto en el que se ejecutará la aplicación
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]