import os
import re
import time
from datetime import timedelta
from pathlib import Path

import pytest

from Database import NotFoundError
from Database.models import Card
from Database.schemas import CardCreate, CardUpdate


@pytest.fixture
def upload_dir(db, isolated_paths):
    return isolated_paths / "uploads"


def set_age(path, age):
    stamp = time.time() - age.total_seconds()
    os.utime(path, (stamp, stamp))


def set_image_unchecked(db, card_id, name):
    with db._session() as session:
        session.get(Card, card_id).front_image = name
        session.commit()


class TestDeleteCard:
    def test_removes_front_and_back_image(self, make_deck, make_card, image, db):
        front, back = image("f.png"), image("b.png")
        card = make_card(make_deck().id, front_image="f.png", back_image="b.png")

        db.delete_card(card.id)

        assert not front.exists()
        assert not back.exists()

    def test_same_image_on_both_sides(self, make_deck, make_card, image, db):
        path = image("x.png")
        card = make_card(make_deck().id, front_image="x.png", back_image="x.png")

        db.delete_card(card.id)

        assert not path.exists()

    def test_keeps_image_used_by_other_card(self, make_deck, make_card, image, db):
        path = image("shared.png")
        deck = make_deck()
        card = make_card(deck.id, front_image="shared.png")
        make_card(deck.id, back_image="shared.png")

        db.delete_card(card.id)

        assert path.exists()

    def test_missing_file_is_ignored(self, make_deck, make_card, image, db):
        path = image("gone.png")
        card = make_card(make_deck().id, front_image="gone.png")
        path.unlink()

        db.delete_card(card.id)

        with pytest.raises(NotFoundError):
            db.get_card(card.id)

    def test_never_deletes_outside_upload_dir(self, make_deck, make_card, isolated_paths, db):
        outside = isolated_paths / "secret.txt"
        outside.write_text("keep")
        card = make_card(make_deck().id)
        set_image_unchecked(db, card.id, "../secret.txt")

        db.delete_card(card.id)

        assert outside.exists()

    def test_missing_card_keeps_files(self, image, db):
        path = image("f.png")

        with pytest.raises(NotFoundError):
            db.delete_card(1)

        assert path.exists()


class TestCascade:
    def test_delete_deck_removes_images_of_its_cards(self, make_deck, make_card, image, db):
        gone, kept = image("gone.png"), image("kept.png")
        deck = make_deck()
        other = make_deck()
        make_card(deck.id, front_image="gone.png")
        make_card(other.id, front_image="kept.png")

        db.delete_deck(deck.id)

        assert not gone.exists()
        assert kept.exists()

    def test_delete_exam_removes_images_of_all_decks(self, make_exam, make_deck, make_card, image, db):
        a, b, kept = image("a.png"), image("b.png"), image("kept.png")
        exam = make_exam()
        make_card(make_deck(exam_id=exam.id).id, front_image="a.png")
        make_card(make_deck(exam_id=exam.id).id, back_image="b.png")
        make_card(make_deck().id, front_image="kept.png")

        db.delete_exam(exam.id)

        assert not a.exists()
        assert not b.exists()
        assert kept.exists()

    def test_cascade_keeps_image_shared_with_surviving_card(self, make_exam, make_deck, make_card, image, db):
        path = image("shared.png")
        exam = make_exam()
        make_card(make_deck(exam_id=exam.id).id, front_image="shared.png")
        make_card(make_deck().id, front_image="shared.png")

        db.delete_exam(exam.id)

        assert path.exists()


class TestUpdateCard:
    def test_replacing_image_removes_old_one(self, make_deck, make_card, image, db):
        old, new = image("old.png"), image("new.png")
        card = make_card(make_deck().id, front_image="old.png")

        db.update_card(card.id, CardUpdate(front_image="new.png"))

        assert not old.exists()
        assert new.exists()

    def test_clearing_image_removes_it(self, make_deck, make_card, image, db):
        path = image("b.png")
        card = make_card(make_deck().id, back_image="b.png")

        db.update_card(card.id, CardUpdate(back_image=None))

        assert not path.exists()

    def test_moving_image_to_other_side_keeps_it(self, make_deck, make_card, image, db):
        path = image("x.png")
        card = make_card(make_deck().id, front_image="x.png")

        db.update_card(card.id, CardUpdate(front_image=None, back_image="x.png"))

        assert path.exists()

    def test_text_update_keeps_images(self, make_deck, make_card, image, db):
        path = image("f.png")
        card = make_card(make_deck().id, front_image="f.png")

        db.update_card(card.id, CardUpdate(front="neu"))

        assert path.exists()


class TestSaveImage:
    def test_writes_file_with_unique_name(self, upload_dir, db):
        first = db.save_image(b"one", ".png")
        second = db.save_image(b"two", ".png")

        assert first != second
        assert (upload_dir / first).read_bytes() == b"one"
        assert (upload_dir / second).read_bytes() == b"two"

    def test_name_matches_upload_route_pattern(self, db):
        name = db.save_image(b"x", ".JPG")

        assert re.fullmatch(r"[0-9a-f]{32}\.jpg", name)

    @pytest.mark.parametrize("extension", ["png", "", ".", "./png", ".p/ng", "../x"])
    def test_rejects_invalid_extension(self, upload_dir, extension, db):
        with pytest.raises(ValueError):
            db.save_image(b"x", extension)

        assert list(upload_dir.iterdir()) == []

    def test_saved_image_is_cleaned_up_with_card(self, upload_dir, make_deck, make_card, db):
        name = db.save_image(b"x", ".png")
        card = make_card(make_deck().id, front_image=name)

        db.delete_card(card.id)

        assert not (upload_dir / name).exists()


