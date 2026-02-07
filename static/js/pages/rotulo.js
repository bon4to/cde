/**
 * Page: rotulo.j2
 * Label roll calculator with image switching
 */
(function() {
    'use strict';

    var staticPath = '';

    window.initRotulo = function(path) {
        staticPath = path;

        var input1 = document.getElementById("espessura_fita");
        var input2 = document.getElementById("diametro_inicial");
        var input3 = document.getElementById("diametro_minimo");
        var input4 = document.getElementById("espessura_papelao");
        var input5 = document.getElementById("compr_rotulo");
        var dynamicImage = document.getElementById("dynamicImage");

        if (input1) {
            input1.addEventListener("focus", function() {
                dynamicImage.src = staticPath + "img/rotulo/rotulo_esp_rot.jpg";
            });
        }
        if (input2) {
            input2.addEventListener("focus", function() {
                dynamicImage.src = staticPath + "img/rotulo/rotulo_diam_total.jpg";
            });
        }
        if (input3) {
            input3.addEventListener("focus", function() {
                dynamicImage.src = staticPath + "img/rotulo/rotulo_diam_int.jpg";
            });
        }
        if (input4) {
            input4.addEventListener("focus", function() {
                dynamicImage.src = staticPath + "img/rotulo/rotulo_esp_tub.jpg";
            });
        }
        if (input5) {
            input5.addEventListener("focus", function() {
                dynamicImage.src = staticPath + "img/rotulo/rotulo_dist_rot.jpg";
            });
        }

        // Form submit handler
        $("#form-field").submit(function(event) {
            event.preventDefault();
            triggerCalculation();
        });

        // Debounced input handler
        var timeout;
        $("input[type='number']").on('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                triggerCalculation();
            }, 1000);
        });

        // Max length validation
        var inputs = document.querySelectorAll('.address');
        inputs.forEach(function(input) {
            input.addEventListener('input', function() {
                verificarComprimento(this);
            });
        });
    };

    function triggerCalculation() {
        var espessura_fita = $("#espessura_fita").val();
        var diametro_inicial = $("#diametro_inicial").val();
        var diametro_minimo = $("#diametro_minimo").val();
        var espessura_papelao = $("#espessura_papelao").val();
        var compr_rotulo = $("#compr_rotulo").val();
        calculaRotulo(espessura_fita, diametro_inicial, diametro_minimo, espessura_papelao, compr_rotulo);
    }

    function calculaRotulo(espessura_fita, diametro_inicial, diametro_minimo, espessura_papelao, compr_rotulo) {
        $.ajax({
            type: "POST",
            url: "/rotulo",
            data: {
                espessura_fita: espessura_fita,
                diametro_inicial: diametro_inicial,
                diametro_minimo: diametro_minimo,
                espessura_papelao: espessura_papelao,
                compr_rotulo: compr_rotulo
            },
            success: function(response) {
                $("#resposta1").text(response.num_rotulos_str + " rótulos");
                $("#resposta2").text(response.comprimento_mtrs + " metros");
                $("#resposta3").text("O tubo de rótulo tem " + response.num_voltas + " voltas");
            },
            error: function(error) {
                console.error("Erro ao exibir o valor", error);
            }
        });
    }

    function verificarComprimento(input) {
        if (input.value.length > input.maxLength) {
            input.value = input.value.slice(0, input.maxLength);
        }
    }
})();
