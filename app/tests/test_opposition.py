import pytest
from datetime import date, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.opposition import Opposition
from app.services.opposition_service import (
    create_opposition_appel_auto,
    update_opposition_appel_service
)
from app.services.fond_service import create_decision_fond_service
from app.services.jugement_definitif_service import create_jugement_definitif_service
from app.schemas.fond import DecisionFondCreate
from app.schemas.jugement_definitif import JugementDefinitifCreate


class TestOppositionValidations:

    def test_create_opposition_auto_success(self, db: Session, dossier_mock, decision_fond_mock):
        date_notif = date.today()

        opposition = create_opposition_appel_auto(
            db=db,
            decision_fond_id=decision_fond_mock.id,
            date_notification=date_notif
        )

        assert opposition.decision_fond_id == decision_fond_mock.id
        assert opposition.date_notification == date_notif
        assert opposition.opposition_possible_jusqua == date_notif + timedelta(days=15)
        assert opposition.opposition_formulee is False

    def test_create_opposition_date_notification_invalide(self, db: Session, decision_fond_mock):
        date_notif = decision_fond_mock.date_decision_fond - timedelta(days=1)

        with pytest.raises(HTTPException) as exc:
            create_opposition_appel_auto(
                db=db,
                decision_fond_id=decision_fond_mock.id,
                date_notification=date_notif
            )

        assert exc.value.status_code == 400
        assert "antérieure" in str(exc.value.detail).lower()

    def test_formuler_opposition_delai_valide(self, db: Session, opposition_mock):
        date_opp = opposition_mock.date_notification + timedelta(days=5)

        updated = update_opposition_appel_service(
            db=db,
            opposition_id=opposition_mock.id,
            date_opposition=date_opp,
            motifs_opposition="Test"
        )

        assert updated.opposition_formulee is True
        assert updated.date_opposition == date_opp

    def test_formuler_opposition_delai_depasse(self, db: Session, opposition_expired_mock):
        date_opp = date.today()

        with pytest.raises(HTTPException) as exc:
            update_opposition_appel_service(
                db=db,
                opposition_id=opposition_expired_mock.id,
                date_opposition=date_opp
            )

        assert exc.value.status_code == 400
        assert "15 jours est dépassé" in str(exc.value.detail)

    def test_formuler_opposition_date_avant_notification(self, db: Session, opposition_mock):
        date_opp = opposition_mock.date_notification - timedelta(days=1)

        with pytest.raises(HTTPException) as exc:
            update_opposition_appel_service(
                db=db,
                opposition_id=opposition_mock.id,
                date_opposition=date_opp
            )

        assert exc.value.status_code == 400
        assert "antérieure" in str(exc.value.detail).lower()

    def test_formuler_opposition_date_apres_limite(self, db: Session, opposition_mock):
        date_opp = opposition_mock.opposition_possible_jusqua + timedelta(days=1)

        with pytest.raises(HTTPException) as exc:
            update_opposition_appel_service(
                db=db,
                opposition_id=opposition_mock.id,
                date_opposition=date_opp
            )

        assert exc.value.status_code == 400
        assert "dépasser la date limite" in str(exc.value.detail)


class TestJugementDefinitifBlocking:

    def test_create_jugement_opposition_en_cours(self, db: Session, dossier_with_opposition):
        data = JugementDefinitifCreate(
            dossier_id=dossier_with_opposition.id,
            deliberation_id=1,
            date_jugement=date.today(),
            texte_jugement="Test"
        )

        with pytest.raises(HTTPException) as exc:
            create_jugement_definitif_service(
                db=db,
                dossier_id=dossier_with_opposition.id,
                avocat_nom="Test",
                data=data,
                user_id=1
            )

        assert exc.value.status_code == 400
        assert "opposition" in str(exc.value.detail).lower()

    def test_create_jugement_opposition_non_mise_a_jour(self, db: Session, dossier_with_expired_opposition):
        data = JugementDefinitifCreate(
            dossier_id=dossier_with_expired_opposition.id,
            deliberation_id=1,
            date_jugement=date.today(),
            texte_jugement="Test"
        )

        with pytest.raises(HTTPException) as exc:
            create_jugement_definitif_service(
                db=db,
                dossier_id=dossier_with_expired_opposition.id,
                avocat_nom="Test",
                data=data,
                user_id=1
            )

        assert exc.value.status_code == 400
        assert "mise à jour" in str(exc.value.detail).lower()

    def test_create_jugement_opposition_formulee(self, db: Session, dossier_with_formuled_opposition):
        data = JugementDefinitifCreate(
            dossier_id=dossier_with_formuled_opposition.id,
            deliberation_id=1,
            date_jugement=date.today(),
            texte_jugement="Test"
        )

        jugement = create_jugement_definitif_service(
            db=db,
            dossier_id=dossier_with_formuled_opposition.id,
            avocat_nom="Test",
            data=data,
            user_id=1
        )

        assert jugement is not None
        assert jugement.dossier_id == dossier_with_formuled_opposition.id


