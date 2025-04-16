# Recomendación de Rutas

Este proyecto es una aplicación web desarrollada con Flask que permite a los usuarios calcular rutas, obtener recomendaciones cercanas (como turismo, comida y panoramas) y visualizar información del clima en el destino.

## Características
- Cálculo de rutas entre dos puntos.
- Recomendaciones cercanas categorizadas (turismo, comida, panoramas).
- Información del clima en el destino.
- Gestión de usuarios (crear, eliminar, bloquear cuentas).

## Requisitos
- Python 3.11 o superior.
- Entorno virtual configurado.

## Instalación
1. Clona este repositorio:
   ```bash
   git clone https://github.com/jleiva831/recomendacionruta.git
   cd recomendacionruta
   ```

2. Crea y activa un entorno virtual:
   - En Windows:
     ```bash
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - En macOS/Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configura la base de datos:
   ```bash
   flask db upgrade
   ```

5. Ejecuta la aplicación:
   ```bash
   python app.py
   ```

## Estructura del Proyecto
```
app.py                # Archivo principal de la aplicación
creausuario.py        # Script para crear usuarios
requirements.txt      # Dependencias del proyecto
migrations/           # Archivos de migración de la base de datos
static/               # Archivos estáticos (CSS, JS)
Templates/            # Plantillas HTML
```

## Notas
- Asegúrate de configurar correctamente las claves de API en `app.py` para OpenWeatherMap y OpenRouteService.
- Si deseas incluir una base de datos de ejemplo, renombra `database.db` a `example.db` y súbela al repositorio.

## Licencia
Este proyecto está bajo la Licencia MIT.