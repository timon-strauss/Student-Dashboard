from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, StatementError

from Database.models import Card, Deck, Exam, ReviewLog, UTCDateTime, utcnow


class TestUtcnow:
    def test_returns_aware_utc(self):
        value = utcnow()

        assert value.tzinfo is timezone.utc
        assert abs(datetime.now(timezone.utc) - value) < timedelta(seconds=5)


class TestUTCDateTime:
    def setup_method(self):
        self.type = UTCDateTime()

    def test_bind_none(self):
        assert self.type.process_bind_param(None, None) is None

    def test_bind_rejects_naive(self):
        with pytest.raises(ValueError, match="timezone-aware"):
            self.type.process_bind_param(datetime(2026, 1, 1), None)

    def test_bind_converts_to_naive_utc(self):
        cet = timezone(timedelta(hours=2))

        result = self.type.process_bind_param(datetime(2026, 1, 1, 14, 0, tzinfo=cet), None)

        assert result == datetime(2026, 1, 1, 12, 0)
        assert result.tzinfo is None

    def test_result_none(self):
        assert self.type.process_result_value(None, None) is None

    def test_result_attaches_utc(self):
        result = self.type.process_result_value(datetime(2026, 1, 1, 12, 0), None)

        assert result == datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class TestPersistence:
    def test_tables_and_indexes_created(self, db):
        with db._session() as session:
            inspector = inspect(session.get_bind())
            tables = set(inspector.get_table_names())
            card_indexes = {i["name"] for i in inspector.get_indexes("cards")}

        assert tables == {"exams", "decks", "cards", "review_logs"}
        assert "ix_cards_deck_id_due" in card_indexes

    def test_foreign_keys_enabled(self, db):
        with db._session() as session:
            assert session.execute(text("PRAGMA foreign_keys")).scalar() == 1

    def test_naive_datetime_is_rejected_on_flush(self, db):
        with db._session() as session:
            session.add(Exam(name="x", exam_date=datetime(2026, 1, 1)))
            with pytest.raises(StatementError):
                session.commit()

    def test_datetime_roundtrip_is_aware_utc(self, db):
        local = datetime(2026, 3, 1, 9, 30, tzinfo=timezone(timedelta(hours=-5)))
        with db._session() as session:
            exam = Exam(name="x", exam_date=local)
            session.add(exam)
            session.commit()
            exam_id = exam.id

        with db._session() as session:
            stored = session.get(Exam, exam_id).exam_date

        assert stored.tzinfo == timezone.utc
        assert stored == local

    def test_card_defaults(self, db, make_deck):
        deck = make_deck()
        before = datetime.now(timezone.utc)
        with db._session() as session:
            card = Card(deck_id=deck.id, front="f", back="b")
            session.add(card)
            session.commit()
            session.refresh(card)

            assert card.position == 0
            assert card.state == 1
            assert card.step == 0
            assert card.stability is None
            assert card.difficulty is None
            assert card.last_review is None
            assert before - timedelta(seconds=1) <= card.due <= datetime.now(timezone.utc)

    def test_review_log_defaults_reviewed_at(self, db, make_deck, make_card):
        card = make_card(make_deck().id)
        with db._session() as session:
            log = ReviewLog(card_id=card.id, rating=3)
            session.add(log)
            session.commit()
            session.refresh(log)

            assert log.reviewed_at.tzinfo == timezone.utc

    @pytest.mark.parametrize("state", [0, 4])
    def test_card_state_check_constraint(self, db, make_deck, state):
        deck = make_deck()
        with db._session() as session:
            session.add(Card(deck_id=deck.id, front="f", back="b", state=state))
            with pytest.raises(IntegrityError):
                session.commit()

    @pytest.mark.parametrize("rating", [0, 5])
    def test_review_rating_check_constraint(self, db, make_deck, make_card, rating):
        card = make_card(make_deck().id)
        with db._session() as session:
            session.add(ReviewLog(card_id=card.id, rating=rating))
            with pytest.raises(IntegrityError):
                session.commit()

    def test_deck_foreign_key_enforced(self, db):
        with db._session() as session:
            session.add(Deck(exam_id=999, name="x"))
            with pytest.raises(IntegrityError):
                session.commit()

    def test_card_foreign_key_enforced(self, db):
        with db._session() as session:
            session.add(Card(deck_id=999, front="f", back="b"))
            with pytest.raises(IntegrityError):
                session.commit()

    def test_review_log_foreign_key_enforced(self, db):
        with db._session() as session:
            session.add(ReviewLog(card_id=999, rating=3))
            with pytest.raises(IntegrityError):
                session.commit()

    def test_relationships(self, db, make_exam, make_deck, make_card):
        exam = make_exam()
        deck = make_deck(exam_id=exam.id)
        card = make_card(deck.id)
        with db._session() as session:
            session.add(ReviewLog(card_id=card.id, rating=3))
            session.commit()

            loaded_exam = session.get(Exam, exam.id)
            loaded_card = session.get(Card, card.id)

            assert [d.id for d in loaded_exam.decks] == [deck.id]
            assert loaded_exam.decks[0].cards[0].id == card.id
            assert loaded_card.deck.exam.id == exam.id
            assert loaded_card.review_logs[0].card is loaded_card

    def test_raw_sql_delete_cascades(self, db, make_exam, make_deck, make_card):
        exam = make_exam()
        deck = make_deck(exam_id=exam.id)
        card = make_card(deck.id)
        with db._session() as session:
            session.add(ReviewLog(card_id=card.id, rating=3))
            session.commit()
            session.execute(text("DELETE FROM exams WHERE id = :id"), {"id": exam.id})
            session.commit()

            counts = [
                session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                for table in ("decks", "cards", "review_logs")
            ]

        assert counts == [0, 0, 0]
