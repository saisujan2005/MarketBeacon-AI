from app.models.base import Base
from app.models.alert import Alert
from app.db.database import engine

Base.metadata.create_all(bind=engine)

print("Alert table created")