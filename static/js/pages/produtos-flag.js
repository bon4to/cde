/**
 * Page: produtos-flag.j2
 * Product visibility toggle functions
 */
(function() {
    'use strict';

    window.confirmAtivar = function(cod_item, checkbox) {
        if (confirm(`Você tem certeza que deseja ATIVAR o item ${cod_item}?`)) {
            window.location.href = "/produtos/toggle-perm/" + cod_item + "/" + 1;
        } else {
            checkbox.checked = true;
        }
    };

    window.confirmOcultar = function(cod_item, checkbox) {
        if (confirm(`Você tem certeza que deseja OCULTAR o item ${cod_item}?`)) {
            window.location.href = "/produtos/toggle-perm/" + cod_item + "/" + 0;
        } else {
            checkbox.checked = false;
        }
    };
})();
