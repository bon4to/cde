/**
 * Page: estoque-enderecado.j2
 * Stock management with item details modal
 */
(function() {
    'use strict';

    var itemsData = [];
    var currentItem = null;

    // Format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS to DD/MM/YYYY
    function formatDateBR(dateStr) {
        if (!dateStr || dateStr === '-') return '-';
        var datePart = dateStr.split(' ')[0];
        var parts = datePart.split('-');
        if (parts.length !== 3) return dateStr;
        return parts[2] + '/' + parts[1] + '/' + parts[0];
    }

    window.initEstoqueEnderecado = function(data) {
        itemsData = data;

        var filterTable = document.getElementById('filterTable');
        if (filterTable) {
            filterTable.addEventListener('click', function(e) {
                var row = e.target.closest('tr[data-item-index]');
                if (row) {
                    var index = parseInt(row.dataset.itemIndex);
                    openItemModal(itemsData[index]);
                }
            });
        }
    };

    function openItemModal(item) {
        currentItem = item;

        document.getElementById('modalTitle').textContent = item.desc_item;
        document.getElementById('modalCodItem').textContent = item.cod_item;
        document.getElementById('modalDescItem').textContent = item.desc_item;
        document.getElementById('modalCodLote').textContent = item.cod_lote;
        document.getElementById('modalAddress').textContent = item.address.trim();
        document.getElementById('modalSaldo').textContent = item.saldo + ' un';

        var validadeText = '-';
        if (typeof item.validade === 'number') {
            validadeText = item.validade + ' dias (' + item.validade_str + ')';
        } else if (item.validade) {
            validadeText = item.validade;
        }
        document.getElementById('modalValidade').textContent = validadeText;

        document.getElementById('modalDateFabDisplay').textContent = formatDateBR(item.date_fab) || '-';
        document.getElementById('modalDateFab').value = '';
        document.getElementById('modalFirstMov').textContent = 'Carregando...';
        document.getElementById('modalDateFabCustomBadge').classList.add('hidden');
        document.getElementById('btnClearDateFab').classList.add('hidden');

        Modal.open('itemModal');

        fetch('/api/custom_date_fab?cod_item=' + encodeURIComponent(item.cod_item) + '&cod_lote=' + encodeURIComponent(item.cod_lote))
            .then(function(response) { return response.json(); })
            .then(function(data) {
                document.getElementById('modalFirstMov').textContent = formatDateBR(data.first_mov) || '-';

                if (data.custom_date_fab) {
                    document.getElementById('modalDateFab').value = data.custom_date_fab;
                    document.getElementById('modalDateFabCustomBadge').classList.remove('hidden');
                    document.getElementById('btnClearDateFab').classList.remove('hidden');
                } else if (data.first_mov) {
                    document.getElementById('modalDateFab').value = data.first_mov;
                }
            })
            .catch(function(err) {
                console.error('Error fetching date_fab:', err);
                document.getElementById('modalFirstMov').textContent = 'Erro';
            });
    }

    window.saveDateFab = function() {
        var dateFab = document.getElementById('modalDateFab').value;
        if (!dateFab) {
            Modal.alert('Por favor, selecione uma data.');
            return;
        }

        fetch('/api/custom_date_fab', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cod_item: currentItem.cod_item,
                cod_lote: currentItem.cod_lote,
                date_fab: dateFab
            })
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                window.location.reload();
            } else {
                Modal.alert(data.error || 'Erro ao salvar data de fabricação.');
            }
        })
        .catch(function(err) {
            console.error('Error saving date_fab:', err);
            Modal.alert('Erro ao salvar data de fabricação.');
        });
    };

    window.clearDateFab = function() {
        Modal.confirm(
            'Remover data customizada? Voltará a usar a data do primeiro movimento.',
            function() {
                fetch('/api/custom_date_fab?cod_item=' + encodeURIComponent(currentItem.cod_item) + '&cod_lote=' + encodeURIComponent(currentItem.cod_lote), {
                    method: 'DELETE'
                })
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        Modal.alert(data.error || 'Erro ao limpar data de fabricação.');
                    }
                })
                .catch(function(err) {
                    console.error('Error clearing date_fab:', err);
                    Modal.alert('Erro ao limpar data de fabricação.');
                });
            },
            { title: 'Limpar Override', confirmText: 'Limpar', danger: true }
        );
    };
})();
