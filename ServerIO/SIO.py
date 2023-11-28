from BulletinBoard import User, Message, Group
from typing import List

import json
import datetime

def send_socket(sock, json_str: str):
    msg = json_str.encode('utf-8')
    total_bytes_sent = 0
    msglen = len(msg).to_bytes(4, byteorder = 'big')
    while total_bytes_sent < 4:
        total_bytes_sent +=\
            sock.send(msglen[total_bytes_sent:])

    total_bytes_sent = 0

    while total_bytes_sent < len(msg):
        total_bytes_sent +=\
            sock.send(msg[total_bytes_sent:])

def send_socket_user(user: User, json_str: str):
    with user.sock_lock:
        if not user.connected:
            return
        send_socket(user.sock, json_str)
        

def send_socket_msg(user: User, msg):
    json_str = {
        "type": "status",
        "data": msg
    }
    send_socket_user(user, json.dumps(json_str))

def send_socket_data(type: str, user: User, data):
    json_msg: str
    match type:
        case "users" | "groupusers":

            data: List[str]
            json_str = {
                "type": "user",
                "data": data
            }
            json_msg = json.dumps(json_str)

        case "message" | "groupmessage":
            data: List[Message]
            sanitized_data = []
            for msg in data:
                sanitized_data.append({
                    "id": msg.id,
                    "timestamp": datetime.datetime.fromtimestamp(msg.post_date).strftime('c'),
                    "sender": str(msg.sender),
                    "subject": msg.subject,
                    "body": msg.body
                })
            json_str = {
                "type": "messages",
                "data": sanitized_data
            }
            json_msg = json.dumps(json_str)

        case "groups":
            data: List[Group]
            data = [f"Group {i+1} id - {v.id}" for i, v in enumerate(data)]
            json_str = {
                "type": "groups",
                "data": data
            }
            json_msg = json.dumps(json_str)
    send_socket_user(user, json_msg)

"""

/*
type can be one of the following:
    status: 
        data is a string to print to the user
    user: 
        data is a list of strings, each string is a string representing a user
    messages: 
        data is a list of dictionaries of the format:
        {
            "id": msg.id, //int
            "timestamp": datetime.datetime.fromtimestamp(msg.post_date).strftime('%c'),//str
            "sender": str(msg.sender),//str
            "subject": msg.subject,//str
            "body": msg.body//str
        }
    groups: 
        data is a list of strings, each is a string representing a user
*/

{
    "type": "messages",
    "data": data
}
"""