# src/user/enums.py

from enum import Enum


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"