from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import os
import openrouteservice
from geopy.distance import geodesic
import requests
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
app.secret_key = "clave_secreta"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "database.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

bcrypt = Bcrypt(app)

# Reemplazar las claves de OpenWeatherMap y OpenRouteService con variables de entorno
ORS_API_KEY = os.getenv("ORS_API_KEY")  # Asegúrate de definir esta variable en tu archivo .env
OWM_API_KEY = os.getenv("OWM_API_KEY")  # Asegúrate de definir esta variable en tu archivo .env
client = openrouteservice.Client(key=ORS_API_KEY)

# Inicializar Flask-Migrate
migrate = Migrate(app, db)

# Modelo de usuario
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Campo para roles
    is_active = db.Column(db.Boolean, default=True)  # Estado de la cuenta (activa o bloqueada)

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Relación con el usuario
    origen = db.Column(db.String(150), nullable=False)
    destino = db.Column(db.String(150), nullable=False)
    distancia_total = db.Column(db.Float, nullable=False)  # Distancia total en km
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())  # Fecha de creación
    checkpoints = db.relationship('Checkpoint', backref='route', lazy=True)  # Relación con los checkpoints


class Checkpoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)  # Relación con la ruta
    lat = db.Column(db.Float, nullable=False)  # Latitud
    lon = db.Column(db.Float, nullable=False)  # Longitud
    kilometro = db.Column(db.Float, nullable=False)  # Distancia acumulada en km
    tiempo_estimado = db.Column(db.Float, nullable=False)  # Tiempo estimado en horas

# Cargar usuario
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def obtener_clima(lat, lon):
    """Obtiene el clima actual para las coordenadas dadas."""
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric&lang=es"
    try:
        response = requests.get(url)
        print(f"URL de la solicitud: {url}")  # Agregar para depuración
        if response.status_code == 200:
            data = response.json()
            return {
                "temperatura": data["main"]["temp"],
                "descripcion": data["weather"][0]["description"],
                "icono": data["weather"][0]["icon"]
            }
        elif response.status_code == 401:
            print("Error 401: Clave de API inválida o desactivada.")
            return {"error": "Clave de API inválida o desactivada."}
        else:
            print(f"Error en la API: {response.status_code}, {response.text}")
            return {"error": f"Error en la API: {response.status_code}"}
    except Exception as e:
        print(f"Excepción al obtener el clima: {e}")
        return {"error": str(e)}

def obtener_pois(lat, lon, categoria="restaurant", radio=1000):
    """Obtiene puntos de interés cercanos a las coordenadas dadas usando OpenStreetMap Nominatim."""
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={categoria}&lat={lat}&lon={lon}&radius={radio}"
    try:
        response = requests.get(url, headers={"User-Agent": "GPStest/1.0"})
        if response.status_code == 200:
            data = response.json()
            pois = []
            for poi in data:
                pois.append({
                    "nombre": poi.get("display_name", "Sin nombre"),
                    "lat": float(poi["lat"]),
                    "lon": float(poi["lon"])
                })
            return pois
        else:
            print(f"Error al obtener POIs: {response.status_code}, {response.text}")
            return []
    except Exception as e:
        print(f"Excepción al obtener POIs: {e}")
        return []

def obtener_pois_por_categorias(lat, lon, categorias, radio=100000):
    """Obtiene puntos de interés cercanos a las coordenadas dadas, agrupados por categorías."""
    pois_por_categoria = {}
    for categoria in categorias:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={categoria}&lat={lat}&lon={lon}&radius={radio}"
        try:
            print(f"Consultando POIs para categoría '{categoria}' con URL: {url}")  # Depuración
            response = requests.get(url, headers={"User-Agent": "GPStest/1.0"})
            if response.status_code == 200:
                data = response.json()
                print(f"Respuesta de la API para '{categoria}': {data}")  # Depuración
                pois = []
                for poi in data:
                    pois.append({
                        "nombre": poi.get("display_name", "Sin nombre"),
                        "lat": float(poi["lat"]),
                        "lon": float(poi["lon"])
                    })
                pois_por_categoria[categoria] = pois
            else:
                print(f"Error al obtener POIs para {categoria}: {response.status_code}, {response.text}")
                pois_por_categoria[categoria] = []
        except Exception as e:
            print(f"Excepción al obtener POIs para {categoria}: {e}")
            pois_por_categoria[categoria] = []
    return pois_por_categoria

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        print(f"Intentando registrar usuario: {username}")

        if User.query.filter_by(username=username).first():
            flash("El usuario ya existe.")
            return redirect(url_for("register"))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()  # Asegúrate de confirmar los cambios en la base de datos
        flash("Usuario registrado exitosamente.")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get("next")  # Redirige a la página solicitada originalmente
            return redirect(next_page) if next_page else redirect(url_for("index"))
        else:
            flash("Credenciales incorrectas.")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.")
    return redirect(url_for("login"))

