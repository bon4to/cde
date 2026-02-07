/**
 * Page: mov/mov-carga/mov-carga-separacao-done.j2
 * Completed cargo separation view
 */
(function() {
    'use strict';

    var nroCarga = '';
    var seq = 0;
    var seqMax = [];
    var fantCliente = '';
    var obs_carga = '';

    window.initMovCargaSeparacaoDone = function(config) {
        nroCarga = config.nroCarga || '';
        seq = config.seq || 0;
        fantCliente = config.fantCliente || '';
        obs_carga = config.obs_carga || '';

        document.addEventListener('DOMContentLoaded', function() {
            reloadTables();
        });
    };

    function createSelect(options) {
        var select = document.getElementById('idCargaContainerSelect');
        var header = document.getElementById('idCargaContainer');

        console.log(options);
        console.log(options.length);

        if (options.length > 1) {
            header.style.display = 'none';
            select.style.display = 'inline-block';
        }

        options.forEach(function(option) {
            if (option !== 0 && option !== seq) {
                var opt = document.createElement('option');
                opt.value = option;
                opt.text = nroCarga + '-' + option;
                select.appendChild(opt);
            }
        });

        select.addEventListener('change', function() {
            var selectedValue = this.value;
            var currentUrl = window.location.pathname;
            var newUrl = currentUrl.split('-')[0] + '-' + selectedValue;
            window.location.href = newUrl;
        });
    }

    window.getSeparacaoDone = function() {
        return new Promise(function(resolve, reject) {
            var localStorageData = localStorage.getItem(getStorageKey());
            if (localStorageData) {
                reject(new Error(304));
            } else {
                fetch('/get/carga/load-table-data?filename=' + getStorageKey() + '&seq=' + seq)
                    .then(function(response) {
                        if (!response.ok) {
                            throw new Error(404);
                        }
                        return response.json();
                    })
                    .then(function(result) {
                        var cargaData = result.data;
                        var num_files = result.num_files;
                        resolve({ cargaData: cargaData, num_files: num_files });
                    })
                    .catch(function(error) {
                        reject(error);
                    });
            }
        });
    };

    async function renderItems() {
        showLoading();
        var itemsTable = document.getElementById('itemsTable').getElementsByTagName('tbody')[0];
        var statusElements = document.getElementsByClassName('separation_status');
        itemsTable.innerHTML = '';

        try {
            var result = await getSeparacaoDone();
            var sepCarga = result.cargaData;
            var numFiles = result.num_files;

            var seqArray = [];
            for (var i = 0; i < numFiles; i++) {
                seqArray.push(i);
            }
            createSelect(seqArray);

            // Obter itens da carga
            var itens_carga;
            try {
                var response = await fetch('/api/itens_carga?id_carga=' + nroCarga, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    throw new Error('Erro HTTP: ' + response.status);
                }

                var fetchResult = await response.json();
                itens_carga = fetchResult.itens;
            } catch (error) {
                console.error('Erro ao obter itens_carga:', error);
                return;
            }

            // Agrupar os itens por código de item
            var groupedItems = sepCarga.reduce(function(acc, item) {
                if (!acc[item.cod_item]) {
                    acc[item.cod_item] = [];
                }
                acc[item.cod_item].push(item);
                return acc;
            }, {});

            // Iterar sobre os grupos de itens
            for (var cod_item in groupedItems) {
                var items = groupedItems[cod_item];
                var subtotal = 0;

                for (var index = 0; index < items.length; index++) {
                    var item = items[index];
                    await visualDelay(50);
                    await getSeparadorName(item.user_id);

                    var row = itemsTable.insertRow();
                    row.insertCell(0).textContent = item.rua_letra + '.' + item.rua_numero;
                    var rowCodItem = row.insertCell(1);
                    rowCodItem.textContent = item.cod_item;
                    rowCodItem.style.textAlign = 'right';

                    var descCell = row.insertCell(2);
                    row.insertCell(3).textContent = item.lote_item;
                    row.insertCell(4).textContent = item.qtde_sep;

                    subtotal += item.qtde_sep;

                    try {
                        var descricao = await fetchItemDescription(item.cod_item);
                        descCell.style.textWrap = "pretty";
                        descCell.textContent = descricao;
                    } catch (error) {
                        console.error('Erro ao obter descrição:', error);
                        descCell.textContent = 'Erro ao obter descrição';
                    }
                }

                var qtde_solic = await fetchQtdeSolic(nroCarga, cod_item, 0);
                var subtotalRow = itemsTable.insertRow();

                subtotalRow.insertCell(0);
                subtotalRow.insertCell(1);
                var cell0 = subtotalRow.insertCell(2);

                cell0.textContent = cod_item;
                cell0.style.textAlign = 'right';

                var cell1 = subtotalRow.insertCell(3);
                cell1.textContent = 'Subtotal:';
                subtotalRow.insertCell(4).innerHTML = '<span class="text-main-color">' + subtotal + '</span> / ' + qtde_solic;

                subtotalRow.classList.add('sub-total');
            }

            // Criar linhas de subtotal para itens zerados que não estão em sepCarga
            for (var i = 0; i < itens_carga.length; i++) {
                var itemCode = itens_carga[i];
                if (!groupedItems[itemCode]) {
                    var subtotalRow = itemsTable.insertRow();

                    subtotalRow.insertCell(0);
                    subtotalRow.insertCell(1);
                    var cell0 = subtotalRow.insertCell(2);

                    cell0.textContent = itemCode;
                    cell0.style.textAlign = 'right';

                    var cell1 = subtotalRow.insertCell(3);
                    cell1.textContent = 'Subtotal:';

                    var qtde_solic = await fetchQtdeSolic(nroCarga, itemCode);
                    subtotalRow.insertCell(4).innerHTML = '<span class="text-main-color">0</span> / ' + qtde_solic;

                    subtotalRow.classList.add('sub-total');
                }
                Array.from(statusElements).forEach(function(element) {
                    element.innerHTML = "<span style='color: green'>Finalizada</span>";
                });
            }

        } catch (error) {
            var alert = document.getElementById('alert-message');
            var content = document.getElementById('contentTable');

            var errorMessage = '<div class="msg-error">Erro: ' + error.message + '</div>';

            if (error.message == 304) {
                errorMessage = '<div class="msg-info"><details><summary>Há uma separação pendente neste código!</summary>Para visualizá-la, filtre por \'pendentes\' clicando no ícone <img class="svg msg-svg" src="/static/svg/grid-2x2.svg"> acima.</details></div><div class="button-mini btn-fancy" onclick="clearItems()" title="APAGAR ITENS DA SEPARAÇÃO"><img class="svg-invert" src="/static/svg/eraser.svg" alt=""></div>';
            } else if (error.message == 404) {
                errorMessage = '<div class="msg-error"><details><summary>Nenhuma separação pendente ou iniciada neste código!</summary>Inicie a <a class="hyperlink" style="font-size: unset" href="/logi/cargas">separação da carga</a> para realizar o faturamento.</details></div>';
            }

            alert.innerHTML = errorMessage;
            alert.classList.toggle('hidden');
            content.classList.add('hidden');
        }
        await visualDelay(500);
        hideLoading();
    }

    async function reloadTables() {
        renderItems();
        renderCartSubtotals();
        listSeparations('cargas/separacao/f', 'server', 'cargas');
    }

    window.reloadTables = reloadTables;
})();
