/**
 * Page: users/users.j2
 * User list navigation
 */
(function() {
    'use strict';

    window.redirectToEdit = function(idUser) {
        window.location.href = "/users/edit?id_user=" + idUser;
    };
})();
