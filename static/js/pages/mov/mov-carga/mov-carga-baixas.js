/**
 * Page: mov/mov-carga/mov-carga-baixas.j2
 * Carga reversal functionality
 */
(function() {
    'use strict';

    window.revertCarga = async function(idCarga) {
        var confirmation = confirm('Deseja reverter a carga ' + idCarga + '? Ela voltará a ficar disponível para separação.');
        if (!confirmation) return;

        try {
            var response = await fetch('/api/revert-carga/' + idCarga + '/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            var data = await response.json();

            if (data.success) {
                showToast('Carga revertida com sucesso!', 'success', 5);
                var row = document.querySelector('tr[data-id="' + idCarga + '"]');
                if (row) row.remove();

                var tbody = document.getElementById('baixasTable');
                if (tbody && tbody.children.length === 0) {
                    location.reload();
                }
            } else {
                showToast('Erro ao reverter: ' + data.error, 'error', 10);
            }
        } catch (error) {
            console.error('Erro ao reverter carga:', error);
            showToast('Erro ao reverter: ' + error, 'error', 10);
        }
    };
})();
