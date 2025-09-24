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
        activation_link = f"https://legalhub.onrender.com/activate?token={token}"
    else:
        activation_link = f"http://localhost:8000/activate?token={token}"

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
            .footer {{
                text-align: center;
                color: #777;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Bienvenue sur LegalHub</h2>
            <p>Bonjour,</p>
            <p>Merci de vous être inscrit sur LegalHub. Pour activer votre compte, veuillez cliquer sur le lien ci-dessous :</p>
            <a href="{activation_link}" class="button">Activer mon compte</a>
            <p>Votre Mot de passe par défaut est 123456 </p>
            <p>Si vous n'avez pas demandé cette activation, vous pouvez ignorer ce message.</p>
            <div class="footer">
                <p>Cordialement,</p>
                <p>L'équipe LegalHub</p>
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
            .footer {{
                text-align: center;
                color: #777;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Bienvenue sur LegalHub</h2>
            <p>Bonjour,</p>
            <p>Votre compte a été activé par l'administrateur de LegalHub.</p>
            <p>Vous pouvez dès maintenant vous connecter avec votre email et le mot de passe par défaut :</p>
            <p><strong>Mot de passe : 123456</strong></p>
            <p>Merci de le changer dès votre première connexion.</p>
            <div class="footer">
                <p>Cordialement,</p>
                <p>L'équipe LegalHub</p>
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
