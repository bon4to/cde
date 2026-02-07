/**
 * Page: cde/db-cfg/data-fetcher.j2
 * SQL console with CodeMirror integration
 */
(function() {
    'use strict';

    var currentQuery = "";
    var editor = null;

    // Initialize CodeMirror when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        var textarea = document.getElementById('sql_query');
        if (!textarea) return;

        editor = CodeMirror.fromTextArea(textarea, {
            lineNumbers: true,
            mode: "text/x-sql",
            theme: "material-darker"
        });

        // Form submit handler
        var formField = document.getElementById("query-field");
        if (formField) {
            formField.addEventListener("submit", function() {
                var submitBtn = document.getElementById("submitform");
                if (submitBtn) submitBtn.disabled = true;
            });
        }
    });

    window.restoreLastQuery = function() {
        var undoButton = document.getElementById("undoButton");
        if (undoButton) undoButton.style.display = "none";
        if (editor) editor.setValue(currentQuery);
    };

    window.addTableToQuery = function(table) {
        var selSchema = document.getElementById("sel_schema");
        var undoButton = document.getElementById("undoButton");

        if (undoButton) undoButton.style.display = "block";
        if (editor) currentQuery = editor.getValue();

        var schema = "";
        if (selSchema && (selSchema.value === "ODBC-DRIVER" || selSchema.value === "API")) {
            schema = "DB2ADMIN.";
        }

        if (editor) editor.setValue("SELECT * FROM " + schema + table + ";");
    };
})();
