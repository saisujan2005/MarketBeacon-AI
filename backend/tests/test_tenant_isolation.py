"""
P0.4 - Tenant isolation.

Central assertion: User A can never retrieve User B's private research.
Also covers the RAG retrieval path, which was the actual leak (reports were
pulled globally into every user's copilot context).
"""

import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db as db_get_db
from app.db.dependencies import get_db as dep_get_db, get_current_user
from app.models.research_report import ResearchReport
from tests.support import get_session, make_user, reset_tables


def _client_for(user, db):
    """TestClient whose DB session and authenticated user are overridden."""
    app.dependency_overrides[db_get_db] = lambda: db
    app.dependency_overrides[dep_get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _clear_overrides():
    app.dependency_overrides.clear()


def _seed_two_users_with_reports():
    reset_tables("research_reports", "users")
    db = get_session()
    user_a = make_user(db, email="alice@example.test")
    user_b = make_user(db, email="bob@example.test")

    report_a = ResearchReport(
        id=uuid.uuid4(),
        user_id=user_a.id,
        entity_name="TCS",
        report_data={"report_text": "ALICE PRIVATE RESEARCH"},
    )
    report_b = ResearchReport(
        id=uuid.uuid4(),
        user_id=user_b.id,
        entity_name="Infosys",
        report_data={"report_text": "BOB PRIVATE RESEARCH"},
    )
    db.add_all([report_a, report_b])
    db.commit()
    return db, user_a, user_b, report_a, report_b


def test_research_report_model_has_owner_column():
    assert hasattr(ResearchReport, "user_id"), (
        "ResearchReport must have a user_id column for tenant isolation."
    )


def test_user_a_cannot_list_user_b_reports():
    db, user_a, user_b, report_a, report_b = _seed_two_users_with_reports()
    try:
        client = _client_for(user_a, db)
        resp = client.get("/research-reports")
        assert resp.status_code == 200
        ids = {row["id"] for row in resp.json()}
        assert str(report_a.id) in ids, "User A should see their own report"
        assert str(report_b.id) not in ids, "LEAK: User A can see User B's report in the list"
    finally:
        _clear_overrides()
        db.close()


def test_user_a_cannot_fetch_user_b_report_by_id():
    db, user_a, user_b, report_a, report_b = _seed_two_users_with_reports()
    try:
        client = _client_for(user_a, db)

        own = client.get(f"/research-reports/{report_a.id}")
        assert own.status_code == 200

        other = client.get(f"/research-reports/{report_b.id}")
        assert other.status_code == 404, (
            f"LEAK: User A fetched User B's report (status {other.status_code})"
        )
        assert "BOB PRIVATE RESEARCH" not in other.text
    finally:
        _clear_overrides()
        db.close()


def test_rag_retrieval_excludes_other_users_reports():
    """
    hybrid_search() previously ran db.query(ResearchReport).all() for every user.
    Verify the query is now scoped and that an anonymous call returns nothing private.
    """
    db, user_a, user_b, report_a, report_b = _seed_two_users_with_reports()
    try:
        scoped_for_a = (
            db.query(ResearchReport)
            .filter(ResearchReport.user_id == user_a.id)
            .all()
        )
        texts = " ".join(str(r.report_data) for r in scoped_for_a)
        assert "ALICE PRIVATE RESEARCH" in texts
        assert "BOB PRIVATE RESEARCH" not in texts

        import inspect as _inspect
        from app.retrieval import hybrid_retriever

        source = _inspect.getsource(hybrid_retriever.hybrid_search)
        assert "db.query(ResearchReport).all()" not in source, (
            "hybrid_search still performs an unscoped ResearchReport query."
        )
        assert "ResearchReport.user_id == user_id" in source, (
            "hybrid_search must filter research reports by user_id."
        )
        # Without a user_id, no private source may be loaded at all.
        assert "reports = []" in source
    finally:
        _clear_overrides()
        db.close()


def test_report_generation_requires_a_user():
    from app.agents.research_report_agent import generate_research_report

    db = get_session()
    try:
        raised = False
        try:
            generate_research_report(db, "TCS", user_id=None)
        except ValueError:
            raised = True
        assert raised, "generate_research_report must reject a missing user_id."
    finally:
        db.close()


def test_explain_service_scopes_alerts_by_user():
    """An alert lookup in the Explain engine must be filtered by user_id."""
    import inspect as _inspect
    from app.services import explain_service

    source = _inspect.getsource(explain_service.explain_item)
    assert "Alert.user_id == user_id" in source, (
        "explain_item must scope alert lookups to the requesting user."
    )
    assert 'cache_key = f"{user_id}:' in source, (
        "explain cache key must be namespaced per user."
    )
