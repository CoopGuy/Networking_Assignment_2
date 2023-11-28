from dataclasses import dataclass
from User import User

@dataclass
class Message:
    id = id
    sender: User
    post_date = None
    subject: str
    body: str