@app.route("/admin/users")
@login_required
def admin_users():
    if not current_user.is_admin:
        flash("No tienes permiso para acceder a esta página.")
        return redirect(url_for("index"))

    users = User.query.all()
    return render_template("admin_users.html", users=users)

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    """Elimina un usuario."""
    if not current_user.is_admin:
        flash("No tienes permiso para realizar esta acción.")
        return redirect(url_for("admin_users"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("Usuario eliminado exitosamente.")
    return redirect(url_for("admin_users"))

@app.route("/admin/create_user", methods=["GET", "POST"])
@login_required
def create_user():
    """Crea un nuevo usuario desde la interfaz de administración."""
    if not current_user.is_admin:
        flash("No tienes permiso para acceder a esta página.")
        return redirect(url_for("admin_users"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        is_admin = request.form.get("is_admin") == "on"

        if User.query.filter_by(username=username).first():
            flash("El usuario ya existe.")
            return redirect(url_for("create_user"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username, password=hashed_password, is_admin=is_admin)
        db.session.add(new_user)
        db.session.commit()
        flash("Usuario creado exitosamente.")
        return redirect(url_for("admin_users"))

    return render_template("create_user.html")

@app.route("/admin/toggle_user/<int:user_id>", methods=["POST"])
@login_required
def toggle_user(user_id):
    """Bloquea o desbloquea una cuenta de usuario."""
    if not current_user.is_admin:
        flash("No tienes permiso para realizar esta acción.")
        return redirect(url_for("admin_users"))

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active  # Cambiar el estado de la cuenta
    db.session.commit()
    flash(f"El estado de la cuenta de {user.username} ha sido cambiado.")
    return redirect(url_for("admin_users"))

@app.route("/calcular_ruta", methods=["GET", "POST"])
@login_required
def calcular_ruta():
    if request.method == "GET":
        return render_template("calcular_ruta.html")

    # Procesar la solicitud POST
    data = request.form
    origen = data.get("origen")
    destino = data.get("destino")
    intervalo_km = float(data.get("intervalo_km", 10))  # Distancia entre checkpoints (por defecto: 10 km)
    velocidad_promedio = float(data.get("velocidad_promedio", 60))  # Velocidad promedio en km/h

    try:
        # Geocodificar las ubicaciones
        origen_coords = client.pelias_search(origen)["features"][0]["geometry"]["coordinates"]
        destino_coords = client.pelias_search(destino)["features"][0]["geometry"]["coordinates"]

        # Calcular la ruta
        route = client.directions(
            coordinates=[origen_coords, destino_coords],
            profile="driving-car",
            format="geojson"
        )

        # Extraer puntos de la ruta
        coordinates = route["features"][0]["geometry"]["coordinates"]
        distance_km = route["features"][0]["properties"]["segments"][0]["distance"] / 1000

        # Crear la ruta en la base de datos
        new_route = Route(
            user_id=current_user.id,
            origen=origen,
            destino=destino,
            distancia_total=distance_km
        )
        db.session.add(new_route)
        db.session.commit()

        # Generar checkpoints y calcular ETA
        route_points = []
        acumulado_km = 0
        tiempo_acumulado = 0  # Tiempo acumulado en horas
        for i in range(len(coordinates) - 1):
            start = coordinates[i]
            end = coordinates[i + 1]
            tramo_km = geodesic((start[1], start[0]), (end[1], end[0])).kilometers

            if acumulado_km + tramo_km >= intervalo_km:
                # Calcular el punto exacto donde se cumple el intervalo
                exceso_km = (acumulado_km + tramo_km) - intervalo_km
                factor = (tramo_km - exceso_km) / tramo_km
                punto_intermedio = [
                    start[0] + factor * (end[0] - start[0]),
                    start[1] + factor * (end[1] - start[1])
                ]

                tiempo_acumulado += intervalo_km / velocidad_promedio  # Tiempo estimado en horas
                checkpoint = Checkpoint(
                    route_id=new_route.id,
                    lat=punto_intermedio[1],
                    lon=punto_intermedio[0],
                    kilometro=round(acumulado_km + tramo_km, 1),
                    tiempo_estimado=round(tiempo_acumulado, 2)
                )
                db.session.add(checkpoint)
                route_points.append({
                    "lat": punto_intermedio[1],
                    "lon": punto_intermedio[0],
                    "kilometro": round(acumulado_km + tramo_km, 1),
                    "tiempo_estimado": round(tiempo_acumulado, 2)
                })

                # Reiniciar el acumulado y continuar desde el punto intermedio
                acumulado_km = exceso_km
                coordinates.insert(i + 1, punto_intermedio)
            else:
                acumulado_km += tramo_km

        db.session.commit()

        # Renderizar la plantilla con el mapa y los puntos calculados
        return render_template("ver_ruta.html", route=new_route, coordinates=coordinates, route_points=route_points)
    except Exception as e:
        flash(f"Error al calcular la ruta: {str(e)}")
        return redirect(url_for("calcular_ruta"))

@app.route("/mis_rutas")
@login_required
def mis_rutas():
    """Muestra las rutas guardadas por el usuario."""
    routes = Route.query.filter_by(user_id=current_user.id).all()

    # Convertir las rutas a un formato JSON para el frontend
    routes_data = []
    for route in routes:
        checkpoints = Checkpoint.query.filter_by(route_id=route.id).all()
        coordinates = [[checkpoint.lon, checkpoint.lat] for checkpoint in checkpoints]
        routes_data.append({
            "id": route.id,
            "origen": route.origen,
            "destino": route.destino,
            "distancia_total": route.distancia_total,
            "fecha_creacion": route.fecha_creacion.strftime('%Y-%m-%d'),  # Aquí se convierte en cadena
            "coordinates": coordinates
        })

    return render_template("mis_rutas.html", routes=routes_data)

@app.route("/eliminar_ruta/<int:route_id>", methods=["POST"])
@login_required
def eliminar_ruta(route_id):
    """Elimina una ruta guardada por el usuario."""
    route = Route.query.get_or_404(route_id)
    if route.user_id != current_user.id:
        flash("No tienes permiso para eliminar esta ruta.")
        return redirect(url_for("mis_rutas"))

    # Eliminar los checkpoints asociados
    Checkpoint.query.filter_by(route_id=route.id).delete()
    db.session.delete(route)
    db.session.commit()
    flash("Ruta eliminada exitosamente.")
    return redirect(url_for("mis_rutas"))

@app.route("/ver_ruta/<int:route_id>")
@login_required
def ver_ruta(route_id):
    """Muestra los detalles de una ruta específica con información del clima y POIs solo para el destino."""
    route = Route.query.get_or_404(route_id)
    if route.user_id != current_user.id:
        flash("No tienes permiso para ver esta ruta.")
        return redirect(url_for("mis_rutas"))

    # Obtener los checkpoints de la ruta
    checkpoints = Checkpoint.query.filter_by(route_id=route.id).all()
    coordinates = [[checkpoint.lon, checkpoint.lat] for checkpoint in checkpoints] if checkpoints else []

    # Validar que existan coordenadas
    if not coordinates:
        flash("No se encontraron coordenadas para esta ruta.")
        return redirect(url_for("mis_rutas"))

    # Obtener el clima en el destino
    clima_destino = obtener_clima(coordinates[-1][1], coordinates[-1][0]) if coordinates else {}

    # Categorías de POIs
    categorias = ["turismo", "comida", "panoramas"]

    # Obtener POIs agrupados por categorías solo para el destino
    pois_destino = obtener_pois_por_categorias(coordinates[-1][1], coordinates[-1][0], categorias) if coordinates else {}

    # Validar que los datos sean serializables y asignar valores predeterminados
    clima_destino = clima_destino if isinstance(clima_destino, dict) else {}
    pois_destino = pois_destino if isinstance(pois_destino, dict) else {}
    coordinates = coordinates if isinstance(coordinates, list) else []

    # Generar puntos de la ruta para el mapa
    route_points = [
        {
            "lat": checkpoint.lat,
            "lon": checkpoint.lon,
            "kilometro": checkpoint.kilometro,
            "tiempo_estimado": checkpoint.tiempo_estimado
        }
        for checkpoint in checkpoints
    ]

    return render_template(
        "ver_ruta.html",
        route=route,
        coordinates=coordinates,
        clima_destino=clima_destino,
        pois_destino=pois_destino,
        route_points=route_points
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)