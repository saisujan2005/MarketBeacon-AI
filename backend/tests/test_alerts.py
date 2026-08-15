"""
P0.5 / P0.7 - Alert importance typing, numeric comparison, and duplicate prevention.
"""

import uuid

from sqlalchemy import Integer

from app.models.alert import Alert
from app.models.post import Post
from app.services.alert_engine import qualifies_for_alert, process_post_alerts
from app.scripts.generate_alerts import generate_alerts
from tests.support import get_session, make_user, make_post, reset_tables


def test_importance_score_column_is_integer():
    col = Alert.__table__.c.importance_score
    assert isinstance(col.type, Integer), (
        f"Alert.importance_score must be Integer, got {col.type!r}"
    )


def test_numeric_comparison_semantics_in_database():
    """
    The original String column made these comparisons lexicographic:
    '100' >= '80' was FALSE and '9' >= '80' was TRUE. Verify real numeric ordering.
    """
    reset_tables("alerts", "posts", "users")
    db = get_session()
    try:
        user = make_user(db)
        for score in (9, 80, 95, 100):
            db.add(Alert(
                id=uuid.uuid4(),
                user_id=user.id,
                title=f"Alert scoring {score}",
                event_type="EARNINGS",
                importance_score=score,
            ))
        db.commit()

        got = {
            a.importance_score
            for a in db.query(Alert).filter(Alert.importance_score >= 80).all()
        }
        assert got == {80, 95, 100}, f"Expected {{80, 95, 100}} for >= 80, got {got}"

        assert db.query(Alert).filter(Alert.importance_score >= 80).count() == 3
        assert db.query(Alert).filter(Alert.importance_score < 80).count() == 1

        # The specific historical failure: 100 must be included, 9 must not.
        high = {a.importance_score for a in db.query(Alert).filter(Alert.importance_score >= 90).all()}
        assert 100 in high, "Score 100 must be treated as >= 90 (was excluded when stored as text)"
        assert 9 not in high, "Score 9 must not be treated as >= 90"

        ordered = [
            a.importance_score
            for a in db.query(Alert).order_by(Alert.importance_score.desc()).all()
        ]
        assert ordered == [100, 95, 80, 9], f"Numeric ordering wrong: {ordered}"
    finally:
        db.close()


def test_threshold_qualification():
    class FakePost:
        def __init__(self, score, level):
            self.importance_score = score
            self.impact_level = level

    assert qualifies_for_alert(FakePost(95, "CRITICAL")) is True
    assert qualifies_for_alert(FakePost(85, "HIGH")) is True
    assert qualifies_for_alert(FakePost(50, "CRITICAL")) is True   # critical overrides score
    assert qualifies_for_alert(FakePost(80, "HIGH")) is False      # strictly greater than
    assert qualifies_for_alert(FakePost(9, "LOW")) is False
    assert qualifies_for_alert(FakePost(None, None)) is False


def test_duplicate_alerts_are_not_created():
    reset_tables("alerts", "posts", "users")
    db = get_session()
    try:
        user = make_user(db)
        post = make_post(db, "RBI cuts repo rate by 25bps", importance_score=95)

        first = process_post_alerts(db, post, user.id)
        assert first is not None, "First call should create an alert"

        second = process_post_alerts(db, post, user.id)
        assert second is None, "Second call must not create a duplicate alert"

        assert db.query(Alert).filter(Alert.user_id == user.id).count() == 1
    finally:
        db.close()


def test_generate_alerts_is_incremental_and_marks_posts_processed():
    reset_tables("alerts", "posts", "users")
    db = get_session()
    try:
        user_a = make_user(db, email="a@example.test")
        user_b = make_user(db, email="b@example.test")

        post = make_post(db, "Fed announces emergency rate cut", importance_score=95)
        low = make_post(db, "Minor lifestyle piece", importance_score=20, impact_level="LOW")

        created = generate_alerts(db)
        # One alert per user for the qualifying post only.
        assert created == 2, f"Expected 2 alerts (one per user), got {created}"
        assert db.query(Alert).count() == 2

        # Both posts are marked processed, including the non-qualifying one.
        db.refresh(post)
        db.refresh(low)
        assert post.alerts_processed_at is not None
        assert low.alerts_processed_at is not None

        # Second run must be a no-op: no rescanning, no duplicates.
        again = generate_alerts(db)
        assert again == 0, f"Second run should create 0 alerts, created {again}"
        assert db.query(Alert).count() == 2

        # A newly arrived post is picked up without touching old ones.
        make_post(db, "ECB signals policy shift", importance_score=95)
        third = generate_alerts(db)
        assert third == 2, f"New post should alert both users, got {third}"
        assert db.query(Alert).count() == 4
    finally:
        db.close()


def test_unenriched_posts_are_skipped():
    """Posts without an importance score are not ready for alerting yet."""
    reset_tables("alerts", "posts", "users")
    db = get_session()
    try:
        make_user(db)
        p = make_post(db, "Unscored article", importance_score=95)
        p.importance_score = None
        db.commit()

        created = generate_alerts(db)
        assert created == 0
        db.refresh(p)
        assert p.alerts_processed_at is None, (
            "Unenriched posts must stay in the queue for a later run."
        )
    finally:
        db.close()
