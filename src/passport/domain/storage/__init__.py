from abc import ABC

from passport.domain.storage.users import UsersRepo


class Storage(ABC):
    users: UsersRepo
