import time, datetime

from threading import Lock
from typing import List, Tuple

from . import Group
from . import Message
from . import Response

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

    def get_message(self, group: Group,message_id) -> Tuple[Response, Message]:
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

    def get_users(self, group)  -> Tuple[Response, List[str]]:
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
        
