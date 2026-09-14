(function () {
    "use strict";

    function initNavigation() {
        const navigation = document.querySelector(".navigation-bar");
        const toggle = document.querySelector(".navigation-toggle");

        if (!navigation || !toggle) return;

        toggle.addEventListener("click", function () {
            const isOpen = navigation.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", String(isOpen));
        });

        navigation.addEventListener("keydown", function (event) {
            if (event.key !== "Escape") return;

            navigation.classList.remove("is-open");
            toggle.setAttribute("aria-expanded", "false");
            toggle.focus();
        });

        window.addEventListener("resize", function () {
            if (window.innerWidth > 900) {
                navigation.classList.remove("is-open");
                toggle.setAttribute("aria-expanded", "false");
            }
        });
    }

    function dismissDropdown(control) {
        const dropdown = control && control.closest(".dropdown");
        if (!dropdown) return;

        dropdown.classList.add("is-dismissed");
        control.blur();

        function resetDismissedState() {
            dropdown.classList.remove("is-dismissed");
            dropdown.removeEventListener("pointerleave", resetDismissedState);
            dropdown.removeEventListener("focusin", resetDismissedState);
            document.removeEventListener("pointerdown", resetDismissedState);
        }

        dropdown.addEventListener("pointerleave", resetDismissedState);
        dropdown.addEventListener("focusin", resetDismissedState);
        document.addEventListener("pointerdown", resetDismissedState);
    }

    window.dismissDropdown = dismissDropdown;

    document.addEventListener("DOMContentLoaded", initNavigation);
})();
