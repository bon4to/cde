/**
 * Page: etiqueta.j2
 * QR code label generation with history
 */
(function() {
    'use strict';

    var ultimoCodigo = '';
    var qrHistory = [];

    function isDuplicateQRCode(qr_text) {
        return qrHistory.some(function(item) { return item.text === qr_text; });
    }

    function addToQRHistory(qr_text, src) {
        qrHistory = qrHistory.filter(function(item) { return item.text !== qr_text; });

        qrHistory.unshift({
            src: src,
            text: qr_text
        });

        if (qrHistory.length > 9) {
            qrHistory.pop();
        }
    }

    function moveToFeatured(index) {
        if (index > 0 && index < qrHistory.length) {
            var qrCode = qrHistory[index];
            qrHistory.splice(index, 1);
            qrHistory.unshift(qrCode);
            updateQRImages();
        }
    }

    function updateQRImages() {
        $("#qrCodeImage").attr("src", qrHistory[0].src);

        for (var i = 1; i < 9; i++) {
            if (qrHistory[i]) {
                $("#qrCodeImage" + (i + 1)).attr("src", qrHistory[i].src);
            } else {
                $("#qrCodeImage" + (i + 1)).attr("src", "");
            }
        }
    }

    function buscarItens(codigo) {
        $.ajax({
            type: "POST",
            url: "/get/item",
            data: { input_code: codigo },
            success: function(response) {
                $("#desc_item").val(response.json_desc_item);
                $("#cod_item").empty();
                if (response.json_cod_item_ocurr) {
                    $("#json_cod_item_ocurr").text('( ' + response.json_cod_item_ocurr + ' )');
                } else {
                    $("#json_cod_item_ocurr").text('');
                }

                if (response.json_cod_item.length > 1) {
                    hideLockLabel("label-cod_item");
                    ultimoCodigo = codigo;
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

    function exibirQRCode(qr_text, desc_item, lote_item, cod_item, check) {
        $.ajax({
            type: "POST",
            url: "/etiqueta",
            data: { qr_text: qr_text, desc_item: desc_item, lote_item: lote_item, cod_item: cod_item, check: check },
            success: function(response) {
                var labelStatus = document.getElementById("label-success");

                addToQRHistory(qr_text, "data:image/img;base64," + response);
                updateQRImages();

                if (check === false) {
                    $("#qrCodeImage").attr("src", "data:image/img;base64," + response);
                } else {
                    $("#qrCodeImage").attr("src", "data:image/img;base64," + response);

                    var link = document.createElement('a');
                    link.href = "data:image/img;base64," + response;
                    link.download = qr_text + ".png";
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }
                labelStatus.innerHTML = '<div class="msg-success" style="width: 100%;">Etiqueta gerada com sucesso!</div>';
            },
            error: function(error) {
                var labelStatus = document.getElementById("label-success");
                labelStatus.innerHTML = '<div class="msg-error" style="width: 100%;">A etiqueta não pôde ser gerada!</div>';
                console.error("Erro ao exibir QR Code:", error);
            }
        });
    }

    // Initialize when DOM is ready
    $(function() {
        // Add click handlers to historical QR codes
        for (var i = 1; i <= 8; i++) {
            (function(index) {
                $("#qrCodeImage" + (index + 1)).click(function() {
                    moveToFeatured(index);
                });
            })(i);
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

        $("#form-field").submit(function(event) {
            event.preventDefault();

            var qr_text = $("#cod_item").val() + ";" + $("#lote_item").val();
            var desc_item = $("#desc_item").val();
            var cod_item = $("#cod_item").val();
            var lote_item = $("#lote_item").val();
            var check = $("#imgDownload").prop('checked');

            exibirQRCode(qr_text, desc_item, lote_item, cod_item, check);
        });
    });
})();
