import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from starlette.templating import Jinja2Templates

from app.automatisation.celery_app import celery_app

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("SMTP_USERNAME"),
    MAIL_PASSWORD=os.getenv("SMTP_PASSWORD"),
    MAIL_FROM=os.getenv("FROM_EMAIL"),
    MAIL_PORT=int(os.getenv("SMTP_PORT", 587)),
    MAIL_SERVER=os.getenv("SMTP_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)
load_dotenv()

ENV = os.getenv("ENV", "development")

CABINET_TELEPHONE = os.getenv("CABINET_TELEPHONE", "+XXX XX XX XX XX")
CABINET_ADRESSE = os.getenv("CABINET_ADRESSE", "Adresse non définie")
CABINET_NOM = os.getenv("CABINET_NOM", "Cabinet d'avocat")
NOM_AVOCAT = os.getenv("NOM_AVOCAT", "Avocat")
MAIL_CABINET = os.getenv("MAIL_CABINET", "contact@cabinet.com")
IBAN = os.getenv("IBAN", "FR76 XXXX XXXX XXXX XXXX XXXX XXX")
BIC = os.getenv("BIC", "XXXXXXXXX")
NOM_MOBILE = os.getenv("NOM_MOBILE", "XXXXXXXXX")
NUMERO_MOBILE = os.getenv("NUMERO_MOBILE", "XXXXXXXXX")

templates = Jinja2Templates(directory="app/templates")


async def send_activation_email(email: EmailStr, token: str):
    if ENV == "production":
        activation_link = f"https://legalhub-2.onrender.com/activate?token={token}"
    else:
        activation_link = f"https://localhost:8000/activate?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px 20px;
            }}
            .email-wrapper {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                color: #ffffff;
                font-size: 28px;
                font-weight: 600;
                margin: 0;
                letter-spacing: 0.5px;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .welcome-text {{
                font-size: 18px;
                color: #2d3748;
                margin-bottom: 20px;
                font-weight: 500;
            }}
            .message-text {{
                font-size: 15px;
                color: #4a5568;
                line-height: 1.8;
                margin-bottom: 15px;
            }}
            .button-container {{
                text-align: center;
                margin: 35px 0;
            }}
            .activate-button {{
                display: inline-block;
                padding: 16px 40px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #ffffff;
                text-decoration: none;
                border-radius: 50px;
                font-size: 16px;
                font-weight: 600;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                transition: transform 0.2s;
            }}
            .activate-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
            }}
            .info-box {{
                background-color: #f7fafc;
                border-left: 4px solid #667eea;
                padding: 20px;
                margin: 25px 0;
                border-radius: 8px;
            }}
            .info-box p {{
                font-size: 15px;
                color: #2d3748;
                margin: 0;
            }}
            .info-box strong {{
                color: #667eea;
                font-size: 16px;
            }}
            .divider {{
                height: 1px;
                background: linear-gradient(to right, transparent, #e2e8f0, transparent);
                margin: 30px 0;
            }}
            .footer {{
                background-color: #f7fafc;
                padding: 30px;
                text-align: center;
            }}
            .footer-text {{
                font-size: 13px;
                color: #718096;
                margin-bottom: 8px;
            }}
            .footer-brand {{
                font-size: 14px;
                color: #667eea;
                font-weight: 600;
            }}
            @media only screen and (max-width: 600px) {{
                .header h1 {{
                    font-size: 24px;
                }}
                .content {{
                    padding: 30px 20px;
                }}
                .activate-button {{
                    padding: 14px 30px;
                    font-size: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <h1>🏛️ LegalHub</h1>
            </div>
            <div class="content">
                <p class="welcome-text">Bonjour et bienvenue ! 👋</p>
                <p class="message-text">
                    Nous sommes ravis de vous accueillir sur LegalHub. Votre inscription a été effectuée avec succès.
                </p>
                <p class="message-text">
                    Pour commencer à utiliser votre compte, veuillez activer celui-ci en cliquant sur le bouton ci-dessous :
                </p>

                <div class="button-container">
                    <a href="{activation_link}" class="activate-button">✓ Activer mon compte</a>
                </div>

                <div class="info-box">
                    <p><strong>🔑 Mot de passe par défaut :</strong> 123456</p>
                    <p style="margin-top: 8px; font-size: 13px; color: #718096;">
                        Nous vous recommandons fortement de changer ce mot de passe dès votre première connexion.
                    </p>
                </div>

                <div class="divider"></div>

                <p class="message-text" style="font-size: 13px; color: #718096;">
                    Si vous n'avez pas demandé cette activation, vous pouvez ignorer ce message en toute sécurité.
                </p>
            </div>
            <div class="footer">
                <p class="footer-text">Cordialement,</p>
                <p class="footer-brand">L'équipe LegalHub</p>
                <p class="footer-text" style="margin-top: 15px;">
                    © 2024 LegalHub. Tous droits réservés.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Activation de votre compte LegalHub",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_activation(email: EmailStr):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px 20px;
            }}
            .email-wrapper {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                color: #ffffff;
                font-size: 28px;
                font-weight: 600;
                margin: 0;
                letter-spacing: 0.5px;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .success-badge {{
                text-align: center;
                margin-bottom: 25px;
            }}
            .success-icon {{
                display: inline-block;
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                border-radius: 50%;
                line-height: 80px;
                font-size: 40px;
                color: white;
                box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);
            }}
            .welcome-text {{
                font-size: 18px;
                color: #2d3748;
                margin-bottom: 20px;
                font-weight: 500;
                text-align: center;
            }}
            .message-text {{
                font-size: 15px;
                color: #4a5568;
                line-height: 1.8;
                margin-bottom: 15px;
                text-align: center;
            }}
            .credentials-box {{
                background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                border: 2px solid #667eea;
                padding: 25px;
                margin: 30px 0;
                border-radius: 12px;
                text-align: center;
            }}
            .credentials-box h3 {{
                color: #2d3748;
                font-size: 16px;
                margin-bottom: 15px;
                font-weight: 600;
            }}
            .password-display {{
                background-color: #ffffff;
                padding: 15px 25px;
                border-radius: 8px;
                display: inline-block;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }}
            .password-display strong {{
                color: #667eea;
                font-size: 24px;
                letter-spacing: 2px;
                font-family: 'Courier New', monospace;
            }}
            .warning-box {{
                background-color: #fef5e7;
                border-left: 4px solid #f59e0b;
                padding: 20px;
                margin: 25px 0;
                border-radius: 8px;
            }}
            .warning-box p {{
                font-size: 14px;
                color: #92400e;
                margin: 0;
            }}
            .warning-icon {{
                font-size: 18px;
                margin-right: 8px;
            }}
            .divider {{
                height: 1px;
                background: linear-gradient(to right, transparent, #e2e8f0, transparent);
                margin: 30px 0;
            }}
            .footer {{
                background-color: #f7fafc;
                padding: 30px;
                text-align: center;
            }}
            .footer-text {{
                font-size: 13px;
                color: #718096;
                margin-bottom: 8px;
            }}
            .footer-brand {{
                font-size: 14px;
                color: #667eea;
                font-weight: 600;
            }}
            @media only screen and (max-width: 600px) {{
                .header h1 {{
                    font-size: 24px;
                }}
                .content {{
                    padding: 30px 20px;
                }}
                .success-icon {{
                    width: 60px;
                    height: 60px;
                    line-height: 60px;
                    font-size: 30px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <h1>🏛️ LegalHub</h1>
            </div>
            <div class="content">
                <div class="success-badge">
                    <div class="success-icon">✓</div>
                </div>

                <p class="welcome-text">Compte activé avec succès ! 🎉</p>

                <p class="message-text">
                    Bonjour,
                </p>
                <p class="message-text">
                    Nous avons le plaisir de vous informer que votre compte LegalHub a été activé par notre administrateur.
                </p>

                <div class="credentials-box">
                    <h3>🔐 Vos identifiants de connexion</h3>
                    <p style="font-size: 14px; color: #4a5568; margin-bottom: 15px;">
                        Utilisez votre email et le mot de passe ci-dessous :
                    </p>
                    <div class="password-display">
                        <strong>123456</strong>
                    </div>
                </div>

                <div class="warning-box">
                    <p>
                        <span class="warning-icon">⚠️</span>
                        <strong>Important :</strong> Pour votre sécurité, veuillez changer ce mot de passe dès votre première connexion.
                    </p>
                </div>

                <div class="divider"></div>

                <p class="message-text" style="font-size: 14px; color: #4a5568;">
                    Vous pouvez maintenant profiter de toutes les fonctionnalités de LegalHub.
                </p>
            </div>
            <div class="footer">
                <p class="footer-text">Cordialement,</p>
                <p class="footer-brand">L'équipe LegalHub</p>
                <p class="footer-text" style="margin-top: 15px;">
                    © 2024 LegalHub. Tous droits réservés.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Activation de votre compte LegalHub",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)

async def send_email(email: EmailStr, subject: str, html_content: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)


async def send_jugement_favorable_email(email: EmailStr, dossier):
    html_content = templates.get_template("email/jugement_favorable.html").render(dossier=dossier)

    message = MessageSchema(
        subject=f"Jugement Favorable - Dossier {dossier.numero_dossier}",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_jugement_definitif_email(email: EmailStr, dossier):
    html_content = templates.get_template("email/jugement_definitif.html").render(dossier=dossier)

    message = MessageSchema(
        subject=f"Jugement Définitif - Dossier {dossier.numero_dossier}",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


@celery_app.task(name="send_jugement_favorable_email_programmer")
def send_jugement_favorable_email_programmer(email: EmailStr, dossier: dict):
    html_content = templates.get_template("email/rappel_grosse.html").render(dossier=dossier)

    message = MessageSchema(
        subject=f"Recuperation Grosse - Dossier {dossier.get('numero_dossier', '')}",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    asyncio.run(fm.send_message(message))


@celery_app.task(name="send_opposition_email_programmer")
def send_opposition_email_programmer(email: str, dossier: dict):
    html_content = templates.get_template("email/rappel_opposition.html").render(dossier=dossier)

    message = MessageSchema(
        subject=f"Rappel Délai d'Opposition - Dossier {dossier.get('numero_dossier', '')}",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    asyncio.run(fm.send_message(message))


@celery_app.task(name="send_appel_email_programmer")
def send_appel_email_programmer(email: str, dossier: dict):
    html_content = templates.get_template("email/rappel_appel.html").render(dossier=dossier)

    message = MessageSchema(
        subject=f"Rappel Délai d'Appel - Dossier {dossier.get('numero_dossier', '')}",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    asyncio.run(fm.send_message(message))


async def send_facture_email(email: EmailStr, facture_data: dict, pdf_path: str = None):
    html_content = templates.get_template("email/facture_envoi.html").render(
        facture=facture_data,
        CABINET_TELEPHONE=CABINET_TELEPHONE,
        CABINET_ADRESSE=CABINET_ADRESSE,
        CABINET_NOM=CABINET_NOM,
        NOM_AVOCAT=NOM_AVOCAT,
        MAIL_CABINET=MAIL_CABINET,
        IBAN=IBAN,
        BIC=BIC,
        NOM_MOBILE=NOM_MOBILE,
        NUMERO_MOBILE=NUMERO_MOBILE
    )

    attachments = []
    if pdf_path and os.path.exists(pdf_path):
        attachments = [pdf_path]

    message = MessageSchema(
        subject=f"Facture {facture_data.get('numero_facture', '')} - Cabinet d'Avocat",
        recipients=[email],
        body=html_content,
        subtype="html",
        attachments=attachments
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_relance_facture_email(email: EmailStr, facture_data: dict):
    html_content = templates.get_template("email/facture_relance.html").render(
        facture=facture_data,
        CABINET_TELEPHONE=CABINET_TELEPHONE,
        CABINET_ADRESSE=CABINET_ADRESSE,
        CABINET_NOM=CABINET_NOM,
        NOM_AVOCAT=NOM_AVOCAT,
        MAIL_CABINET=MAIL_CABINET,
        IBAN=IBAN,
        BIC=BIC,
        NOM_MOBILE=NOM_MOBILE,
        NUMERO_MOBILE=NUMERO_MOBILE
    )

    message = MessageSchema(
        subject=f"Relance Facture {facture_data.get('numero_facture', '')} - Échéance dépassée",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


@celery_app.task(name="send_facture_email_task")
def send_facture_email_task(email: str, facture_data: dict, pdf_path: str = None):
    try:
        asyncio.run(send_facture_email(email, facture_data, pdf_path))
        return {"status": "success", "message": "Facture envoyée par email"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@celery_app.task(name="send_relance_facture_task")
def send_relance_facture_task(email: str, facture_data: dict):
    try:
        asyncio.run(send_relance_facture_email(email, facture_data))
        return {"status": "success", "message": "Relance envoyée par email"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@celery_app.task(name="check_factures_rappel")
def check_factures_rappel():
    from app.db.session import SessionLocal
    from app.repositories.facture import get_factures_en_attente_relance, update_relance_facture

    db = SessionLocal()
    try:
        factures_relance = get_factures_en_attente_relance(db)
        count_sent = 0

        for facture in factures_relance:
            client_email = None
            if hasattr(facture.dossier, 'client') and facture.dossier.client:
                client_email = facture.dossier.client.email

            if client_email:
                facture_data = {
                    'numero_facture': facture.numero_facture,
                    'montant_ttc': facture.montant_ttc,
                    'date_echeance': facture.date_echeance.isoformat(),
                    'nom_client': facture.nom_client_anonyme,
                    'description': facture.description,
                    'nombre_relances': facture.nombre_relances + 1,
                    'jours_retard': (datetime.utcnow().date() - facture.date_echeance).days
                }

                send_relance_facture_task.delay(client_email, facture_data)

                update_relance_facture(db, facture.id)
                count_sent += 1

        db.commit()
        return f"Envoyé {count_sent} rappels de facturation"

    except Exception as e:
        db.rollback()
        return f"Erreur lors de l'envoi des rappels: {str(e)}"
    finally:
        db.close()


async def send_password_change_confirmation(email: EmailStr, token: str):
    if ENV == "production":
        confirmation_link = f"https://legalhub-2.onrender.com/confirm-password-change?token={token}"
    else:
        confirmation_link = f"https://localhost:8000/confirm-password-change?token={token}"

    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f7fa;
                margin: 0;
                padding: 0;
            }}
            .container {{
                width: 100%;
                max-width: 600px;
                margin: auto;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                padding: 30px;
            }}
            h2 {{
                color: #007bff;
                text-align: center;
            }}
            p {{
                font-size: 16px;
                color: #333;
                line-height: 1.5;
            }}
            .button {{
                display: inline-block;
                padding: 12px 25px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-size: 16px;
                margin: 20px 0;
            }}
            .warning {{
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                color: #777;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Confirmation de changement de mot de passe</h2>
            <p>Bonjour,</p>
            <p>Vous avez demandé à changer votre mot de passe sur LegalHub. Pour confirmer cette modification, veuillez cliquer sur le lien ci-dessous :</p>
            <div style="text-align: center;">
                <a href="{confirmation_link}" class="button">Confirmer le changement</a>
            </div>
            <div class="warning">
                <strong>⚠️ Important :</strong> Ce lien expire dans 24 heures. Si vous n'avez pas demandé cette modification, ignorez ce message ou contactez immédiatement l'administrateur.
            </div>
            <p>Pour votre sécurité, ce lien ne peut être utilisé qu'une seule fois.</p>
            <div class="footer">
                <p>Cordialement,</p>
                <p>L'équipe LegalHub</p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Confirmation de changement de mot de passe - LegalHub",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_password_reset_email(email: EmailStr, token: str, user_name: str = ""):
    if ENV == "production":
        reset_link = f"https://legalhub-2.onrender.com/reset_password?token={token}"
    else:
        reset_link = f"https://localhost:8000/reset_password?token={token}"

    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f4f7fa;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                padding: 30px;
            }}
            .button {{
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 25px;
                font-weight: bold;
                margin: 20px 0;
                transition: all 0.3s ease;
            }}
            .button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }}
            .warning {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #6c757d;
                font-size: 14px;
            }}
            .security-icon {{
                font-size: 48px;
                margin-bottom: 20px;
            }}
            .link-box {{
                word-break: break-all;
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                font-family: monospace;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="security-icon">🔐</div>
                <h1>Réinitialisation de mot de passe</h1>
            </div>
            <div class="content">
                <p>Bonjour{' ' + user_name if user_name else ''},</p>
                <p>Vous avez demandé à réinitialiser votre mot de passe sur LegalHub. Pour créer un nouveau mot de passe, veuillez cliquer sur le bouton ci-dessous :</p>
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">Réinitialiser mon mot de passe</a>
                </div>
                <div class="warning">
                    <strong>⚠️ Important :</strong>
                    <ul style="margin: 10px 0;">
                        <li>Ce lien expire dans <strong>24 heures</strong></li>
                        <li>Il ne peut être utilisé qu'<strong>une seule fois</strong></li>
                        <li>Si vous n'avez pas demandé cette réinitialisation, ignorez ce message</li>
                        <li>Votre mot de passe actuel reste valide tant que vous n'en créez pas un nouveau</li>
                    </ul>
                </div>
                <p>Si le bouton ne fonctionne pas, vous pouvez copier et coller ce lien dans votre navigateur :</p>
                <p class="link-box">{reset_link}</p>
            </div>
            <div class="footer">
                <p>Cordialement,<br>L'équipe LegalHub</p>
                <p style="font-size: 12px; color: #adb5bd;">
                    Cet email a été envoyé automatiquement, merci de ne pas y répondre.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Réinitialisation de votre mot de passe - LegalHub",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


@celery_app.task()
def send_delai_alert_email(email: str, dossier: dict):
    try:
        html_content = templates.get_template("email/alerte_fond.html").render(dossier=dossier)

        message = MessageSchema(
            subject=f"Alerte Récupération Décision au Fond - Dossier {dossier.get('numero_dossier', '')}",
            recipients=[email],
            body=html_content,
            subtype="html"
        )

        fm = FastMail(conf)
        asyncio.run(fm.send_message(message))

        print(f"✅ Email d’alerte FOND envoyé à {email} pour le dossier {dossier.get('numero_dossier', 'Inconnu')}")

    except Exception as e:
        print(f"❌ Erreur lors de l’envoi de l’email d’alerte FOND : {str(e)}")
