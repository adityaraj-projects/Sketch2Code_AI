import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.collaboration.comments_service import CommentError, add_comment, delete_comment, list_comments
from app.collaboration.versions_service import VersionError, list_versions, restore_version, save_version
from app.db.database import Base
from app.models.project import Project
from app.models.user import User


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def owner(db_session):
    user = User(full_name="Alice Owner", email="alice@example.com", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def collaborator(db_session):
    user = User(full_name="Bob Collaborator", email="bob@example.com", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def project(db_session, owner):
    p = Project(owner_id=owner.id, name="Test Project", canvas_data={"nodes": [], "edges": [], "strokes": [], "viewport": {"x": 0, "y": 0, "zoom": 1}})
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


def test_add_comment_attached_to_a_node(db_session, project, owner):
    comment = add_comment(db_session, project.id, owner.id, owner.full_name, "Check this condition", node_id="dec1")
    assert comment.node_id == "dec1"
    assert comment.text == "Check this condition"


def test_add_comment_at_a_free_floating_point(db_session, project, owner):
    comment = add_comment(db_session, project.id, owner.id, owner.full_name, "General note", x=120.0, y=340.0)
    assert comment.x == 120.0 and comment.y == 340.0


def test_comment_requires_either_node_or_position(db_session, project, owner):
    with pytest.raises(CommentError):
        add_comment(db_session, project.id, owner.id, owner.full_name, "orphaned comment")


def test_empty_comment_text_rejected(db_session, project, owner):
    with pytest.raises(CommentError):
        add_comment(db_session, project.id, owner.id, owner.full_name, "   ", node_id="a")


def test_list_comments_returns_in_chronological_order(db_session, project, owner):
    add_comment(db_session, project.id, owner.id, owner.full_name, "first", node_id="a")
    add_comment(db_session, project.id, owner.id, owner.full_name, "second", node_id="b")
    comments = list_comments(db_session, project.id)
    assert [c.text for c in comments] == ["first", "second"]


def test_only_author_can_delete_their_comment(db_session, project, owner, collaborator):
    comment = add_comment(db_session, project.id, owner.id, owner.full_name, "mine", node_id="a")
    with pytest.raises(CommentError):
        delete_comment(db_session, project.id, comment.id, collaborator.id)
    delete_comment(db_session, project.id, comment.id, owner.id)
    assert list_comments(db_session, project.id) == []


def test_save_version_snapshots_current_canvas_data(db_session, project, owner):
    project.canvas_data = {"nodes": [{"id": "n1"}], "edges": [], "strokes": [], "viewport": {"x": 0, "y": 0, "zoom": 1}}
    db_session.commit()

    version = save_version(db_session, project, owner.id, owner.full_name, label="Checkpoint 1")
    assert version.label == "Checkpoint 1"
    assert version.canvas_data["nodes"] == [{"id": "n1"}]


def test_save_version_without_label_gets_a_readable_default(db_session, project, owner):
    version = save_version(db_session, project, owner.id, owner.full_name)
    assert "Version at" in version.label


def test_list_versions_most_recent_first(db_session, project, owner):
    save_version(db_session, project, owner.id, owner.full_name, label="v1")
    save_version(db_session, project, owner.id, owner.full_name, label="v2")
    versions = list_versions(db_session, project.id)
    assert versions[0].label == "v2"
    assert versions[1].label == "v1"


def test_restore_version_replaces_current_canvas_data(db_session, project, owner):
    project.canvas_data = {"nodes": [{"id": "old"}], "edges": [], "strokes": [], "viewport": {"x": 0, "y": 0, "zoom": 1}}
    db_session.commit()
    old_version = save_version(db_session, project, owner.id, owner.full_name, label="before change")

    project.canvas_data = {"nodes": [{"id": "new"}], "edges": [], "strokes": [], "viewport": {"x": 0, "y": 0, "zoom": 1}}
    db_session.commit()

    restored = restore_version(db_session, project, old_version.id)
    assert restored.canvas_data["nodes"] == [{"id": "old"}]


def test_restore_unknown_version_raises(db_session, project, owner):
    with pytest.raises(VersionError):
        restore_version(db_session, project, uuid.uuid4())


def test_version_pruning_keeps_only_the_most_recent(db_session, project, owner, monkeypatch):
    import app.collaboration.versions_service as versions_module
    from datetime import datetime, timedelta
    monkeypatch.setattr(versions_module, "MAX_VERSIONS_PER_PROJECT", 3)

    base_time = datetime.utcnow()
    for i in range(5):
        save_version(
            db_session,
            project,
            owner.id,
            owner.full_name,
            label=f"v{i}",
            created_at=base_time + timedelta(seconds=i),
        )

    versions = list_versions(db_session, project.id)
    assert len(versions) == 3
    assert [v.label for v in versions] == ["v4", "v3", "v2"]
