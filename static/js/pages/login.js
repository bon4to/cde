/**
 * Page: login.j2
 * Disables submit button on form submission to prevent double-submit
 */
(function() {
    'use strict';

    document.getElementById("form-field").addEventListener("submit", function() {
        document.getElementById("submitform").disabled = true;
    });
})();
