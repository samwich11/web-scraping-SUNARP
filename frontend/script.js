// =======================================
// Sistema de pestañas
// =======================================

const tabs = document.querySelectorAll(".tab");
const contents = document.querySelectorAll(".content");

tabs.forEach((tab) => {

    tab.addEventListener("click", () => {

        // Quitar la pestaña activa
        tabs.forEach((t) => {
            t.classList.remove("active");
        });

        // Ocultar todos los contenidos
        contents.forEach((content) => {
            content.classList.remove("active");
        });

        // Activar la pestaña seleccionada
        tab.classList.add("active");

        // Mostrar el contenido correspondiente
        const target = document.getElementById(tab.dataset.tab);

        if (target) {
            target.classList.add("active");
        }

    });

});


// =======================================
// Animación de los botones (prototipo)
// =======================================

const buttons = document.querySelectorAll(".buttons button, .upload-btn");

buttons.forEach((button) => {

    button.addEventListener("click", () => {

        button.style.transform = "scale(0.96)";

        setTimeout(() => {

            button.style.transform = "scale(1)";

        }, 120);

    });

});


// =======================================
// Simulación del área de carga de archivos
// (solo frontend, sin funcionalidad)
// =======================================

const uploadBox = document.querySelector(".upload-box");
const fileInput = document.querySelector('input[type="file"]');

if (uploadBox && fileInput) {

    // Abrir el selector al hacer clic
    uploadBox.addEventListener("click", (e) => {

        // Evita que el botón vuelva a disparar el evento
        if (e.target.tagName !== "BUTTON") {
            fileInput.click();
        }

    });

    // Botón "Seleccionar Archivo"
    const uploadButton = document.querySelector(".upload-btn");

    if (uploadButton) {

        uploadButton.addEventListener("click", (e) => {

            e.stopPropagation();
            fileInput.click();

        });

    }

    // Mostrar nombre del archivo seleccionado
    fileInput.addEventListener("change", () => {

        if (fileInput.files.length > 0) {

            const fileName = fileInput.files[0].name;

            const text = uploadBox.querySelector("p");

            text.textContent = `Archivo seleccionado: ${fileName}`;

        }

    });

    // Efecto Drag & Drop (solo visual)

    uploadBox.addEventListener("dragover", (e) => {

        e.preventDefault();

        uploadBox.classList.add("dragging");

    });

    uploadBox.addEventListener("dragleave", () => {

        uploadBox.classList.remove("dragging");

    });

    uploadBox.addEventListener("drop", (e) => {

        e.preventDefault();

        uploadBox.classList.remove("dragging");

        if (e.dataTransfer.files.length > 0) {

            const fileName = e.dataTransfer.files[0].name;

            const text = uploadBox.querySelector("p");

            text.textContent = `Archivo seleccionado: ${fileName}`;

        }

    });

}