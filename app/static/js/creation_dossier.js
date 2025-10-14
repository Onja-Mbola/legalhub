let currentStep = 1;
const totalSteps = 4;
let selectedClient = null;

document.addEventListener('DOMContentLoaded', () => {
    initForm();
    setupClientSearch();
    setupTypeAffaire();
});

function initForm() {
    const now = new Date();
    const utcPlus3 = new Date(now.getTime() + (3 * 60 * 60 * 1000));
    const formatted = utcPlus3.toISOString().slice(0, 16);
    document.getElementById("date_creation").value = formatted;

    // Setup form submission
    document.getElementById('creationDossierForm').addEventListener('submit', handleSubmit);
}

// ============= GESTION DES MODES =============
function selectMode(mode) {
    document.querySelectorAll('.mode-card').forEach(card => {
        card.classList.remove('active');
    });
    document.querySelector(`[data-mode="${mode}"]`).classList.add('active');

    document.getElementById('mode_creation').value = mode;

    if (mode === 'client_existant') {
        document.getElementById('client-existant-container').classList.remove('d-none');
        document.getElementById('nouveau-client-container').classList.add('d-none');
    } else {
        document.getElementById('client-existant-container').classList.add('d-none');
        document.getElementById('nouveau-client-container').classList.remove('d-none');
    }

    selectedClient = null;
}

// ============= RECHERCHE CLIENT =============
function setupClientSearch() {
    const searchInput = document.getElementById('client_search');
    const suggestionsDiv = document.getElementById('client_suggestions');

    let debounceTimer;

    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const query = e.target.value.trim();

        if (query.length < 2) {
            suggestionsDiv.style.display = 'none';
            return;
        }

        debounceTimer = setTimeout(() => {
            searchClients(query);
        }, 300);
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.client-search-container')) {
            suggestionsDiv.style.display = 'none';
        }
    });
}

async function searchClients(query) {
    const suggestionsDiv = document.getElementById('client_suggestions');

    try {
        const response = await fetch(`/api/clients/search?q=${encodeURIComponent(query)}`);
        const clients = await response.json();

        if (clients.length === 0) {
            suggestionsDiv.innerHTML = `
                <div class="p-3 text-muted text-center">
                    <i class="fas fa-search mb-2"></i>
                    <p class="mb-0">Aucun client trouvé</p>
                </div>
            `;
        } else {
            suggestionsDiv.innerHTML = clients.map(client => `
                <div class="client-suggestion-item" onclick='selectClient(${JSON.stringify(client)})'>
                    <div class="fw-bold">${client.nom}</div>
                    <div class="small text-muted">
                        ${client.email || ''} ${client.telephone ? '• ' + client.telephone : ''}
                    </div>
                    ${client.adresse ? `<div class="small text-muted">${client.adresse}</div>` : ''}
                </div>
            `).join('');
        }

        suggestionsDiv.style.display = 'block';
    } catch (error) {
        console.error('Erreur recherche clients:', error);
    }
}

function selectClient(client) {
    selectedClient = client;

    document.getElementById('client_suggestions').style.display = 'none';

    document.getElementById('client_search').value = '';

    document.getElementById('client_id').value = client.id;

    const detailsDiv = document.getElementById('selected_client_details');
    detailsDiv.innerHTML = `
        <div class="mb-2"><strong>${client.nom}</strong></div>
        ${client.email ? `<div class="small"><i class="fas fa-envelope me-2"></i>${client.email}</div>` : ''}
        ${client.telephone ? `<div class="small"><i class="fas fa-phone me-2"></i>${client.telephone}</div>` : ''}
        ${client.adresse ? `<div class="small"><i class="fas fa-map-marker-alt me-2"></i>${client.adresse}</div>` : ''}
    `;

    document.getElementById('client_selected_info').style.display = 'block';
}

function clearClientSelection() {
    selectedClient = null;
    document.getElementById('client_id').value = '';
    document.getElementById('client_selected_info').style.display = 'none';
    document.getElementById('client_search').value = '';
}

