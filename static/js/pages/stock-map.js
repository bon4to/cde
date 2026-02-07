/**
 * Page: stock-map.j2
 * Interactive warehouse stock map visualization
 */
(function() {
    'use strict';

    // Map layout configuration
    var mapLayout = {
        'A': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36],
        'B': [1, 2, 3, 4, 0, 0, 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 0, 0],
        'C': [0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 0, 0, 0, 0, 0, 0, 0, 0],
        'D': [0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 0, 0],
        'PP1': [1, 2],
        'PP2': [1, 2],
        'PP3': [1],
        'PP4': [1]
    };

    // Colors for each item
    var colors = [
        'rgb(var(--alt-color-1))', 'rgb(var(--alt-color-2))', 'rgb(var(--alt-color-3))',
        'rgb(var(--alt-color-4))', 'rgb(var(--alt-color-5))', 'rgb(var(--alt-color-6))',
        'rgb(var(--alt-color-7))'
    ];

    // Generate row function
    function generateRua(map, groupedData, corredor) {
        mapLayout[corredor].forEach(function(numero) {
            var cell = document.createElement('div');
            if (numero === 0) {
                cell.classList.add('invisible-cell');
                map.appendChild(cell);
                return;
            }
            cell.classList.add('map-cell');
            var items = groupedData[corredor] && groupedData[corredor][numero];

            if (items) {
                var stackedBar = document.createElement('div');
                stackedBar.classList.add('stacked-bar');
                stackedBar.draggable = false;
                var total = Object.values(items).reduce(function(a, b) { return a + b; }, 0);

                Object.keys(items).forEach(function(item, index) {
                    var itemBar = document.createElement('div');
                    itemBar.classList.add('item-bar');
                    itemBar.style.height = ((items[item] / total) * 100) + '%';
                    itemBar.style.backgroundColor = colors[index % colors.length];

                    var legend = document.createElement('div');
                    legend.classList.add('legend');
                    legend.innerHTML = corredor + '.' + numero + '<br>' + item + ': ' + items[item];
                    itemBar.appendChild(legend);

                    stackedBar.appendChild(itemBar);
                });

                cell.appendChild(stackedBar);
            } else {
                cell.classList.add('empty-cell');
                cell.innerHTML = '';
            }

            map.appendChild(cell);
        });
    }

    // Initialize map
    document.addEventListener('DOMContentLoaded', function() {
        var map = document.getElementById('map');
        if (!map) return;

        fetch('/get/stock_items')
            .then(function(response) { return response.json(); })
            .then(function(data) {
                // Group by letter and number
                var groupedData = {};
                data.forEach(function(item) {
                    var letra = item.letra;
                    var numero = item.numero;
                    var cod_item = item.cod_item;
                    var saldo = item.saldo;

                    if (!groupedData[letra]) groupedData[letra] = {};
                    if (!groupedData[letra][numero]) groupedData[letra][numero] = {};
                    if (!groupedData[letra][numero][cod_item]) groupedData[letra][numero][cod_item] = 0;
                    groupedData[letra][numero][cod_item] += saldo;
                });

                // Generate rows
                generateRua(map, groupedData, 'A');

                var corredorAB = document.createElement('div');
                corredorAB.classList.add('corredor-space');
                map.appendChild(corredorAB);

                generateRua(map, groupedData, 'B');
                generateRua(map, groupedData, 'C');

                var corredorCD = document.createElement('div');
                corredorCD.classList.add('corredor-space');
                map.appendChild(corredorCD);

                generateRua(map, groupedData, 'D');
            });

        // Zoom and pan controls
        var scale = 1;
        var posX = 0, posY = 0;
        var isDragging = false;
        var startX, startY;

        map.addEventListener('wheel', function(e) {
            e.preventDefault();
            var zoomIntensity = 0.1;
            var zoom = e.deltaY > 0 ? 1 - zoomIntensity : 1 + zoomIntensity;
            scale = Math.min(Math.max(0.5, scale * zoom), 3);
            map.style.transform = 'scale(' + scale + ') translate(' + posX + 'px, ' + posY + 'px)';
        }, { passive: false });

        map.addEventListener('mousedown', function(e) {
            isDragging = true;
            startX = e.pageX - posX;
            startY = e.pageY - posY;
        });

        map.addEventListener('mousemove', function(e) {
            if (!isDragging) return;
            posX = e.pageX - startX;
            posY = e.pageY - startY;
            map.style.transform = 'scale(' + scale + ') translate(' + posX + 'px, ' + posY + 'px)';
        });

        map.addEventListener('mouseup', function() {
            isDragging = false;
        });

        map.addEventListener('mouseleave', function() {
            isDragging = false;
        });
    });
})();
