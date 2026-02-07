/**
 * Page: admin/migrations.j2
 * Database migration management functions
 */
(function() {
    'use strict';

    window.runPending = function() {
        if (!confirm('Executar todas as migrações pendentes?')) return;

        fetch('/api/migrations/run', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert('Migrações executadas: ' + data.results.length);
                    location.reload();
                } else {
                    alert('Erro: ' + data.error);
                }
            });
    };

    window.rollback = function(name) {
        if (!confirm('Reverter migração ' + name + '?')) return;

        fetch('/api/migrations/rollback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert('Migração revertida');
                    location.reload();
                } else {
                    alert('Erro: ' + data.error);
                }
            });
    };
})();
