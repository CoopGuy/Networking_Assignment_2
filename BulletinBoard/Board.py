from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import time, datetime
from threading import Lock

from ServerIO import send_socket_data, send_socket_msg

"""a basic message class to hold the attributes of a message

Raises:
    None

Returns:
    None
"""
@dataclass
class Message:
    id: int
    sender: User
    post_date = None
    subject: str
    body: str

"""a dataclass for holding a response, has generic functions for creating a 
successful or failed response and checking the state of the response

Raises:
    None

Returns:
    None
"""
class Response:
    statusCodes = {
        0: "OK",
        1: "Failed"
    }
        
    OK = 0
    FAILED = 1
    
    """initialze the response with the given args
    Args:
        msg: the message/reason for failure/success
    Raises:
        None
    """
    def __init__(self, status, msg = None):
        self.status = status
        if msg == None:
            self.msg = self.statusCodes[status]
        else:
            self.msg = msg
    
    """report if the response was successful
    Raises:
        None
    Returns:
        bool: if the response was successful
    """
    def is_OK(self):
        return self.status == 0
    
"""a group class for managing all aspects of a message board group

Raises:
    None

Returns:
    None
"""
class Group:
    """Instantiate the class with the given id and empty values
    Args:
        id: the numeric id of the group
    """
    def __init__(self, id):
        self.id = id
        self.idcounter = 0
        self.messages: List[Message] = []
        self.connected_users: List[User] = []
        self.lock: Lock = Lock()
    """a function for a specific user to send a message to this class
    Args:
        user: the user sending the message
        message: the message the user is sending
    Raises:
        Exception: the user is not part of the group
    """
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
    """yield all messages up to a time + 2
    Args:
        time: the time threshold
    Raises:
        None
    """
    def __msgs_up_to_time_plus_two__(self, time):
        if len(self.messages) == 0: return []
        
        try:
            i = next(i for i, x in enumerate(self.messages) if x.post_date > time)
        except:
            i = len(self.messages) - 1

        i = max(i - 1, 0)
        return self.messages[i:]

    """retrieve messages for a user
    Args:
        user: the user sending the message
        alreadylocked: bool indicator if the caller has had its lock acquired already
    Raises:
        Exception: when the user provided is not in the group
    """
    def get_messages(self, user: User, alreadylocked = False):
        lock = self.lock if not alreadylocked else Lock()
        with lock:
            if user not in self.connected_users:
                raise Exception("No such user in group")
            if len(self.messages) < 2: 
                return self.messages.copy()
            else:
                return self.__msgs_up_to_time_plus_two__(user.connection_time)

    """allow a user to join the group
    Args:
        user: the user sending the message
    Raises:
        Exception: when the user is already in the group
    """
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
            
    """allow a user to leave the group
    Args:
        user: the user sending the message
    Raises:
        Exception: when the provided user is not in the group
    """
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
    
    """check if a given user is a member of the group
    Args:
        user: the user sending the message
    """
    def is_member(self, user: User):
        with self.lock:
            return user in self.connected_users
        
    """get a list of the users in the group
    """
    def get_users(self):
        with self.lock:
            return self.connected_users.copy()
        
"""a user class to handle all interactions a specific user may perform with 
this server

Raises:
    None

Returns:
    None
"""
class User:
    """init the user with the current time, the socket they are connected on, 
    and a lock for that socket

    Raises:
        None

    Returns:
        None
    """
    def __init__(self, sock, sock_lock):
        self.connection_time = time.time()
        self.username = None
        self.member_groups: List[Group] = []
        self.connected = True
        self.sock = sock
        self.sock_lock = sock_lock

    """allows a user to join the provided group
    Args:
        group: the group the user wants to join
    
    Raises:
        None

    Returns:
        Response: the response the server gave to the users action
    """
    def join_group(self, group: Group) -> Response:
        self.member_groups.append(group)
        try:
            group.join_user(self)
        except Exception as e:
            self.member_groups.remove(group)
            return Response(Response.FAILED, str(e))
        return Response(Response.OK)
    
    """allows a user to leave the provided group
    Args:
        group: the group the user wants to leave
    
    Raises:
        None

    Returns:
        Response: the response the server gave to the users action
    """
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

    """attempts to have the user leave all groups they are a part of
    
    Raises:
        None

    Returns:
        None
    """
    def leave_all_groups(self):
        for group in self.member_groups:
            try:
                self.leave_group(group)
            except:
                pass

    """allows a user to post a message to the provided group
    Args:
        group: the group the user wants to message
        message: the message the user wants to post
    Raises:
        None

    Returns:
        Response: the response the server gave to the users action
    """
    def post_message(self, group: Group, message: Message) -> Response:
        try:
            group.send_message(self, message)
        except:
            return Response(Response.FAILED, "You are not a part of that group")
        return Response(Response.OK)

    """allows a user to get a message from a group by an id
    Args:
        group: the group the user wants to retrieve the message from
        message_id: the numeric id of the desired message
    Raises:
        None

    Returns:
        Response: the response the server gave to the users action
    """
    def get_message(self, group: Group, message_id) -> Tuple[Response, Message]:
        if group not in self.member_groups:
            return (Response(Response.FAILED, "You are not in that group"), None)
        res, visible_messages = self.get_messages(group)
        try:
            msg = next(filter(lambda x: x.id == message_id, visible_messages))
            return (Response(Response.OK), msg)
        except:
            return (Response(Response.FAILED, "Message does not exist"), None)

    """allows a user to get all messages they are allowed to read from a 
    specified group
    Args:
        group: the group the user wants to request messages from
    
    Raises:
        None

    Returns:
        Response: the response the server gave to the users action
    """
    def get_messages(self, group: Group) -> Tuple[Response, List[Message]]:
        return (
            Response(Response.OK), 
            group.get_messages(self)
        )

    """allows a user to get a list of all users connected to a group
    Args:
        group: the group the user wants to query

    Raises:
        None

    Returns:
        Response: the response the server gave to the users action
    """
    def get_users(self, group: Group)  -> Tuple[Response, List[str]]:
        return (
            Response(Response.OK), 
            [str(x) for x in group.get_users()]
        )
    
    """allows a user to check if they are in a group
    Args:
        group: the group the user wants to query

    Raises:
        None

    Returns:
        bool: if the user is connected to the given group
    """
    def in_group(self, group: Group):
        return group in self.member_groups
    
    """allows a user to get a list of all groups they're connected to
    Args:
        group: the group the user wants to query

    Raises:
        None

    Returns:
        the groups the member is joined to
    """
    def get_all_groups(self):
        return self.member_groups.copy()
    
    """allows a user to disconnect from a group
    Args:
        group: the group the user wants to leave

    Raises:
        None

    Returns:
        None
    """
    def disconnect(self):
        with self.sock_lock:
            self.connected = False
            self.sock.close()
        self.leave_all_groups()

    # to string
    def __str__(self):
        return f"{self.username} - Connected at {datetime.datetime.fromtimestamp(self.connection_time).strftime('%c')}"