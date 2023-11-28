import time
from typing import List, Tuple
from Group import Group
from Message import Message
from Response import Response
class User:
    def __init__(self, username):
        self.connection_time = time.time()
        self.username = username
        self.member_groups: List[Group] = []
    
    def join_group(self, group: Group) -> Response:
        self.member_groups.append(group)
        try:
            group.join_user(self)
        except:
            self.member_groups.remove(group)
            return Response(Response.FAILED)
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