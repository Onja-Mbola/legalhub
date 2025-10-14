from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Demandeur(Base):
    __tablename__ = "demandeurs"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    nom = Column(String, nullable=True)
    qualite = Column(Integer, ForeignKey("param_general.id"), nullable=False)
    telephone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    adresse = Column(String, nullable=True)

    dossier = relationship("Dossier", back_populates="demandeurs")
    client = relationship("Client")
    qualite_param = relationship("ParamGeneral")

    @property
    def nom_complet(self):
        return self.client.nom if self.client else self.nom

    @property
    def email_contact(self):
        return self.client.email if self.client else self.email

    @property
    def telephone_contact(self):
        return self.client.telephone if self.client else self.telephone
