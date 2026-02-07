/**
 * Page: mov/mov-request/mov-request-separacao-pend.j2
 * Pending request separation management
 */
(function() {
    'use strict';

    var nroReq = '';

    window.initMovRequestSeparacaoPend = function(config) {
        nroReq = config.nroReq || '';

        document.addEventListener('DOMContentLoaded', function() {
            reloadTables();
        });
    };

    window.getSeparacaoReqPend = function() {
        return new Promise(function(resolve, reject) {
            var localStorageData = localStorage.getItem(getStorageKey());
            if (localStorageData) {
                var payload = {
                    report_dir: 'requests'
                };
                fetch('/get/list-all-separations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                })
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.includes(getStorageKey() + '.json')) {
                        reject(new Error(304));
                    } else {
                        resolve(JSON.parse(localStorageData));
                    }
                });
            } else {
                fetch('/get/request/load-table-data?filename=' + getStorageKey())
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
            var sepReq = await getSeparacaoReqPend();

            // Obter itens da req
            var itens_req;
            try {
                var response = await fetch('/api/itens_req?id_req=' + nroReq, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    throw new Error('Erro HTTP: ' + response.status);
                }

                var result = await response.json();
                itens_req = result.itens;
            } catch (error) {
                console.error('Erro ao obter itens_req:', error);
                return;
            }

            // Agrupar os itens por código de item
            var groupedItems = sepReq.reduce(function(acc, item) {
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

                var qtde_solic = await fetchQtdeSolic(nroReq, cod_item);
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

            // Criar linhas de subtotal para itens zerados que não estão em sepReq
            for (var i = 0; i < itens_req.length; i++) {
                var itemCode = itens_req[i];
                if (!groupedItems[itemCode]) {
                    var subtotalRow = itemsTable.insertRow();

                    subtotalRow.insertCell(0);
                    subtotalRow.insertCell(1);
                    var cell0 = subtotalRow.insertCell(2);

                    cell0.textContent = itemCode;
                    cell0.style.textAlign = 'right';

                    var cell1 = subtotalRow.insertCell(3);
                    cell1.textContent = 'Subtotal:';

                    var qtde_solic = await fetchQtdeSolic(nroReq, itemCode);
                    subtotalRow.insertCell(4).innerHTML = '<span class="text-main-color">0</span> / ' + qtde_solic;

                    subtotalRow.classList.add('sub-total');
                }
            }

        } catch (error) {
            var alert = document.getElementById('alert-message');
            var content = document.getElementById('contentTable');

            var errorMessage = '<div class="msg-error">Erro: ' + error.message + '</div>';

            if (error.message == 304) {
                errorMessage = '<div class="msg-success"><details><summary>A requisição selecionada já foi finalizada.</summary>Para visualizá-la, filtre por \'finalizados\' clicando no ícone <img class="svg msg-svg" src="/static/svg/grid-2x2.svg"> acima.</details></div>';
                alert.innerHTML = errorMessage;

                Array.from(statusElements).forEach(function(element) {
                    element.innerHTML = '<span style="color: green">Finalizada</span>';
                });

            } else if (error.message == 404) {
                errorMessage = '<div class="msg-error"><details><summary>Nenhuma separação pendente ou iniciada neste código!</summary>Inicie a <a class="hyperlink" style="font-size: unset" href="/logi/req">separação da requisição</a> para realizar o faturamento.</details></div>';
                alert.innerHTML = errorMessage;
            }
            alert.classList.toggle('hidden');
            content.classList.add('hidden');
        }
        await visualDelay(500);
        hideLoading();
    }

    function reloadTables() {
        listSeparationsLocalStorage('requisicao/separacao/p');
        renderItems();
        renderCartSubtotals();
    }

    window.reloadTables = reloadTables;
})();
