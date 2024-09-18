// Inicializar o mapa
var map = L.map('map').setView([latitude_inicial, longitude_inicial], 13);

// Camada do mapa
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Carregar os dados do estoque
fetch('/s')
    .then(response => response.json())
    .then(data => {
        data.forEach(item => {
            let rua_letra = item.letra;
            let rua_numero = item.numero;
            let cod_item = item.cod_item;
            let desc_item = item.desc_item;
            let cod_lote = item.cod_lote;
            let saldo = item.saldo;

            // Criar coordenadas baseadas na rua e número (ajuste conforme necessário)
            let latitude = rua_numero * 0.001;  // Exemplos de cálculos fictícios
            let longitude = rua_letra.charCodeAt(0) * 0.001;

            // Adicionar marcador no mapa
            L.marker([latitude, longitude])
                .addTo(map)
                .bindPopup(`
                    <b>Item:</b> ${cod_item} - ${desc_item}<br>
                    <b>Lote:</b> ${cod_lote}<br>
                    <b>Saldo:</b> ${saldo}
                `);
        });
    });
