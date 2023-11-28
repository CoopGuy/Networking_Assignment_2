from threading import Lock
from time import time
from typing import List
from Message import Message
from User import User
class Group:
    def __init__(self, id):
        self.id = id
        self.messages: List[Message] = []
        self.connected_users: List[User] = []
        self.lock: Lock = Lock()
    
    def send_message(self, user: User, message: Message):

        with self.lock:
            if user not in self.connected_users:
                raise Exception("No such user in group")
            message.post_date = time()
            self.messages.append(message)

    # yield all messages up to a time + 2
    def __msgs_up_to_time_plus_two__(self, time):
        if len(self.messages) == 0: return []
        
        try:
            i = next(i for i, _ in enumerate(self.messages) if lambda x: x.post_date > time)
        except:
            i = len(self.messages) - 1

        i = max(i - 2, 0)
        return self.messages[i:]

    def get_messages(self, user: User):
        with self.lock:
            if user not in self.connected_users:
                raise Exception("No such user in group")
            if len(self.messages) < 2: 
                return self.messages.copy()
            else:
                return self.__msgs_up_to_time_plus_two__(user.connection_time)

    def join_user(self, user: User):
        with self.lock:
            if user.username in [user.username for user in self.connected_users]:
                raise Exception("User already in group")
            self.connected_users.append(user)
    def disconnect_user(self, user: User):
        with self.lock:
            if user.username not in [user.username for user in self.connected_users]:
                raise Exception("User not in group")
            self.connected_users.remove(user)

    def is_member(self, user: User):
        with self.lock:
            return user in self.connected_users
    def get_users(self):
        with self.lock:
            return self.connected_users.copy()