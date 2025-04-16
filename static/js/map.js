document.addEventListener('DOMContentLoaded', () => {
    const map = L.map('map').setView([0, 0], 2);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    const coordinates = window.routeCoordinates;
    const polyline = L.polyline(coordinates.map(coord => [coord[1], coord[0]]), { color: 'blue' }).addTo(map);
    map.fitBounds(polyline.getBounds());

    const climaOrigen = window.climaOrigen;
    if (climaOrigen && !climaOrigen.error) {
        const origenMarker = L.marker([coordinates[0][1], coordinates[0][0]]).addTo(map);
        origenMarker.bindPopup(`
            <strong>Clima en el Origen</strong><br>
            Temperatura: ${climaOrigen.temperatura}°C<br>
            Descripción: ${climaOrigen.descripcion}<br>
            <img src="http://openweathermap.org/img/wn/${climaOrigen.icono}@2x.png" alt="Icono del clima">
        `);
    }

    const climaDestino = window.climaDestino;
    if (climaDestino && !climaDestino.error) {
        const destinoMarker = L.marker([coordinates[coordinates.length - 1][1], coordinates[coordinates.length - 1][0]]).addTo(map);
        destinoMarker.bindPopup(`
            <strong>Clima en el Destino</strong><br>
            Temperatura: ${climaDestino.temperatura}°C<br>
            Descripción: ${climaDestino.descripcion}<br>
            <img src="http://openweathermap.org/img/wn/${climaDestino.icono}@2x.png" alt="Icono del clima">
        `);
    }

    // Agregar POIs en el origen
    const poisOrigen = window.poisOrigen;
    poisOrigen.forEach(poi => {
        const poiMarker = L.marker([poi.lat, poi.lon]).addTo(map);
        poiMarker.bindPopup(`
            <strong>${poi.nombre}</strong><br>
            Categoría: Restaurante
        `);
    });

    // Agregar POIs en el destino
    const poisDestino = window.poisDestino;
    poisDestino.forEach(poi => {
        const poiMarker = L.marker([poi.lat, poi.lon]).addTo(map);
        poiMarker.bindPopup(`
            <strong>${poi.nombre}</strong><br>
            Categoría: Restaurante
        `);
    });

    const recenterButton = document.createElement('button');
    recenterButton.textContent = 'Centrar Ruta';
    recenterButton.style.position = 'absolute';
    recenterButton.style.top = '10px';
    recenterButton.style.right = '10px';
    recenterButton.style.zIndex = '1000';
    recenterButton.style.padding = '10px';
    recenterButton.style.backgroundColor = '#007bff';
    recenterButton.style.color = 'white';
    recenterButton.style.border = 'none';
    recenterButton.style.borderRadius = '5px';
    recenterButton.style.cursor = 'pointer';

    recenterButton.addEventListener('click', () => {
        map.fitBounds(polyline.getBounds());
    });

    document.body.appendChild(recenterButton);
});
