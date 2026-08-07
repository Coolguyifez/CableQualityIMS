document.addEventListener("DOMContentLoaded", () => {

    const sidebar = document.querySelector(".sidebar");
    const toggle = document.querySelector("#menu-toggle");
    const overlay = document.querySelector(".sidebar-overlay");

    if (!toggle) return;

    toggle.addEventListener("click", () => {

        sidebar.classList.toggle("active");

        overlay.classList.toggle("show");

    });

    overlay.addEventListener("click", () => {

        sidebar.classList.remove("active");

        overlay.classList.remove("show");

    });

    document.querySelectorAll(".sidebar a").forEach(link => {

        link.addEventListener("click", () => {

            if (window.innerWidth <= 991) {

                sidebar.classList.remove("active");

                overlay.classList.remove("show");

            }

        });

    });

});