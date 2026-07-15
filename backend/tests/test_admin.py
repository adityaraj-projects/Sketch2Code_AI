import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.admin.deps import get_current_admin_user
from app.admin.service import (
    AdminError,
    admin_delete_project,
    get_analytics_summary,
    list_all_projects,
    list_users_with_stats,
    set_user_active,
)
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


def _make_user(db, name, email, is_admin=False, is_active=True):
    user = User(full_name=name, email=email, hashed_password="x", is_admin=is_admin, is_active=is_active)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_project(db, owner, name="Untitled", is_shared=False):
    p = Project(owner_id=owner.id, name=name, is_shared=is_shared, canvas_data={"nodes": [], "edges": [], "strokes": [], "viewport": {"x": 0, "y": 0, "zoom": 1}})
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def test_list_users_with_stats_counts_projects_correctly(db_session):
    alice = _make_user(db_session, "Alice", "alice@example.com")
    bob = _make_user(db_session, "Bob", "bob@example.com")
    _make_project(db_session, alice, "A1")
    _make_project(db_session, alice, "A2")

    rows = {r.user.email: r.project_count for r in list_users_with_stats(db_session)}
    assert rows["alice@example.com"] == 2
    assert rows["bob@example.com"] == 0


def test_list_all_projects_includes_owner_info(db_session):
    alice = _make_user(db_session, "Alice", "alice@example.com")
    _make_project(db_session, alice, "Alice's Flowchart", is_shared=True)

    rows = list_all_projects(db_session)
    assert len(rows) == 1
    assert rows[0].owner_name == "Alice"
    assert rows[0].owner_email == "alice@example.com"
    assert rows[0].project.is_shared is True


def test_admin_can_deactivate_another_user(db_session):
    admin = _make_user(db_session, "Admin", "admin@example.com", is_admin=True)
    target = _make_user(db_session, "Target", "target@example.com")

    updated = set_user_active(db_session, target.id, False, admin.id)
    assert updated.is_active is False


def test_admin_cannot_deactivate_themself(db_session):
    admin = _make_user(db_session, "Admin", "admin@example.com", is_admin=True)
    with pytest.raises(AdminError):
        set_user_active(db_session, admin.id, False, admin.id)


def test_set_active_on_unknown_user_raises(db_session):
    admin = _make_user(db_session, "Admin", "admin@example.com", is_admin=True)
    with pytest.raises(AdminError):
        set_user_active(db_session, uuid.uuid4(), False, admin.id)


def test_admin_delete_project_removes_it(db_session):
    alice = _make_user(db_session, "Alice", "alice@example.com")
    project = _make_project(db_session, alice)

    admin_delete_project(db_session, project.id)

    assert db_session.get(Project, project.id) is None


def test_admin_delete_unknown_project_raises(db_session):
    with pytest.raises(AdminError):
        admin_delete_project(db_session, uuid.uuid4())


def test_analytics_summary_reflects_real_counts(db_session):
    alice = _make_user(db_session, "Alice", "alice@example.com")
    bob = _make_user(db_session, "Bob", "bob@example.com")
    _make_project(db_session, alice, "A1", is_shared=True)
    _make_project(db_session, alice, "A2", is_shared=False)
    _make_project(db_session, bob, "B1", is_shared=True)

    summary = get_analytics_summary(db_session)

    assert summary.total_users == 2
    assert summary.total_projects == 3
    assert summary.shared_projects == 2
    assert summary.avg_projects_per_user == pytest.approx(1.5)


def test_analytics_with_no_users_avoids_division_by_zero(db_session):
    summary = get_analytics_summary(db_session)
    assert summary.total_users == 0
    assert summary.avg_projects_per_user == 0.0


def test_non_admin_user_rejected_by_dependency():
    regular_user = User(full_name="Regular", email="r@example.com", hashed_password="x", is_admin=False)
    with pytest.raises(HTTPException) as exc_info:
        get_current_admin_user(regular_user)
    assert exc_info.value.status_code == 403


def test_admin_user_passes_dependency():
    admin_user = User(full_name="Admin", email="a@example.com", hashed_password="x", is_admin=True)
    assert get_current_admin_user(admin_user) is admin_user
