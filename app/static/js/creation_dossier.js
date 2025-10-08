console.log("Création dossier - Module chargé");
let currentStep = 1;
const totalSteps = 4;

document.addEventListener('DOMContentLoaded', () => {
    const typeAffaireSelect = document.getElementById('type_affaire');
    const sousTypeContainer = document.getElementById('sous_type_affaire_container');
    const sousTypeSelect = document.getElementById('sous_type_affaire');
    const form = document.getElementById('creationDossierForm');

    setTimeout(() => {
        document.querySelector('.card').style.opacity = '1';
    }, 100);

    function populateSousTypes(type) {
        let options = [];

        if (type === 'civil') {
            options = civilTypes;
        } else if (type === 'penal') {
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

        const submitBtn = document.getElementById('nextBtn');
        const originalHTML = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Enregistrement...';

        const files = document.getElementById('pieces_jointes').files;
        const dateValue = document.getElementById('date_creation').value;
        const formattedDate = dateValue;

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
                submitBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> Succès !';
                submitBtn.classList.remove('btn-primary');
                submitBtn.classList.add('btn-success');

                setTimeout(() => {
                    window.location.href = result.redirect_url;
                }, 500);
            } else {
                showNotification("Dossier enregistré avec succès !", "success");
                submitBtn.innerHTML = originalHTML;
                submitBtn.disabled = false;
            }
        } catch (error) {
            console.error("Erreur :", error);
            showNotification("Une erreur est survenue lors de l'enregistrement.", "error");
            submitBtn.innerHTML = originalHTML;
            submitBtn.disabled = false;
        }
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const now = new Date();
    const utcPlus3 = new Date(now.getTime() + (3 * 60 * 60 * 1000));
    const formatted = utcPlus3.toISOString().slice(0, 16);
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
    div.classList.add('border', 'rounded', 'p-3', 'mb-3', 'position-relative');
    div.style.transition = 'all 0.3s ease';
    div.dataset.index = index;

    let qualiteOptions = '<option value="">-- Sélectionner --</option>';
    if (Array.isArray(qualiteTypes)) {
        qualiteTypes.forEach(item => {
            qualiteOptions += `<option value="${item.id}">${item.valeur}</option>`;
        });
    }

    div.innerHTML = `
        <div class="position-absolute top-0 end-0 mt-2 me-2">
        </div>
        <div class="row g-3">
            <div class="col-md-6">
                <label class="form-label fw-semibold small">Nom complet</label>
                <input type="text" class="form-control" name="${prefix}[${index}][nom]" placeholder="Nom et prénom" required>
            </div>
            <div class="col-md-6">
                <label class="form-label fw-semibold small">Qualité</label>
                <select class="form-select" name="${prefix}[${index}][qualite]" required>
                    ${qualiteOptions}
                </select>
            </div>
            <div class="col-md-6">
                <label class="form-label fw-semibold small">Téléphone</label>
                <input type="tel" class="form-control" name="${prefix}[${index}][telephone]" placeholder="+261 34 12 345 67" required>
            </div>
            <div class="col-md-6">
                <label class="form-label fw-semibold small">Email</label>
                <input type="email" class="form-control" name="${prefix}[${index}][email]" placeholder="email@example.com" required>
            </div>
              <button type="button" class="btn btn-sm btn-outline-danger rounded-circle" onclick="removeContact(this)" style="width: 32px; height: 32px; padding: 0;">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    container.appendChild(div);

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

function addDemandeur() {
    createContactFields('demandeurs-container', 'demandeurs');
}

function addAdverse() {
    createContactFields('adverses-container', 'adverses');
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
    const inputs = stepElement.querySelectorAll("input[required], select[required], textarea[required]");
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
        showNotification("Veuillez remplir tous les champs obligatoires", "warning");
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

const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
    .is-invalid {
        border-color: #dc3545 !important;
        background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12' width='12' height='12' fill='none' stroke='%23dc3545'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath stroke-linejoin='round' d='M5.8 3.6h.4L6 6.5z'/%3e%3ccircle cx='6' cy='8.2' r='.6' fill='%23dc3545' stroke='none'/%3e%3c/svg%3e");
        background-repeat: no-repeat;
        background-position: right calc(0.375em + 0.1875rem) center;
        background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
        padding-right: calc(1.5em + 0.75rem);
    }
    
    .is-valid {
        border-color: #10b981 !important;
        background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3e%3cpath fill='%2310b981' d='M2.3 6.73L.6 4.53c-.4-1.04.46-1.4 1.1-.8l1.1 1.4 3.4-3.8c.6-.63 1.6-.27 1.2.7l-4 4.6c-.43.5-.8.4-1.1.1z'/%3e%3c/svg%3e");
        background-repeat: no-repeat;
        background-position: right calc(0.375em + 0.1875rem) center;
        background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
        padding-right: calc(1.5em + 0.75rem);
    }
`;
document.head.appendChild(style);

showStep(currentStep);