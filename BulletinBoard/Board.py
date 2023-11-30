from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import time, datetime
from threading import Lock

from ServerIO import send_socket_data, send_socket_msg

@dataclass
class Message:
    id: int
    sender: User
    post_date = None
    subject: str
    body: str

class Response:
    statusCodes = {
        0: "OK",
        1: "Failed"
    }
        
    OK = 0
    FAILED = 1
    
    def __init__(self, status, msg = None):
        self.status = status
        if msg == None:
            self.msg = self.statusCodes[status]
        else:
            self.msg = msg
    
    def is_OK(self):
        return self.status == 0
    
class Group:
    def __init__(self, id):
        self.id = id
        self.idcounter = 0
        self.messages: List[Message] = []
        self.connected_users: List[User] = []
        self.lock: Lock = Lock()
    
    def send_message(self, user: User, message: Message):
        with self.lock:
            if user not in self.connected_users:
                raise Exception("No such user in group")
            message.post_date = time.time()
            message.id = self.idcounter
            self.idcounter += 1
            self.messages.append(message)
            for u in self.connected_users:
                send_socket_data("message", u, [message])

    # yield all messages up to a time + 2
    def __msgs_up_to_time_plus_two__(self, time):
        if len(self.messages) == 0: return []
        
        try:
            i = next(i for i, x in enumerate(self.messages) if x.post_date > time)
        except:
            i = len(self.messages) - 1

        i = max(i - 1, 0)
        return self.messages[i:]

    def get_messages(self, user: User, alreadylocked = False):
        lock = self.lock if not alreadylocked else Lock()
        with lock:
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
            for member in self.connected_users:
                if member is user: continue
                try:
                    send_socket_msg(member, f"{user.username} has connected to group {self.id}")
                except:
                    print(f"Failed to notify a user in group {self.id} of user join")
            try:
                send_socket_data("message", user, self.get_messages(user, True))
            except:
                print("Failed to send joining user stored messages")
            
    def disconnect_user(self, user: User):
        with self.lock:
            if user.username not in [user.username for user in self.connected_users]:
                raise Exception("User not in group")
            self.connected_users.remove(user)
            for member in self.connected_users:
                if member is user: continue
                try:
                    send_socket_msg(member, f"{user.username} has disconnected from group {self.id}")
                except:
                    print(f"Failed to notify a user in group {self.id} of user leave")

    def is_member(self, user: User):
        with self.lock:
            return user in self.connected_users
    def get_users(self):
        with self.lock:
            return self.connected_users.copy()
        
class User:
    def __init__(self, sock, sock_lock):
        self.connection_time = time.time()
        self.username = None
        self.member_groups: List[Group] = []
        self.connected = True
        self.sock = sock
        self.sock_lock = sock_lock

    
    def join_group(self, group: Group) -> Response:
        self.member_groups.append(group)
        try:
            group.join_user(self)
        except Exception as e:
            self.member_groups.remove(group)
            return Response(Response.FAILED, str(e))
        return Response(Response.OK)
        
    def leave_group(self, group: Group) -> Response:
        try:
            self.member_groups.remove(group)
            group.disconnect_user(self)
            return Response(Response.OK)
        except:
            try:
                return Response(
                    Response.FAILED, 
                    f"You are not a member of group {group.id}"
                )
            except:
                return Response(
                    Response.FAILED, 
                    f"Fatal server error"
                )

    def leave_all_groups(self):
        for group in self.member_groups:
            try:
                self.leave_group(group)
            except:
                pass

    def post_message(self, group: Group, message: Message) -> Response:
        try:
            group.send_message(self, message)
        except:
            return Response(Response.FAILED, "You are not a part of that group")
        return Response(Response.OK)

    def get_message(self, group: Group, message_id) -> Tuple[Response, Message]:
        if group not in self.member_groups:
            return (Response(Response.FAILED, "You are not in that group"), None)
        res, visible_messages = self.get_messages(group)
        try:
            msg = next(filter(lambda x: x.id == message_id, visible_messages))
            return (Response(Response.OK), msg)
        except:
            return (Response(Response.FAILED, "Message does not exist"), None)

    def get_messages(self, group: Group) -> Tuple[Response, List[Message]]:
        return (
            Response(Response.OK), 
            group.get_messages(self)
        )

    def get_users(self, group: Group)  -> Tuple[Response, List[str]]:
        return (
            Response(Response.OK), 
            [str(x) for x in group.get_users()]
        )
    
    def in_group(self, group: Group):
        return group in self.member_groups
    
    def get_all_groups(self):
        return self.member_groups.copy()
    
    def disconnect(self):
        with self.sock_lock:
            self.connected = False
            self.sock.close()
        self.leave_all_groups()

    # to string
    def __str__(self):
        return f"{self.username} - Connected at {datetime.datetime.fromtimestamp(self.connection_time).strftime('%c')}"