class TestDecisionFondValidations:

    def test_create_decision_date_notification_invalide(self, db: Session, dossier_mock):
        data = DecisionFondCreate(
            dossier_id=dossier_mock.id,
            deliberation_decision_id=1,
            date_decision_fond=date.today(),
            type_decision_fond="par_defaut",
            date_notification=date.today() - timedelta(days=1),
            delai_appel=30
        )

        with pytest.raises(HTTPException) as exc:
            create_decision_fond_service(db=db, data=data)

        assert exc.value.status_code == 400
        assert "antérieure" in str(exc.value.detail).lower()

    def test_create_decision_par_defaut_cree_opposition(self, db: Session, dossier_mock):
        data = DecisionFondCreate(
            dossier_id=dossier_mock.id,
            deliberation_decision_id=1,
            date_decision_fond=date.today(),
            type_decision_fond="par_defaut",
            date_notification=date.today(),
            delai_appel=30
        )

        decision = create_decision_fond_service(db=db, data=data)

        opposition = db.query(Opposition).filter(
            Opposition.decision_fond_id == decision.id
        ).first()

        assert opposition is not None
        assert opposition.opposition_formulee is False

    def test_create_decision_contradictoire_sans_opposition(self, db: Session, dossier_mock):
        data = DecisionFondCreate(
            dossier_id=dossier_mock.id,
            deliberation_decision_id=1,
            date_decision_fond=date.today(),
            type_decision_fond="contradictoire",
            date_notification=date.today(),
            delai_appel=30
        )

        decision = create_decision_fond_service(db=db, data=data)

        opposition = db.query(Opposition).filter(
            Opposition.decision_fond_id == decision.id
        ).first()

        assert opposition is None


# Fixtures pour les tests
@pytest.fixture
def dossier_mock(db: Session):
    from app.models.dossier import Dossier
    from app.core.workflow_enums import ProcessStage

    dossier = Dossier(
        numero_dossier="TEST-001",
        nom_dossier="Test Dossier",
        current_stage=ProcessStage.DELIBERATION_APPEL.value
    )
    db.add(dossier)
    db.commit()
    db.refresh(dossier)
    return dossier


@pytest.fixture
def decision_fond_mock(db: Session, dossier_mock):
    from app.models.fond import Fond

    decision = Fond(
        dossier_id=dossier_mock.id,
        deliberation_decision_id=1,
        date_decision_fond=date.today() - timedelta(days=5),
        type_decision_fond="par_defaut",
        delai_appel=30
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


@pytest.fixture
def opposition_mock(db: Session, dossier_mock, decision_fond_mock):
    from app.models.opposition import Opposition

    opposition = Opposition(
        dossier_id=dossier_mock.id,
        decision_fond_id=decision_fond_mock.id,
        date_notification=date.today(),
        opposition_possible_jusqua=date.today() + timedelta(days=15),
        opposition_formulee=False
    )
    db.add(opposition)
    db.commit()
    db.refresh(opposition)
    return opposition


@pytest.fixture
def opposition_expired_mock(db: Session, dossier_mock, decision_fond_mock):
    from app.models.opposition import Opposition

    opposition = Opposition(
        dossier_id=dossier_mock.id,
        decision_fond_id=decision_fond_mock.id,
        date_notification=date.today() - timedelta(days=20),
        opposition_possible_jusqua=date.today() - timedelta(days=5),
        opposition_formulee=False
    )
    db.add(opposition)
    db.commit()
    db.refresh(opposition)
    return opposition


@pytest.fixture
def dossier_with_opposition(db: Session, dossier_mock, opposition_mock):
    return dossier_mock


@pytest.fixture
def dossier_with_expired_opposition(db: Session, dossier_mock, opposition_expired_mock):
    return dossier_mock


@pytest.fixture
def dossier_with_formuled_opposition(db: Session, dossier_mock):
    from app.models.opposition import Opposition
    from app.models.fond import Fond

    decision = Fond(
        dossier_id=dossier_mock.id,
        deliberation_decision_id=1,
        date_decision_fond=date.today() - timedelta(days=20),
        type_decision_fond="par_defaut",
        delai_appel=30
    )
    db.add(decision)
    db.commit()

    opposition = Opposition(
        dossier_id=dossier_mock.id,
        decision_fond_id=decision.id,
        date_notification=date.today() - timedelta(days=20),
        opposition_possible_jusqua=date.today() - timedelta(days=5),
        opposition_formulee=True,
        date_opposition=date.today() - timedelta(days=10)
    )
    db.add(opposition)
    db.commit()

    return dossier_mock