/**
 * Page: mov/mov-carga/mov-carga-separacao-pend.j2
 * Pending cargo separation management
 */
(function() {
    'use strict';

    var nroCarga = '';
    var fantCliente = '';
    var obs_carga = '';

    window.initMovCargaSeparacaoPend = function(config) {
        nroCarga = config.nroCarga || '';
        fantCliente = config.fantCliente || '';
        obs_carga = config.obs_carga || '';

        document.addEventListener('DOMContentLoaded', function() {
            reloadTables();
        });
    };

    window.getSeparacaoPend = function() {
        return new Promise(function(resolve, reject) {
            var localStorageData = localStorage.getItem(getStorageKey());
            if (localStorageData) {
                resolve(JSON.parse(localStorageData));
            } else {
                fetch('/get/carga/load-table-data?filename=' + getStorageKey())
                    .then(function(response) {
                        if (!response.ok) {
                            throw new Error('Erro ao carregar dados do servidor');
                        }
                        return response.json();
                    })
                    .then(function(data) {
                        reject(new Error(304));
                    })
                    .catch(function(error) {
                        reject(new Error(404));
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
            var sepCarga = await getSeparacaoPend();

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

                var result = await response.json();
                itens_carga = result.itens;
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
                    await visualDelay(100);
                    await getSeparadorName(item.user_id);

                    var row = itemsTable.insertRow();
                    row.insertCell(0).textContent = item.rua_letra + '.' + item.rua_numero;
                    row.insertCell(1).textContent = item.cod_item;

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

                var qtde_solic = await fetchQtdeSolic(nroCarga, cod_item);
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
            }

        } catch (error) {
            var alert = document.getElementById('alert-message');
            var content = document.getElementById('contentTable');

            var errorMessage = '<div class="msg-error">Erro: ' + error.message + '</div>';

            if (error.message == 304) {
                hasPendingItems().then(function(bool) {
                    if (bool === true) {
                        showToast('A carga está incompleta. Verifique seus itens!', 'warn', 10);

                        errorMessage = '<div class="msg-alert"><details><summary>A separação foi finalizada, mas está incompleta.</summary>Para finalizá-la, clique no ícone <img class="svg msg-svg" src="/static/svg/package-badge.svg"> acima..</details></div>';
                    } else {
                        errorMessage = '<div class="msg-success"><details><summary>A carga selecionada já foi finalizada.</summary>Para visualizá-la, filtre por \'finalizados\' clicando no ícone <img class="svg msg-svg" src="/static/svg/grid-2x2.svg"> acima.</details></div>';
                    }

                    alert.innerHTML = errorMessage;
                });
                console.log(errorMessage);
                Array.from(statusElements).forEach(function(element) {
                    element.innerHTML = '<span style="color: green">Finalizada</span>';
                });

            } else if (error.message == 404) {
                errorMessage = '<div class="msg-error"><details><summary>Nenhuma separação pendente ou iniciada neste código!</summary>Inicie a <a class="hyperlink" style="font-size: unset" href="/logi/cargas">separação da carga</a> para realizar o faturamento.</details></div>';
                alert.innerHTML = errorMessage;
            }
            alert.classList.toggle('hidden');
            content.classList.add('hidden');
        }
        await visualDelay(500);
        hideLoading();
    }

    function reloadTables() {
        listSeparations('cargas/separacao/p', 'browser');
        renderItems();
        renderCartSubtotals();
    }

    window.reloadTables = reloadTables;
})();