// ============= TYPE AFFAIRE =============
function setupTypeAffaire() {
    const typeAffaireSelect = document.getElementById('type_affaire');
    const sousTypeContainer = document.getElementById('sous_type_affaire_container');
    const sousTypeSelect = document.getElementById('sous_type_affaire');

    typeAffaireSelect.addEventListener('change', () => {
        const selectedText = typeAffaireSelect.options[typeAffaireSelect.selectedIndex].text.toLowerCase();

        let options = [];
        if (selectedText === 'civil') {
            options = civilTypes;
        } else if (selectedText === 'penal') {
            options = penalTypes;
        }

        if (options.length > 0) {
            sousTypeContainer.style.display = 'block';
            sousTypeSelect.innerHTML = '<option value="">Sélectionner un sous-type</option>';

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
    });
}

// ============= DEMANDEURS / ADVERSES =============
function addDemandeur() {
    createContactFields('demandeurs-container', 'demandeurs');
}

function addAdverse() {
    createContactFields('adverses-container', 'adverses');
}

function createContactFields(containerId, prefix) {
    const container = document.getElementById(containerId);
    const index = container.children.length;

    const div = document.createElement('div');
    div.classList.add('border', 'rounded', 'p-3', 'mb-3', 'position-relative');
    div.dataset.index = index;

    let qualiteOptions = '<option value="">-- Sélectionner --</option>';
    if (Array.isArray(qualiteTypes)) {
        qualiteTypes.forEach(item => {
            qualiteOptions += `<option value="${item.id}">${item.valeur}</option>`;
        });
    }

    div.innerHTML = `
        <div class="row g-3">
            <div class="col-md-6">
                <label class="form-label fw-semibold small">Nom complet <span class="text-danger">*</span></label>
                <input type="text" class="form-control" name="${prefix}[${index}][nom]" placeholder="Nom et prénom" required>
            </div>
            <div class="col-md-6">
                <label class="form-label fw-semibold small">Qualité <span class="text-danger">*</span></label>
                <select class="form-select" name="${prefix}[${index}][qualite]" required>
                    ${qualiteOptions}
                </select>
            </div>
            <div class="col-md-6">
                <label class="form-label fw-semibold small">Téléphone</label>
                <input type="tel" class="form-control" name="${prefix}[${index}][telephone]" placeholder="+261 34 12 345 67">
            </div>
            <div class="col-md-6">
                <label class="form-label fw-semibold small">Email</label>
                <input type="email" class="form-control" name="${prefix}[${index}][email]" placeholder="email@example.com">
            </div>
            <div class="col-12">
                <label class="form-label fw-semibold small">Adresse</label>
                <input type="text" class="form-control" name="${prefix}[${index}][adresse]" placeholder="Adresse complète">
            </div>
            ${prefix === 'adverses' ? `
            <div class="col-12">
                <label class="form-label fw-semibold small">Avocat adverse</label>
                <input type="text" class="form-control" name="${prefix}[${index}][avocat]" placeholder="Nom de l'avocat">
            </div>
            ` : ''}
            <div class="col-12 text-end">
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeContact(this)">
                    <i class="fas fa-trash me-1"></i> Retirer
                </button>
            </div>
        </div>
    `;

    container.appendChild(div);

    // Animation
    setTimeout(() => {
        div.style.opacity = '0';
        div.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            div.style.transition = 'all 0.3s ease';
            div.style.opacity = '1';
            div.style.transform = 'translateY(0)';
        }, 10);
    }, 0);
}

function removeContact(button) {
    const div = button.closest('div.border');
    if (div) {
        div.style.opacity = '0';
        div.style.transform = 'translateX(20px)';
        setTimeout(() => {
            div.remove();
        }, 300);
    }
}

function collectContacts(containerId) {
    const container = document.getElementById(containerId);
    const contacts = [];

    container.querySelectorAll('div.border').forEach(div => {
        const prefix = containerId.replace('-container', '');
        const index = div.dataset.index;

        const contact = {
            nom: div.querySelector(`[name="${prefix}[${index}][nom]"]`).value,
            qualite: parseInt(div.querySelector(`[name="${prefix}[${index}][qualite]"]`).value),
            telephone: div.querySelector(`[name="${prefix}[${index}][telephone]"]`)?.value || null,
            email: div.querySelector(`[name="${prefix}[${index}][email]"]`)?.value || null,
            adresse: div.querySelector(`[name="${prefix}[${index}][adresse]"]`)?.value || null
        };

        // Pour adverses, ajouter l'avocat
        if (prefix === 'adverses') {
            contact.avocat = div.querySelector(`[name="${prefix}[${index}][avocat]"]`)?.value || null;
        }

        contacts.push(contact);
    });

    return contacts;
}

// ============= NAVIGATION ÉTAPES =============
function showStep(step) {
    document.querySelectorAll(".wizard-step").forEach((el, index) => {
        el.classList.toggle("d-none", index !== step - 1);
    });

    document.getElementById("progressBar").style.width = `${(step / totalSteps) * 100}%`;
    updateStepIndicators(step);

    document.getElementById("prevBtn").disabled = step === 1;

    const nextBtn = document.getElementById("nextBtn");
    if (step === totalSteps) {
        nextBtn.innerHTML = '<i class="fas fa-save me-2"></i> Enregistrer le dossier';
        nextBtn.classList.remove('btn-primary');
        nextBtn.classList.add('btn-success');
    } else {
        nextBtn.innerHTML = 'Suivant <i class="fas fa-arrow-right ms-2"></i>';
        nextBtn.classList.remove('btn-success');
        nextBtn.classList.add('btn-primary');
    }
}

