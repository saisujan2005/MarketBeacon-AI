from app.models.base import Base
from app.models.notification import Notification
from app.db.database import engine

Base.metadata.create_all(bind=engine)

print("Notification table created")