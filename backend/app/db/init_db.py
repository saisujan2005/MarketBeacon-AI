"""
Creates all database tables based on SQLAlchemy models.

Run once from backend/ directory:
    python -m app.db.init_db
"""

from app.db.database import engine
from app.models.base import Base

# Import every model so Base knows about them before create_all
from app.models.post import Post          # noqa: F401
from app.models.alert import Alert        # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.notification_summary import NotificationSummary  # noqa: F401
from app.models.watchlist import Watchlist        # noqa: F401
from app.models.source import Source              # noqa: F401
from app.models.timeline_event import TimelineEvent  # noqa: F401
from app.models.daily_briefing import DailyBriefing  # noqa: F401
from app.models.research_report import ResearchReport  # noqa: F401
from app.models.chat import ChatSession, ChatMessage  # noqa: F401
from app.models.research_document import ResearchDocument  # noqa: F401
from app.models.research_metric import ResearchMetric  # noqa: F401
from app.models.research_cache import CompanyPeerCache, CompanyResearchCache  # noqa: F401
from app.models.user import User, UserPreferences  # noqa: F401
from app.models.holding import Holding  # noqa: F401
from app.models.research_workspace import ResearchWorkspace  # noqa: F401
from app.models.push_subscription import PushSubscription  # noqa: F401



def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Done. Tables created:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    init_db()