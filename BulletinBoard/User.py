import time, datetime

from threading import Lock
from typing import List, Tuple

from Group import Group
from Message import Message
from Response import Response

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

    def post_message(self, message: Message) -> Response:
        for group in self.member_groups:
            group.send_message(self, message)
        return Response(Response.OK)

    def get_message(self, message_id) -> Tuple[Response, Message]:
        res, visible_messages = self.get_messages()
        try:
            msg = next(filter(lambda x: x.id == message_id, visible_messages))
            return (Response(Response.OK), msg)
        except:
            return (Response(Response.FAILED, "Message is not visible or does not exist"), None)

    def get_messages(self) -> Tuple[Response, List[Message]]:
        return (
            Response(Response.OK), 
            [group.get_messages(self) for group in self.member_groups]
        )

    def get_users(self)  -> Tuple[Response, List[Group]]:
        return (
            Response(Response.OK), 
            List(set([item for sublist in [group.get_users() for group in self.member_groups] for item in sublist]))
        )
    
    def in_group(self, group: Group):
        return group in self.member_groups
    
    def get_all_groups(self):
        return self.member_groups.copy()
    
    def disconnect(self):
        self.connected = False
        with self.sock_lock:
            self.sock.close()
        self.leave_all_groups()

    # to string
    def __str__(self):
        return f"{self.username} - Connected at {datetime.datetime.fromtimestamp(self.connection_time).strftime('%c')}"
        