function updateStepIndicators(step) {
    document.querySelectorAll('.step-indicator').forEach((indicator, index) => {
        indicator.classList.remove('active', 'completed');

        if (index + 1 === step) {
            indicator.classList.add('active');
        } else if (index + 1 < step) {
            indicator.classList.add('completed');
        }
    });

    document.getElementById('stepCounter').textContent = step;
}

function validateStep(step) {
    const stepElement = document.getElementById(`step-${step}`);

    // Validation spéciale pour step 1 (mode + client)
    if (step === 1) {
        const mode = document.getElementById('mode_creation').value;

        if (mode === 'client_existant') {
            const clientId = document.getElementById('client_id').value;
            if (!clientId) {
                showNotification("Veuillez sélectionner un client", "warning");
                return false;
            }
        } else if (mode === 'nouveau') {
            const nomClient = document.getElementById('nouveau_client_nom').value.trim();
            if (!nomClient) {
                showNotification("Veuillez renseigner le nom du client", "warning");
                return false;
            }
        }
        return true;
    }

    // Validation normale pour les autres steps
    const inputs = stepElement.querySelectorAll("input[required], select[required]");
    let valid = true;
    let firstInvalid = null;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add("is-invalid");
            if (!firstInvalid) firstInvalid = input;
            valid = false;

            input.style.animation = 'shake 0.5s';
            setTimeout(() => {
                input.style.animation = '';
            }, 500);
        } else {
            input.classList.remove("is-invalid");
            input.classList.add("is-valid");
        }
    });

    if (firstInvalid) {
        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
        firstInvalid.focus();
    }

    return valid;
}

function changeStep(n) {
    if (n === 1 && !validateStep(currentStep)) {
        return;
    }

    if (n === 1 && currentStep === totalSteps) {
        document.getElementById("creationDossierForm").dispatchEvent(new Event('submit'));
        return;
    }

    currentStep += n;
    if (currentStep < 1) currentStep = 1;
    if (currentStep > totalSteps) currentStep = totalSteps;

    window.scrollTo({ top: 0, behavior: 'smooth' });
    showStep(currentStep);
}

// ============= SOUMISSION FORMULAIRE =============
async function handleSubmit(e) {
    e.preventDefault();

    const submitBtn = document.getElementById('nextBtn');
    const originalHTML = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Enregistrement...';

    const mode = document.getElementById('mode_creation').value;
    const files = document.getElementById('pieces_jointes').files;

    const dossierData = {
        nom_dossier: document.getElementById('nom_dossier').value,
        type_affaire: parseInt(document.getElementById('type_affaire').value),
        sous_type_affaire: document.getElementById('sous_type_affaire').value ? parseInt(document.getElementById('sous_type_affaire').value) : null,
        urgence: document.getElementById('urgence').value ? parseInt(document.getElementById('urgence').value) : null,
        juridiction: document.getElementById('juridiction').value || null,
        tribunal: document.getElementById('tribunal').value || null,
        avocat_responsable_user: document.getElementById('avocat_responsable').value,
        date_creation: document.getElementById('date_creation').value,
        commentaire: document.getElementById('commentaire').value || null,
        consentement_rgpd: document.getElementById('consentement_rgpd').checked,
        mode_creation: mode,
        demandeurs: collectContacts('demandeurs-container'),
        adverses: collectContacts('adverses-container')
    };

    // Ajouter client selon le mode
    if (mode === 'client_existant') {
        dossierData.client_id = parseInt(document.getElementById('client_id').value);
    } else if (mode === 'nouveau') {
        const nomClient = document.getElementById('nouveau_client_nom').value.trim();
        if (nomClient) {
            dossierData.nouveau_client = {
                nom: nomClient,
                email: document.getElementById('nouveau_client_email').value || null,
                telephone: document.getElementById('nouveau_client_telephone').value || null,
                adresse: document.getElementById('nouveau_client_adresse').value || null,
                type_client: document.getElementById('nouveau_client_type').value
            };
        }
    }

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
            submitBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> Succès !';
            submitBtn.classList.remove('btn-success');
            submitBtn.classList.add('btn-success');

            setTimeout(() => {
                window.location.href = result.redirect_url;
            }, 500);
        }
    } catch (error) {
        console.error("Erreur :", error);
        showNotification("Une erreur est survenue lors de l'enregistrement.", "error");
        submitBtn.innerHTML = originalHTML;
        submitBtn.disabled = false;
    }
}

// ============= UTILITAIRES =============
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' || type === 'danger' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
            <span>${message}</span>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 300);
    }, 3000);
}

// Animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
    .is-invalid {
        border-color: #dc3545 !important;
    }
    
    .is-valid {
        border-color: #10b981 !important;
    }
`;
document.head.appendChild(style);

showStep(currentStep);