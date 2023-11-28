from typing import List
from Message import Message
from User import User
class Group:
    def __init__(self, id):
        self.id = id
        self.past_messages: List[Message] = []
        self.connected_users: List[User] = []
    
    def send_message(self, user: User, message: Message):
        pass
    def get_messages(self, user: User):
        pass
    
    def join_user(self, user: User):
        pass
    def disconnect_user(self, user: User):
        pass

    def is_member(self, user: User):
        return user in self.connected_users
    def get_users(self):
        return self.connected_users
    