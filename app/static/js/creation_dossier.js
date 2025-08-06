console.log("onkl");
let currentStep = 1;
const totalSteps = 4;

document.addEventListener('DOMContentLoaded', () => {
    const typeAffaireSelect = document.getElementById('type_affaire');
    const sousTypeContainer = document.getElementById('sous_type_affaire_container');
    const sousTypeSelect = document.getElementById('sous_type_affaire');
    const form = document.getElementById('creationDossierForm');

    function populateSousTypes(type) {
        let options = [];

        if (type === 'civil') {
            options = civilTypes;
        } else if (type === 'penal') {
            options = penalTypes;
        }

        if (options.length > 0) {
            sousTypeContainer.style.display = 'block';
            sousTypeSelect.innerHTML = '';

            options.forEach(item => {
                const opt = document.createElement('option');
                opt.value = item.id;
                opt.textContent = item.valeur;
                sousTypeSelect.appendChild(opt);
            });
        } else {
            sousTypeContainer.style.display = 'none';
            sousTypeSelect.innerHTML = '';
        }
    }

    typeAffaireSelect.addEventListener('change', () => {
        const selectedText = typeAffaireSelect.options[typeAffaireSelect.selectedIndex].text.toLowerCase();
        if (selectedText === 'civil') {
            populateSousTypes('civil');
        } else if (selectedText === 'penal') {
            populateSousTypes('penal');
        } else {
            populateSousTypes('');
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const files = document.getElementById('pieces_jointes').files;
        const dateValue = document.getElementById('date_creation').value;
        const formattedDate = dateValue ;

        const dossierData = {
            nom_dossier: document.getElementById('nom_dossier').value,
            type_affaire: typeAffaireSelect.value,
            sous_type_affaire: document.getElementById('sous_type_affaire').value || null,
            urgence: document.getElementById('urgence').value || null,
            juridiction: document.getElementById('juridiction').value || null,
            tribunal: document.getElementById('tribunal').value || null,
            avocat_responsable: document.getElementById('avocat_responsable').value,
            avocat_adverse: document.getElementById('avocat_adverse').value || null,
            date_creation: formattedDate,
            commentaire: document.getElementById('commentaire').value || null,
            client: {
                adresse_client: document.getElementById('adresse_client').value,
                role_client: document.getElementById('role_client').value || null,
                demandeurs: collectContacts('demandeurs-container') || null,
                adverses: collectContacts('adverses-container') || null
            }
        };

        console.log("Valeur envoyée pour date_creation :", dossierData.date_creation);

        const formData = new FormData();
        formData.append("dossier_data", JSON.stringify(dossierData));
        for (let file of files) {
            formData.append("files", file);
        }

        try {
            const response = await fetch("/dossiers/nouveau", {
                method: "POST",
                body: formData
            });

            const result = await response.json();
            if (result.redirect_url) {
                // console.log("Valeur envoyée pour date_creation :", dossierData.date_creation);
                // console.log("Valeur envoyée pour date_creation :", dossierData);
                window.location.href = result.redirect_url;
            } else {
                alert("Dossier enregistré avec succès !");
            }
        } catch (error) {
            console.error("Erreur :", error);
            alert("Une erreur est survenue lors de l'enregistrement.");
        }
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const now = new Date();
    const utcPlus3 = new Date(now.getTime() + (3 * 60 * 60 * 1000));
    const formatted = utcPlus3.toISOString().slice(0,16);
    document.getElementById("date_creation").value = formatted;
});

function collectContacts(containerId) {
    const container = document.getElementById(containerId);
    const contacts = [];
    container.querySelectorAll('div.border').forEach(div => {
        contacts.push({
            nom: div.querySelector(`[name^="${containerId.slice(0, -10)}"][name$="[nom]"]`).value,
            qualite: div.querySelector(`[name^="${containerId.slice(0, -10)}"][name$="[qualite]"]`).value,
            telephone: div.querySelector(`[name^="${containerId.slice(0, -10)}"][name$="[telephone]"]`).value,
            email: div.querySelector(`[name^="${containerId.slice(0, -10)}"][name$="[email]"]`).value
        });
    });
    return contacts;
}

function createContactFields(containerId, prefix) {
    const container = document.getElementById(containerId);
    const index = container.children.length;

    const div = document.createElement('div');
    div.classList.add('border', 'p-3', 'mb-3', 'rounded', 'w-100');
    div.dataset.index = index;

    let qualiteOptions = '<option value="">-- Sélectionner --</option>';
    if (Array.isArray(qualiteTypes)) {
        qualiteTypes.forEach(item => {
            qualiteOptions += `<option value="${item.id}">${item.valeur}</option>`;
        });
    }

    div.innerHTML = `
        <div class="mb-3">
            <label class="form-label">Nom</label>
            <input type="text" class="form-control" name="${prefix}[${index}][nom]" required>
        </div>
        <div class="mb-3">
            <label class="form-label">Qualité</label>
            <select class="form-select" name="${prefix}[${index}][qualite]" required>
                ${qualiteOptions}
            </select>
        </div>
        <div class="mb-3">
            <label class="form-label">Numéro de téléphone</label>
            <input type="tel" class="form-control" name="${prefix}[${index}][telephone]" placeholder="+261 34 12 345 67" required>
        </div>
        <div class="mb-3">
            <label class="form-label">Email</label>
            <input type="email" class="form-control" name="${prefix}[${index}][email]" required>
        </div>
        <button type="button" class="btn btn-danger btn-sm" onclick="removeContact(this)">Supprimer</button>
    `;

    container.appendChild(div);
}

function addDemandeur() { createContactFields('demandeurs-container', 'demandeurs'); }
function addAdverse() { createContactFields('adverses-container', 'adverses'); }
function removeContact(button) {
    const div = button.closest('div.border');
    if (div) div.remove();
}

function showStep(step) {
    document.querySelectorAll(".wizard-step").forEach((el, index) => {
        el.classList.toggle("d-none", index !== step - 1);
    });

    document.getElementById("progressBar").style.width = `${(step / totalSteps) * 100}%`;

    document.getElementById("prevBtn").disabled = step === 1;
    document.getElementById("nextBtn").innerHTML =
        step === totalSteps
            ? '<i class="fas fa-save me-2"></i> Enregistrer'
            : 'Suivant <i class="fas fa-arrow-right ms-2"></i>';
}

function validateStep(step) {
    const stepElement = document.getElementById(`step-${step}`);
    const inputs = stepElement.querySelectorAll("input, select, textarea");
    let valid = true;

    inputs.forEach(input => {
        if (input.hasAttribute("required") && !input.value.trim()) {
            input.classList.add("is-invalid");
            valid = false;
        } else {
            input.classList.remove("is-invalid");
        }
    });

    return valid;
}

function changeStep(n) {
    if (n === 1 && !validateStep(currentStep)) return;

    if (n === 1 && currentStep === totalSteps) {
        document.getElementById("creationDossierForm").dispatchEvent(new Event('submit'));
        return;
    }

    currentStep += n;
    if (currentStep < 1) currentStep = 1;
    if (currentStep > totalSteps) currentStep = totalSteps;
    showStep(currentStep);
}

showStep(currentStep);
