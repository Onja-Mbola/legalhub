document.addEventListener('DOMContentLoaded', function() {
    const profileForm = document.getElementById('profileForm');
    const passwordForm = document.getElementById('passwordForm');
    const clarckForm = document.getElementById('clarckForm');

    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            if (!validateProfileForm()) {
                e.preventDefault();
            }
        });
    }

    if (passwordForm) {
        const newPasswordField = document.getElementById('new_password');
        const confirmPasswordField = document.getElementById('confirm_password');

        newPasswordField.addEventListener('input', checkPasswordStrength);
        confirmPasswordField.addEventListener('input', checkPasswordMatch);

        passwordForm.addEventListener('submit', function(e) {
            if (!validatePasswordForm()) {
                e.preventDefault();
            }
        });
    }

    if (clarckForm) {
        clarckForm.addEventListener('submit', function(e) {
            if (!validateClarckForm()) {
                e.preventDefault();
            }
        });
    }
});

function validateProfileForm() {
    const nom = document.getElementById('nom').value.trim();
    const email = document.getElementById('email').value.trim();

    if (nom.length < 2) {
        showError('Le nom doit contenir au moins 2 caractères');
        return false;
    }

    if (!isValidEmail(email)) {
        showError('Format d\'email invalide');
        return false;
    }

    return true;
}

function validatePasswordForm() {
    const currentPassword = document.getElementById('current_password').value;
    const newPassword = document.getElementById('new_password').value;
    const confirmPassword = document.getElementById('confirm_password').value;

    if (!currentPassword) {
        showError('Veuillez saisir votre mot de passe actuel');
        return false;
    }

    if (newPassword.length < 8) {
        showError('Le nouveau mot de passe doit contenir au moins 8 caractères');
        return false;
    }

    if (newPassword !== confirmPassword) {
        showError('Les mots de passe ne correspondent pas');
        return false;
    }

    return true;
}

function validateClarckForm() {
    const nom = document.getElementById('clarck_nom').value.trim();
    const email = document.getElementById('clarck_email').value.trim();

    if (nom.length < 2) {
        showError('Le nom du clarck doit contenir au moins 2 caractères');
        return false;
    }

    if (!isValidEmail(email)) {
        showError('Format d\'email invalide pour le clarck');
        return false;
    }

    return true;
}

function checkPasswordStrength() {
    const password = document.getElementById('new_password').value;
    const strengthBar = document.getElementById('passwordStrength');

    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) score++;

    strengthBar.className = 'password-strength';
    if (score < 3) {
        strengthBar.classList.add('strength-weak');
    } else if (score < 5) {
        strengthBar.classList.add('strength-medium');
    } else {
        strengthBar.classList.add('strength-strong');
    }
}

function checkPasswordMatch() {
    const newPassword = document.getElementById('new_password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    const confirmField = document.getElementById('confirm_password');

    if (confirmPassword && newPassword !== confirmPassword) {
        confirmField.classList.add('is-invalid');
    } else {
        confirmField.classList.remove('is-invalid');
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function showError(message) {
    let alertDiv = document.querySelector('.alert-danger');
    if (!alertDiv) {
        alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="fas fa-exclamation-circle me-2"></i>
            <span class="error-message">${message}</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.container-fluid').insertAdjacentElement('afterbegin', alertDiv);
    } else {
        alertDiv.querySelector('.error-message').textContent = message;
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
}