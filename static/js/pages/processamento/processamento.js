/**
 * Page: processamento/processamento.j2
 * Processing management with date filtering
 */
(function() {
    'use strict';

    // Initialize with week filter on load
    document.addEventListener('DOMContentLoaded', function() {
        getSemana();
    });

    window.updateLinhaOptions = function() {
        var embalagem = document.getElementById("embalagem").value;
        var linhaSelect = document.getElementById("linha");

        linhaSelect.innerHTML = "";

        if (embalagem === "PET") {
            addOption(linhaSelect, "2", "2");
            addOption(linhaSelect, "5", "5");
        } else if (embalagem === "VIDRO") {
            addOption(linhaSelect, "1", "1");
            addOption(linhaSelect, "3", "3");
        } else if (embalagem === "BAG") {
            addOption(linhaSelect, "4", "4");
        }
    };

    window.updateCorOptions = function() {
        var liqLinha = document.getElementById("liq_linha");
        var corSelect = document.getElementById("liq_cor");
        var corField = document.getElementById("liq_cor_field");
        var twoSplitField = document.getElementById("two_split_field");

        corSelect.innerHTML = "";
        liqLinha.classList.remove('address');

        if (liqLinha.value === "UVA") {
            addOption(corSelect, "TINTO", "TINTO");
            addOption(corSelect, "BRANCO", "BRANCO");
            addOption(corSelect, "ROSE", "ROSÉ");

            corField.style.display = "inline-block";
            liqLinha.classList.add('address');
            twoSplitField.classList.add('two-split');

        } else if (liqLinha.value === "MISTO") {
            addOption(corSelect, "UVA / MACA", "UVA / MACA");
            addOption(corSelect, "MACA / UVA", "MACA / UVA");
            addOption(corSelect, "MACA / LARANJA", "MACA / LARANJA");
            addOption(corSelect, "LARANJA / MACA", "LARANJA / MACA");
            addOption(corSelect, "TANGERINA / MACA", "TANGERINA / MACA");
            addOption(corSelect, "MACA / TANGERINA", "MACA / TANGERINA");
            addOption(corSelect, "LIMAO / MACA", "LIMAO / MACA");
            addOption(corSelect, "MACA / UVAS BRANCAS", "MACA / UVAS BRANCAS");
            addOption(corSelect, "MACA / TANGERINA / ACEROLA", "MACA / TANGERINA / ACEROLA");
            addOption(corSelect, "MACA / MANGA", "MACA / MANGA");
            addOption(corSelect, "MACA / MARACUJA", "MACA / MARACUJA");
            addOption(corSelect, "TANGERINA / MACA", "TANGERINA / MACA");
            addOption(corSelect, "UVA / MIRTILO", "UVA / MIRTILO");
            addOption(corSelect, "UVAS BRANCAS / FRAMBOESA", "UVAS BRANCAS / FRAMBOESA");
            addOption(corSelect, "UVA / AMORA", "UVA / AMORA");
            addOption(corSelect, "UVA / ACAI", "UVA / ACAI");

            corField.style.display = "inline-block";
            liqLinha.classList.add('address');
            twoSplitField.classList.add('two-split');

        } else {
            addOption(corSelect, " ", " ");
            corField.style.display = 'none';
            twoSplitField.classList.remove('two-split');
        }
    };

    function addOption(selectElement, value, text) {
        var option = document.createElement("option");
        option.value = value;
        option.text = text;
        selectElement.appendChild(option);
    }

    window.redirectToEdit = function(idProducao) {
        window.location.href = "/processamento/edit?id_producao=" + idProducao;
    };

    window.confirmConcluir = function(codProducao, checkbox) {
        if (confirm("Você tem certeza que deseja concluir esta programação?")) {
            window.location.href = "/processamento/done/" + codProducao;
        } else {
            checkbox.checked = false;
        }
    };

    window.filterByDate = function() {
        var filterDate1 = document.getElementById('filterDate1').value;
        var filterDate2 = document.getElementById('filterDate2').value;
        var tables = document.querySelectorAll('.table-overflow');

        if (!filterDate2) {
            filterDate2 = filterDate1;
        }

        tables.forEach(function(table) {
            var rows = table.querySelectorAll('tr');
            rows.forEach(function(row) {
                var cells = row.querySelectorAll('td');
                if (cells.length > 5) {
                    var dataProducao = cells[4].textContent.trim();
                    var isVisible = isDateInRange(dataProducao, filterDate1, filterDate2);
                    row.style.display = isVisible ? 'table-row' : 'none';
                }
            });
        });
    };

    function isDateInRange(date, startDate, endDate) {
        if (!startDate && !endDate) {
            return true;
        } else if (!startDate) {
            endDate.value = startDate.value;
        } else if (!endDate) {
            startDate.value = endDate.value;
        }

        var dateObj = new Date(date);
        var startDateObj = new Date(startDate);
        var endDateObj = new Date(endDate);

        if (!isNaN(dateObj.getTime()) && !isNaN(startDateObj.getTime()) && !isNaN(endDateObj.getTime())) {
            return dateObj >= startDateObj && dateObj <= endDateObj;
        }

        return false;
    }

    window.getHoje = function() {
        var today = new Date();
        var periodDateField = document.getElementById("period-date");

        document.getElementById('filterDate1').value = today.toISOString().split('T')[0];
        document.getElementById('filterDate2').value = '';
        periodDateField.style.display = 'none';

        filterByDate();
        document.getElementById('filterDate1').focus();
    };

    window.limpaData = function() {
        document.getElementById('filterDate1').value = "";
        document.getElementById('filterDate2').value = "";
        filterByDate();
        document.getElementById('filterDate1').focus();
    };

    function getSemana() {
        var today = new Date();
        var firstDayOfWeek = new Date(today);
        var lastDayOfWeek = new Date(today);
        var periodDateField = document.getElementById("period-date");

        var diff = today.getDay();
        firstDayOfWeek.setDate(today.getDate() - diff);
        lastDayOfWeek.setDate(today.getDate() + (6 - diff));

        document.getElementById('filterDate1').value = formatDate(firstDayOfWeek);
        document.getElementById('filterDate2').value = formatDate(lastDayOfWeek);
        periodDateField.style.display = 'contents';

        filterByDate();
        document.getElementById('filterDate1').focus();
    }
    window.getSemana = getSemana;

    function formatDate(date) {
        var year = date.getFullYear();
        var month = date.getMonth() + 1;
        var day = date.getDate();

        month = month < 10 ? '0' + month : month;
        day = day < 10 ? '0' + day : day;

        return year + '-' + month + '-' + day;
    }
})();
