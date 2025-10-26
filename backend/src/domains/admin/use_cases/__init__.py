"""
Admin use cases.

This package contains all use cases related to admin workflows:
- User management
- Statistics
- Bulk operations
"""

from .bulk_action_users import BulkActionUsersUseCase
from .create_user import CreateUserUseCase
from .delete_user import DeleteUserUseCase
from .get_user import GetUserUseCase
from .get_user_stats import GetUserStatsUseCase
from .helpers import AdminUseCase, get_admin_usecase
from .list_users import ListUsersUseCase
from .update_user import UpdateUserUseCase

__all__ = [
    # Use cases
    "ListUsersUseCase",
    "GetUserUseCase",
    "UpdateUserUseCase",
    "DeleteUserUseCase",
    "GetUserStatsUseCase",
    "BulkActionUsersUseCase",
    "CreateUserUseCase",
    # Helpers
    "AdminUseCase",
    "get_admin_usecase",
]
