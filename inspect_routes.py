import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.main import app

print("Registered FastAPI Routes:")
for route in app.routes:
    # Use hasattr to check for methods since some routes (like Mount) might not have it
    methods = getattr(route, "methods", "N/A")
    print(f"  {route.path} -> {route.name} (methods: {methods})")