class TestGetImagePath:
    def test_returns_path_of_saved_image(self, db):
        name = db.save_image(b"data", ".webp")

        assert db.get_image_path(name).read_bytes() == b"data"

    def test_missing_image_raises(self, db):
        with pytest.raises(NotFoundError) as exc:
            db.get_image_path("nope.png")

        assert (exc.value.entity, exc.value.entity_id) == ("Image", "nope.png")

    @pytest.mark.parametrize("name", ["../secret.txt", "../uploads", ""])
    def test_rejects_paths_outside_upload_dir(self, isolated_paths, name, db):
        (isolated_paths / "secret.txt").write_text("x")

        with pytest.raises(NotFoundError):
            db.get_image_path(name)


class TestImageInUse:
    def test_front_and_back(self, make_deck, make_card, image, db):
        image("f.png")
        image("b.png")
        deck = make_deck()
        make_card(deck.id, front_image="f.png")
        make_card(deck.id, back_image="b.png")

        assert db.image_in_use("f.png")
        assert db.image_in_use("b.png")
        assert not db.image_in_use("other.png")


class TestImageMustExist:
    def test_create_with_missing_image_raises(self, make_deck, db):
        deck = make_deck()

        with pytest.raises(NotFoundError) as exc:
            db.create_card(CardCreate(deck_id=deck.id, front="f", back="b", back_image="missing.png"))

        assert (exc.value.entity, exc.value.entity_id) == ("Image", "missing.png")
        assert db.list_cards(deck.id) == []

    def test_create_with_path_outside_upload_dir_raises(self, make_deck, isolated_paths, db):
        (isolated_paths / "secret.txt").write_text("x")

        with pytest.raises(NotFoundError):
            db.create_card(CardCreate(deck_id=make_deck().id, front="f", back="b", front_image="../secret.txt"))

    def test_update_with_missing_image_raises_and_keeps_card(self, make_deck, make_card, image, db):
        path = image("old.png")
        card = make_card(make_deck().id, front_image="old.png")

        with pytest.raises(NotFoundError) as exc:
            db.update_card(card.id, CardUpdate(front="neu", front_image="missing.png"))

        assert exc.value.entity == "Image"
        assert db.get_card(card.id) == card
        assert path.exists()

    def test_missing_card_is_reported_before_image(self, db):
        with pytest.raises(NotFoundError) as exc:
            db.update_card(1, CardUpdate(front_image="missing.png"))

        assert exc.value.entity == "Card"


class TestRemoveUnusedImages:
    def test_removes_old_unused_saved_images(self, upload_dir, db):
        path = upload_dir / db.save_image(b"x", ".png")
        set_age(path, timedelta(hours=2))

        db.remove_unused_images()

        assert not path.exists()

    def test_keeps_recent_images(self, upload_dir, db):
        path = upload_dir / db.save_image(b"x", ".png")

        db.remove_unused_images()

        assert path.exists()

    def test_keeps_images_in_use(self, upload_dir, make_deck, make_card, db):
        name = db.save_image(b"x", ".png")
        make_card(make_deck().id, back_image=name)
        set_age(upload_dir / name, timedelta(days=30))

        db.remove_unused_images()

        assert (upload_dir / name).exists()

    def test_custom_age(self, upload_dir, db):
        path = upload_dir / db.save_image(b"x", ".png")
        set_age(path, timedelta(minutes=10))

        db.remove_unused_images(older_than=timedelta(minutes=5))

        assert not path.exists()

    def test_ignores_files_not_created_by_save_image(self, upload_dir, image, db):
        foreign = image("notes.txt")
        hidden = image(".DS_Store")
        folder = upload_dir / ("a" * 32 + ".png")
        folder.mkdir()
        for path in (foreign, hidden, folder):
            set_age(path, timedelta(days=30))

        db.remove_unused_images()

        assert foreign.exists()
        assert hidden.exists()
        assert folder.is_dir()

    def test_runs_on_db_start(self, start_db, isolated_paths):
        upload_dir = isolated_paths / "uploads"
        upload_dir.mkdir(parents=True)
        old = upload_dir / ("b" * 32 + ".png")
        old.write_bytes(b"x")
        set_age(old, timedelta(hours=2))

        start_db(f"sqlite:///{isolated_paths / 'test.db'}")

        assert not old.exists()


def raise_permission_error(self, missing_ok=False):
    raise PermissionError(self)


class TestUnlinkFailure:
    @pytest.fixture
    def failing_unlink(self, monkeypatch):
        monkeypatch.setattr(Path, "unlink", raise_permission_error)

    def test_delete_card_succeeds_and_keeps_file(self, make_deck, make_card, image, failing_unlink, db):
        path = image("f.png")
        card = make_card(make_deck().id, front_image="f.png")

        db.delete_card(card.id)

        with pytest.raises(NotFoundError):
            db.get_card(card.id)
        assert path.exists()

    def test_kept_file_is_removed_later(self, upload_dir, make_deck, make_card, monkeypatch, db):
        name = db.save_image(b"x", ".png")
        card = make_card(make_deck().id, front_image=name)
        original = Path.unlink
        monkeypatch.setattr(Path, "unlink", raise_permission_error)
        db.delete_card(card.id)
        monkeypatch.setattr(Path, "unlink", original)
        set_age(upload_dir / name, timedelta(hours=2))

        db.remove_unused_images()

        assert not (upload_dir / name).exists()
