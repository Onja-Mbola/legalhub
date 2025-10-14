import os
from datetime import timedelta
from io import BytesIO

from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.colors import blue
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

load_dotenv()

CABINET_TELEPHONE = os.getenv("CABINET_TELEPHONE", "+XXX XX XX XX XX")
CABINET_ADRESSE = os.getenv("CABINET_ADRESSE", "Adresse non définie")
CABINET_NOM = os.getenv("CABINET_NOM", "Cabinet d'avocat")
NOM_AVOCAT = os.getenv("NOM_AVOCAT", "Avocat")
MAIL_CABINET = os.getenv("MAIL_CABINET", "contact@cabinet.com")
IBAN = os.getenv("IBAN", "FR76 XXXX XXXX XXXX XXXX XXXX XXX")
BIC = os.getenv("BIC", "XXXXXXXXX")
NOM_MOBILE = os.getenv("NOM_MOBILE", "XXXXXXXXX")
NUMERO_MOBILE = os.getenv("NUMERO_MOBILE", "XXXXXXXXX")


def generate_facture_pdf(facture, dossier) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2 * cm, leftMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30,
                                 alignment=1, textColor=blue)
    normal_style = styles['Normal']
    bold_style = ParagraphStyle('Bold', parent=normal_style, fontSize=12, spaceAfter=12, fontName='Helvetica-Bold')

    story = []

    cabinet_info = [
        Paragraph(f"<b>{CABINET_NOM}</b>", title_style),
        Paragraph(f"Maître {NOM_AVOCAT}", bold_style),
        Paragraph(f"{CABINET_ADRESSE}", normal_style),
        Paragraph(f"Tél: {CABINET_TELEPHONE}", normal_style),
        Paragraph(f"Email: {MAIL_CABINET}", normal_style),
        Spacer(1, 20)
    ]
    story.extend(cabinet_info)

    facture_table_data = [
        ['FACTURE N°:', facture.numero_facture, 'CLIENT:', facture.nom_client_anonyme],
        ['Date d\'émission:', facture.date_emission.strftime('%d/%m/%Y') if facture.date_emission else 'N/A',
         'Dossier N°:', dossier.numero_dossier],
        ['Date d\'échéance:', facture.date_echeance.strftime('%d/%m/%Y'),
         'Type d\'affaire:', dossier.type_affaire_param.valeur if dossier.type_affaire_param else 'N/A'],
    ]
    facture_table = Table(facture_table_data, colWidths=[3 * cm, 5 * cm, 2.5 * cm, 4.5 * cm])
    facture_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (3, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (3, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(facture_table)
    story.append(Spacer(1, 30))

    story.append(Paragraph("<b>DESCRIPTION DES PRESTATIONS</b>", bold_style))
    story.append(Spacer(1, 10))

    prestations_data = [['Description', 'Montant HT'], [facture.description, f"{facture.montant_ht:.2f} Ariary"]]
    prestations_table = Table(prestations_data, colWidths=[9 * cm, 6 * cm])
    prestations_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, 1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(prestations_table)
    story.append(Spacer(1, 20))

    tva_amount = facture.montant_ht * (facture.taux_tva / 100)
    total_data = [
        ['', 'Montant HT:', f"{facture.montant_ht:.2f} Ariary"],
        ['', f'TVA ({facture.taux_tva}%):', f"{tva_amount:.2f} Ariary"],
        ['', 'TOTAL TTC:', f"{facture.montant_ttc:.2f} Ariary"]
    ]
    total_table = Table(total_data, colWidths=[6 * cm, 3.5 * cm, 5.5 * cm])
    total_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (1, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 2), (-1, 2), 12),
        ('BACKGROUND', (1, 2), (-1, 2), colors.lightgrey),
        ('LINEBELOW', (1, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (1, 1), (-1, 1), 1, colors.black),
        ('BOX', (1, 2), (-1, 2), 2, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
    ]))
    story.append(total_table)
    story.append(Spacer(1, 30))

    conditions = [
        Paragraph("<b>CONDITIONS DE PAIEMENT</b>", bold_style),
        Paragraph(f"Échéance: {facture.date_echeance.strftime('%d/%m/%Y')}", normal_style),
        Paragraph("Mode de paiement: Virement bancaire ou chèque", normal_style),
        Paragraph("Pénalités de retard: 3 fois le taux d'intérêt légal", normal_style),
        Paragraph("Indemnité forfaitaire pour frais de recouvrement: 40 Ariary", normal_style),
        Spacer(1, 20)
    ]
    story.extend(conditions)

    story.append(Paragraph("<b>COORDONNÉES BANCAIRES</b>", bold_style))
    story.append(Paragraph(f"IBAN: {IBAN}", normal_style))
    story.append(Paragraph(f"BIC: {BIC}", normal_style))
    story.append(Spacer(1, 30))

    story.append(Paragraph("<b>COORDONNÉES MOBILE MONEY</b>", bold_style))
    story.append(Paragraph(f"NOM: {NOM_MOBILE}", normal_style))
    story.append(Paragraph(f"NUMERO: {NUMERO_MOBILE}", normal_style))
    story.append(Spacer(1, 30))

    story.append(Paragraph("Cette facture est établie conformément aux dispositions légales en vigueur.",
                           ParagraphStyle('Footer', parent=normal_style, fontSize=8, alignment=1)))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_rapport_facturation_pdf(report_data) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2 * cm, leftMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=20,
                                 alignment=1, textColor=blue)
    story = []

    period_text = {
        'current_month': 'Mois en cours',
        'last_month': 'Mois précédent',
        'current_quarter': 'Trimestre en cours',
        'current_year': 'Année en cours',
        'custom': 'Période personnalisée'
    }.get(report_data['period'], 'Période sélectionnée')
    date_avec_3h = report_data['date_generation'] + timedelta(hours=3)
    story.append(Paragraph(f"<b>RAPPORT DE FACTURATION</b>", title_style))
    story.append(Paragraph(f"{CABINET_NOM}", styles['Normal']))
    story.append(Paragraph(f"Période: {period_text}", styles['Normal']))
    story.append(Paragraph(f"Généré le: {date_avec_3h.strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 30))

    stats = report_data['stats_facturation']
    stats_data = [
        ['STATISTIQUES GÉNÉRALES', ''],
        ['Nombre total de factures:', str(stats.nombre_factures_total)],
        ['Factures payées:', str(stats.nombre_factures_payees)],
        ['Factures impayées:', str(stats.nombre_factures_impayees)],
        ['Montant total facturé:', f"{stats.total_facture:.2f} Ariary"],
        ['Montant payé:', f"{stats.total_paye:.2f} Ariary"],
        ['Montant impayé:', f"{stats.total_impaye:.2f} Ariary"],
        ['Taux de recouvrement:', f"{stats.taux_recouvrement:.1f}%"]
    ]
    stats_table = Table(stats_data, colWidths=[6.5 * cm, 5.5 * cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 30))

    if report_data.get('revenus_mensuels'):
        story.append(Paragraph("<b>REVENUS MENSUELS</b>", styles['Heading2']))
        story.append(Spacer(1, 10))
        revenus_data = [['Mois', 'Revenus (Ariary)']]
        mois_noms = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        for mois, montant in report_data['revenus_mensuels'].items():
            if montant > 0:
                mois_nom = mois_noms[int(mois) - 1] if mois.isdigit() else mois
                revenus_data.append([mois_nom, f"{montant:.2f} Ariary"])
        if len(revenus_data) > 1:
            revenus_table = Table(revenus_data, colWidths=[4 * cm, 8 * cm])
            revenus_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(revenus_table)
            story.append(Spacer(1, 20))

    if report_data.get('sources_revenus'):
        story.append(Paragraph("<b>REVENUS PAR TYPE D'AFFAIRE</b>", styles['Heading2']))
        story.append(Spacer(1, 10))
        sources_data = [['Type d\'affaire', 'Revenus (Ariary)', 'Pourcentage']]
        total_sources = sum(report_data['sources_revenus'].values())
        for type_affaire, montant in report_data['sources_revenus'].items():
            pourcentage = (montant / total_sources * 100) if total_sources > 0 else 0
            sources_data.append([type_affaire[:30], f"{montant:.2f} Ariary", f"{pourcentage:.1f}%"])
        sources_table = Table(sources_data, colWidths=[4.5 * cm, 5 * cm, 2.5 * cm])
        sources_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(sources_table)
        story.append(Spacer(1, 20))

    if report_data.get('factures'):
        story.append(Paragraph("<b>DÉTAIL DES FACTURES</b>", styles['Heading2']))
        story.append(Spacer(1, 10))
        factures_data = [['N° Facture', 'Client', 'Montant TTC', 'Échéance', 'Statut']]
        for facture in report_data['factures'][:20]:
            factures_data.append([
                facture.numero_facture,
                facture.nom_client_anonyme[:20],
                f"{facture.montant_ttc:.2f} Ariary",
                facture.date_echeance.strftime('%d/%m/%Y'),
                facture.statut.value.title().replace('_', ' ')
            ])
        factures_table = Table(factures_data, colWidths=[3.5 * cm, 3 * cm, 4.5 * cm, 2.5 * cm, 2.5 * cm])
        factures_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(factures_table)

    if report_data.get('top_clients'):
        story.append(Spacer(1, 30))
        story.append(Paragraph("<b>TOP CLIENTS (ANONYMISÉS)</b>", styles['Heading2']))
        story.append(Spacer(1, 10))
        clients_data = [['Rang', 'Référence Client', 'Revenus (Ariary)', 'Nb Factures']]
        for i, client in enumerate(report_data['top_clients'], 1):
            clients_data.append([str(i), client['nom_client_anonyme'], f"{client['total_revenus']:.2f} Ariary",
                                 str(client['nb_factures'])])
        clients_table = Table(clients_data, colWidths=[1.5 * cm, 4.5 * cm, 5 * cm, 3 * cm])
        clients_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(clients_table)

    story.append(Spacer(1, 30))
    story.append(Paragraph("Rapport généré automatiquement par le système de gestion du cabinet.",
                           ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=1)))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
