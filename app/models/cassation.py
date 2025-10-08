from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Cassation(Base):
    __tablename__ = "cassations"

    id = Column(Integer, primary_key=True, index=True)
    decision_fond_id = Column(Integer, ForeignKey("fond.id", ondelete="CASCADE"), nullable=False)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)

    date_notification_decision = Column(Date, nullable=False)
    date_limite_cassation = Column(Date, nullable=False)
    date_depot_requete = Column(Date, nullable=True)
    date_limite_memoire_ampliatif = Column(Date, nullable=True)
    date_depot_memoire_ampliatif = Column(Date, nullable=True)
    date_reception_memoire_defense = Column(Date, nullable=True)
    date_limite_reponse = Column(Date, nullable=True)
    date_delibere = Column(Date, nullable=True)

    statut = Column(String, nullable=False, default="en_attente_requete")
    # Statuts: en_attente_requete, requete_deposee, memoire_ampliatif_depose,
    #          memoire_defense_recu, reponse_envoyee, delibere

    copie_requete = Column(String, nullable=True)
    copie_memoire_ampliatif = Column(String, nullable=True)
    copie_memoire_defense = Column(String, nullable=True)
    copie_reponse = Column(String, nullable=True)

    observations = Column(Text, nullable=True)

    ocr_texte = Column(Text, nullable=True)
    entites_extraites = Column(JSON, nullable=True)

    alerte_requete_envoyee = Column(Boolean, default=False)
    alerte_memoire_ampliatif_envoyee = Column(Boolean, default=False)

    decision_fond = relationship("Fond", back_populates="cassations")
    dossier = relationship("Dossier", back_populates="cassations")
