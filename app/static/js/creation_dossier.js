console.log("onkl");

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

        const dossierData = {
            nom_dossier: document.getElementById('nom_dossier').value,
            type_affaire: typeAffaireSelect.value,
            sous_type_affaire: document.getElementById('sous_type_affaire').value,
            urgence: document.getElementById('urgence').value,
            juridiction: document.getElementById('juridiction').value,
            tribunal: document.getElementById('tribunal').value,
            avocat_responsable: document.getElementById('avocat_responsable').value,
            avocat_adverse: document.getElementById('avocat_adverse').value,
            date_creation: document.getElementById('date_creation').value,
            commentaire: document.getElementById('commentaire').value,
            client: {
                adresse_client: document.getElementById('adresse_client').value,
                role_client : document.getElementById('role_client').value,
                demandeurs: collectContacts('demandeurs-container'),
                adverses: collectContacts('adverses-container')
            }
        };

        console.log(dossierData);

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

function collectContacts(containerId) {
    const container = document.getElementById(containerId);
    const contacts = [];
    container.querySelectorAll('div.border').forEach(div => {
        const index = div.dataset.index;
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
            <label class="form-label" for="${prefix}_nom_${index}">Nom</label>
            <input type="text" class="form-control" name="${prefix}[${index}][nom]" required>
        </div>
        <div class="mb-3">
            <label class="form-label" for="${prefix}_qualite_${index}">Qualité</label>
            <select class="form-select" name="${prefix}[${index}][qualite]" required>
                ${qualiteOptions}
            </select>
        </div>
        <div class="mb-3">
            <label class="form-label" for="${prefix}_tel_${index}">Numéro de téléphone</label>
            <input type="tel" class="form-control" name="${prefix}[${index}][telephone]" placeholder="+261 34 12 345 67" required>
        </div>
        <div class="mb-3">
            <label class="form-label" for="${prefix}_email_${index}">Email</label>
            <input type="email" class="form-control" name="${prefix}[${index}][email]" required>
        </div>
        <button type="button" class="btn btn-danger btn-sm" onclick="removeContact(this)">Supprimer</button>
    `;

    container.appendChild(div);
}

function addDemandeur() { createContactFields('demandeurs-container', 'demandeurs'); }
function addAdverse() { createContactFields('adverses-container', 'adverses'); }
function removeContact(button) { const div = button.closest('div.border'); if (div) div.remove(); }
