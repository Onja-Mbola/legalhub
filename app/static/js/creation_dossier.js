console.log("on");

document.addEventListener('DOMContentLoaded', () => {
    const typeAffaireSelect = document.getElementById('type_affaire');
    const sousTypeContainer = document.getElementById('sous_type_affaire_container');
    const sousTypeSelect = document.getElementById('sous_type_affaire');

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
        const selectedType = typeAffaireSelect.value;
        populateSousTypes(selectedType);
    });
});


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
            <input type="text" class="form-control" id="${prefix}_nom_${index}" name="${prefix}[${index}][nom]" required>
        </div>
        <div class="mb-3">
            <label class="form-label" for="${prefix}_qualite_${index}">Qualité</label>
            <select class="form-select" id="${prefix}_qualite_${index}" name="${prefix}[${index}][qualite]" required>
                ${qualiteOptions}
            </select>
        </div>
        <div class="mb-3">
            <label class="form-label" for="${prefix}_tel_${index}">Numéro de téléphone</label>
            <input type="tel" class="form-control" id="${prefix}_tel_${index}" name="${prefix}[${index}][telephone]" pattern="^\\+?[0-9\\-\\s]{7,15}$" placeholder="+261 34 12 345 67" required>
        </div>
        <div class="mb-3">
            <label class="form-label" for="${prefix}_email_${index}">Email</label>
            <input type="email" class="form-control" id="${prefix}_email_${index}" name="${prefix}[${index}][email]" required>
        </div>
        <button type="button" class="btn btn-danger btn-sm" onclick="removeContact(this)">Supprimer</button>
    `;

    container.appendChild(div);
}

function addDemandeur() {
    createContactFields('demandeurs-container', 'demandeurs');
}

function addAdverse() {
    createContactFields('adverses-container', 'adverses');
}

function removeContact(button) {
    const div = button.closest('div.border');
    if (div) div.remove();
}
