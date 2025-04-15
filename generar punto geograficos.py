import csv
import json
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.point import Point
from datetime import datetime  # Importamos el módulo datetime

# Inicializar geolocalizador
geolocator = Nominatim(user_agent="gps_ruta_app")

# Ingresar ciudades
origen_nombre = input("📍 Ingrese la ciudad de origen (ej: Buenos Aires, Argentina): ")
destino_nombre = input("📍 Ingrese la ciudad de destino (ej: Rosario, Argentina): ")

# Obtener coordenadas
origen = geolocator.geocode(origen_nombre)
destino = geolocator.geocode(destino_nombre)

# Validar resultados
if not origen or not destino:
    print("❌ No se pudo encontrar una de las ciudades. Verifica los nombres.")
    exit()

# Mostrar resultados
print(f"\n✅ Coordenadas encontradas:")
print(f"Origen: {origen.address} → ({origen.latitude}, {origen.longitude})")
print(f"Destino: {destino.address} → ({destino.latitude}, {destino.longitude})\n")

# Crear puntos
start = Point(origen.latitude, origen.longitude)
end = Point(destino.latitude, destino.longitude)
distance_km = geodesic(start, end).kilometers
num_points = int(distance_km // 10) + 1

lat_step = (end.latitude - start.latitude) / (num_points - 1)
lon_step = (end.longitude - start.longitude) / (num_points - 1)

route_points = []
for i in range(num_points):
    lat = start.latitude + i * lat_step
    lon = start.longitude + i * lon_step
    checkpoint_location = geolocator.reverse((lat, lon), language='es', timeout=10)
    if checkpoint_location:
        location_name = checkpoint_location.address
    else:
        location_name = "Ubicación no encontrada"
    
    # Obtener la hora de lectura
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    route_points.append({
        "kilometro": i * 10,
        "latitud": round(lat, 6),
        "longitud": round(lon, 6),
        "ubicacion": location_name,  # Agregamos el nombre de la ubicación
        "hora": current_time  # Agregamos la hora de lectura
    })

# Mostrar puntos en consola
print("🧭 Ruta aproximada con Checkpoints y Hora de Lectura:")
print("Km\tLatitud\t\tLongitud\tUbicación\t\tHora")
for point in route_points:
    print(f"{point['kilometro']}\t{point['latitud']}\t{point['longitud']}\t{point['ubicacion']}\t{point['hora']}")

# Guardar en CSV
csv_filename = "ruta_gps_con_checkpoints_y_hora.csv"
with open(csv_filename, "w", newline="") as csvfile:
    fieldnames = ["kilometro", "latitud", "longitud", "ubicacion", "hora"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for point in route_points:
        writer.writerow(point)

print(f"\n📄 Ruta guardada en archivo CSV con Checkpoints y Hora: {csv_filename}")

# Guardar en GeoJSON
geojson_filename = "ruta_gps_con_checkpoints_y_hora.geojson"
geojson_data = {
    "type": "FeatureCollection",
    "features": []
}

for point in route_points:
    feature = {
        "type": "Feature",
        "properties": {
            "kilometro": point["kilometro"],
            "ubicacion": point["ubicacion"],
            "hora": point["hora"]  # Agregar la hora en las propiedades
        },
        "geometry": {
            "type": "Point",
            "coordinates": [point["longitud"], point["latitud"]]
        }
    }
    geojson_data["features"].append(feature)

with open(geojson_filename, "w") as f:
    json.dump(geojson_data, f, indent=2)

print(f"🗺️ Ruta guardada en archivo GeoJSON con Checkpoints y Hora: {geojson_filename}")
