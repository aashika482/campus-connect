# Import every model so Base.metadata knows all tables. Alembic (alembic/env.py) relies
# on this to autogenerate migrations, and it also lets relationship("Club") etc. resolve
# no matter which model a module imports first.
# When you add a new model file, import it here.
from app.models import user, club, event, membership, discussion, notification  # noqa: F401
