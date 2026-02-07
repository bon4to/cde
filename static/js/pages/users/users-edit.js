/**
 * Page: users/users-edit.j2
 * User permission and password management
 */
(function() {
    'use strict';

    var currentUserId = null;

    window.redefinePassword = function(idUser) {
        currentUserId = idUser;
        document.getElementById('newPassword').value = '';
        document.getElementById('confirmPassword').value = '';
        Modal.open('passwordModal');
    };

    window.submitPassword = function() {
        var newPassword = document.getElementById('newPassword').value;
        var confirmPassword = document.getElementById('confirmPassword').value;

        if (newPassword.length < 6) {
            Modal.alert('A senha deve ter no mínimo 6 caracteres.');
            return;
        }

        if (newPassword !== confirmPassword) {
            Modal.alert('As senhas não coincidem.');
            return;
        }

        fetch('/api/users/set-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id_user: currentUserId,
                password: newPassword
            })
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                Modal.close('passwordModal');
                Modal.alert('Senha redefinida com sucesso!');
            } else {
                Modal.alert(data.error || 'Erro ao redefinir senha.');
            }
        })
        .catch(function(err) {
            console.error('Error:', err);
            Modal.alert('Erro ao redefinir senha.');
        });
    };

    window.confirmRemover = function(idUser, idPerm, checkbox) {
        Modal.confirm("Você tem certeza que deseja remover esta permissão?", function() {
            window.location.href = "/users/remove-perm/" + idUser + "/" + idPerm;
        }, { title: 'Remover Permissão', confirmText: 'Remover', danger: true });

        checkbox.checked = true;
    };

    window.confirmAdicionar = function(idUser, idPerm, checkbox) {
        Modal.confirm("Você tem certeza que deseja adicionar esta permissão?", function() {
            window.location.href = "/users/add-perm/" + idUser + "/" + idPerm;
        }, { title: 'Adicionar Permissão', confirmText: 'Adicionar' });

        checkbox.checked = false;
    };
})();
