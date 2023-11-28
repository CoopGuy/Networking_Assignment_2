import time
from dataclasses import dataclass
from User import User

@dataclass
class Message:
    id = id
    sender: User
    post_date = time.time()
    subject: str
    body: str