import asyncio
import os
from datetime import datetime, timedelta

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

ENV = os.getenv("ENV", "development")

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
