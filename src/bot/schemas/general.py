from enum import Enum


class UserRoles(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
