/**
 * Page: mov/mov-carga/mov-carga.j2
 * Carga management and separation
 */
(function() {
    'use strict';

    var nroCarga = '';
    var codItem = '';
    var userID = '';
    var itemCount = 0;

    window.initMovCarga = function(config) {
        nroCarga = config.nroCarga || '';
        codItem = config.codItem || '';
        userID = config.userId || '';

        document.addEventListener('DOMContentLoaded', function() {
            var rows = document.querySelectorAll('.js_query_selector');

            rows.forEach(function(row) {
                row.addEventListener('click', function() {
                    var idCarga = this.getAttribute('data-id');
                    window.location.href = '/logi/cargas/' + idCarga;
                });

                var carga = row.getAttribute('data-id');

                row.addEventListener('mouseenter', function() {
                    rows.forEach(function(r) {
                        if (r.getAttribute('data-id') === carga) {
                            r.classList.add('hover-related');
                        }
                    });
                });

                row.addEventListener('mouseleave', function() {
                    rows.forEach(function(r) {
                        if (r.getAttribute('data-id') === carga) {
                            r.classList.remove('hover-related');
                        }
                    });
                });
            });

            if (!codItem) {
                listSeparations('cargas/separacao/p', 'browser');
            }
        });
    };

    window.getSeparacao = function() {
        return new Promise(function(resolve, reject) {
            var localStorageData = localStorage.getItem(getStorageKey());
            if (localStorageData) {
                try {
                    var checkPending = typeof hasPendingItems === 'function' ? hasPendingItems() : Promise.resolve(false);
                    checkPending.then(function(bool) {
                        if (bool === true) {
                            showToast('A carga está incompleta. Verifique seus itens!', 'warn', 10);
                            showIncompleteAlert();
                        } else {
                            resolve(JSON.parse(localStorageData));
                        }
                    });
                } catch (error) {
                    resolve(JSON.parse(localStorageData));
                }
            } else {
                fetch('/get/carga/load-table-data?filename=' + getStorageKey())
                    .then(function(response) {
                        if (!response.ok) {
                            throw new Error('Erro ao carregar dados do servidor');
                        }
                        return response.json();
                    })
                    .then(function(data) {
                        reject(new Error('A carga selecionada já foi finalizada.'));
                        if (typeof hasPendingItems === 'function') {
                            hasPendingItems().then(function(bool) {
                                if (bool === true) {
                                    showToast('A carga está incompleta. Verifique seus itens!', 'warn', 10);
                                    showIncompleteAlert();
                                }
                            });
                        }
                    })
                    .catch(function(error) {
                        reject(new Error('Nenhuma carga pendente ou iniciada neste código.'));
                    });
            }
        });
    };

    function showIncompleteAlert() {
        var errorMessage = '<div class="msg-alert"><details><summary>A separação foi finalizada, mas está incompleta.</summary>Para finalizá-la, clique no ícone acima.</details></div>';
        var alert = document.getElementById('alert-message');
        var standardTable = document.getElementById('standardTable');
        var detailedTable = document.getElementById('detailedTable');

        if (alert) {
            alert.innerHTML = errorMessage;
            alert.classList.toggle('hidden');
        }
        if (standardTable) standardTable.classList.add('hidden');
        if (detailedTable) detailedTable.classList.add('hidden');
    }

    window.toggleTableSubtotal = function() {
        var detailedTable = document.getElementById('detailedTable');
        var standardTable = document.getElementById('standardTable');

        if (detailedTable) detailedTable.classList.toggle('hidden');
        if (standardTable) standardTable.classList.toggle('hidden');
    };

    window.getAndCompareItems = async function() {
        try {
            var sepCarga = await getSeparacao();
            var storageKey = getStorageKey();

            var itemsList = [];

            for (var i = 0; i < sepCarga.length; i++) {
                var item = sepCarga[i];
                var cod_item = item.cod_item;
                var qtde_solic = item.qtde_solic;
                var qtde_sep = getQtdeItemLS(storageKey, cod_item);

                itemsList.push({ cod_item: cod_item, qtde_solic: qtde_solic, qtde_sep: qtde_sep });
            }

            console.log('Lista de Itens:', itemsList);

        } catch (error) {
            console.error('Erro ao obter separação:', error);
        }
    };
})();
