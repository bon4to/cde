/**
 * Page: mov/mov.j2
 * Movement operations with item search
 */

// Global variables needed by bundle.js
var isColumnVisible = false;
var userID = '';
var tableData = [];

(function() {
    'use strict';

    var ultimoCodigo = '';

    window.initMov = function(userId) {
        userID = userId;

        // Initialize field visibility based on operation type
        if (typeof toggleFields === 'function') {
            toggleFields();
        }

        $("#formBuscarItens").submit(function(event) {
            event.preventDefault();
            var codigo = $("#input_code").val();
            buscarItens(codigo);
            $("#input_code").val('');
        });

        $("#cod_item").change(function(event) {
            event.preventDefault();
            var codigo = $("#cod_item").val();
            buscarItens(codigo);
            $("#input_code").val(ultimoCodigo);
        });

        document.getElementById("form-field").addEventListener("submit", function() {
            document.getElementById("submitform").disabled = true;
        });
    };

    function buscarItens(codigo) {
        $.ajax({
            type: "POST",
            url: "/get/item",
            data: { input_code: codigo },
            success: function(response) {
                $("#desc_item").val(response.json_desc_item);

                $("#cod_item").empty();
                if (response.json_cod_item.length != 1) {
                    $("#json_item_no").text('( ' + response.json_cod_item.length + ' )');
                } else {
                    $("#json_item_no").text('');
                }

                if (response.json_cod_item.length > 1) {
                    hideLockLabel("label-cod_item");
                    ultimoCodigo = codigo;
                }

                if (response.json_cod_item) {
                    response.json_cod_item.forEach(function(item) {
                        $("#cod_item").append("<option value='" + item + "'>" + item + "</option>");
                    });
                    if (response.json_cod_item && response.json_cod_item.length > 0) {
                        $("#filterInput").val(response.json_cod_item[0]);
                        filterTable();
                    }
                } else {
                    $("#cod_item").append("<option value=''></option>");
                }
                $("#lote_item").val(response.json_cod_lote);

                if (response.json_cod_lote === "") {
                    hideLockLabel("label-cod_lote");
                    $("#lote_item").prop("readonly", false);
                } else {
                    $("#lote_item").prop("readonly", true);
                    getItemFirstMov(response.json_cod_lote);
                }
            },
            error: function(error) {
                console.error("Erro ao buscar itens:", error);
            }
        });
    }

    window.getItemFirstMov = function(loteItem) {
        var selectedItem = document.getElementById("cod_item").value;
        var dataFabInput = document.getElementById("date_fab");
        var dataLockedInput = document.getElementById("data_locked");

        function setDataFab(date) {
            if (date) {
                dataFabInput.value = date;
                dataFabInput.setAttribute('readonly', true);
                dataLockedInput.value = true;

                dataFabInput.onclick = function() {
                    alert("O lote deste item foi registrado pela primeira vez em " + date);
                };
                return;
            }
            dataFabInput.value = '';
            dataFabInput.removeAttribute('readonly');
            dataLockedInput.value = false;
            dataFabInput.onclick = '';
        }

        if (loteItem.length <= 3 || !/^[A-Z]{2}\d{4}$/.test(loteItem)) {
            setDataFab(null);
            return;
        }

        dataFabInput.max = new Date().toISOString().split('T')[0];

        fetch('/api/get_item_first_mov?cod_item=' + selectedItem + '&cod_lote=' + loteItem)
            .then(function(response) { return response.json(); })
            .then(function(data) {
                setDataFab(data.first_mov);
            })
            .catch(function(error) {
                console.error('Erro ao obter data de fabricação:', error);
            });
    };
})();
