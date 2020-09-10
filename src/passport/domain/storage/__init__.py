from abc import ABC

from passport.domain.storage.sessions import SessionRepo
from passport.domain.storage.users import UsersRepo


class Storage(ABC):
    sessions: SessionRepo
    users: UsersRepo
