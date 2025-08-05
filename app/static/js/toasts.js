document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".toast").forEach(function (toastEl) {
        new bootstrap.Toast(toastEl).show();
    });

    const params = new URLSearchParams(window.location.search);
    if (params.has("success")) {
        const toast = document.getElementById("toastSuccess");
        if (toast) new bootstrap.Toast(toast).show();
    }
    if (params.has("updated")) {
        const toast = document.getElementById("toastUpdated");
        if (toast) new bootstrap.Toast(toast).show();
    }
});
