"""Database module entry point."""
from src.database.core import DatabaseCore
from src.database.crud import DatabaseCRUDMixin

# Combine Core Infrastructure and CRUD Operations
class Database(DatabaseCore, DatabaseCRUDMixin):
    pass

# Global database instance
db = Database()