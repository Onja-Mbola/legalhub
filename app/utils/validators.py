import re


def validate_password_strength(password: str) -> dict:
    score = 0
    feedback = []

    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Au moins 8 caractères requis")

    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("Au moins une majuscule requise")

    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Au moins une minuscule requise")

    if re.search(r'\d', password):
        score += 1
    else:
        feedback.append("Au moins un chiffre requis")

    if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        score += 1
    else:
        feedback.append("Au moins un caractère spécial recommandé")

    strength_levels = {
        0: "très faible",
        1: "très faible",
        2: "faible",
        3: "moyen",
        4: "fort",
        5: "très fort"
    }

    return {
        "score": score,
        "strength": strength_levels[score],
        "feedback": feedback,
        "is_valid": score >= 4
    }


def validate_email_format(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone_format(phone: str) -> bool:
    if not phone:
        return True

    pattern = r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$'
    return re.match(pattern, phone) is not None