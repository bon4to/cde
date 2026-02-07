/**
 * Page: mov/mov-faturado.j2
 * Billed items view with search
 */
(function() {
    'use strict';

    function buscarItens() {
        var codigo = $("#input_code").val();

        $.ajax({
            type: "POST",
            url: "/get/item",
            data: { input_code: codigo },
            success: function(response) {
                $("#desc_item").val(response.json_desc_item);
                $("#input_code").val("");
                $("#cod_item").empty();

                if (response.json_cod_item.length > 1) {
                    hideLockLabel("label-cod_item");
                }

                if (response.json_cod_item) {
                    response.json_cod_item.forEach(function(item) {
                        $("#cod_item").append("<option value='" + item + "'>" + item + "</option>");
                    });
                } else {
                    $("#cod_item").append("<option value=''></option>");
                }

                $("#lote_item").val(response.json_cod_lote);

                if (response.json_cod_lote === "") {
                    hideLockLabel("label-cod_lote");
                    $("#lote_item").prop("readonly", false);
                } else {
                    $("#lote_item").prop("readonly", true);
                }
            },
            error: function(error) {
                console.error("Erro ao buscar itens:", error);
            }
        });
    }

    // Initialize on DOM ready
    $(document).ready(function() {
        $("#formBuscarItens").submit(function(event) {
            event.preventDefault();
            buscarItens();
        });

        var formField = document.getElementById("form-field");
        if (formField) {
            formField.addEventListener("submit", function() {
                document.getElementById("submitform").disabled = true;
            });
        }
    });
})();
