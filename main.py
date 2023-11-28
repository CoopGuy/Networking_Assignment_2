import time
import json
import datetime
from threading import Lock
from typing import List

import socket
import Server
from BulletinBoard import User, Message, Group, Response

HOST = "localhost"
PORT = 65100

def read_socket(conn: socket.socket):
    num = conn.recv(4)
    num = int.from_bytes(num, byteorder='big')
    if num > 100000: print("Large message from client received")
    msg = conn.recv(num).decode("utf-8")
    return msg

def send_socket(user: User, json_str: str):
    msg = json_str.encode('utf-8')
    total_bytes_sent = 0
    
    with user.sock_lock:
        msglen = len(msg).to_bytes(4, byteorder = 'big')
        while total_bytes_sent < 4:
            total_bytes_sent +=\
                user.sock.send(msglen[total_bytes_sent:])

        total_bytes_sent = 0

        while total_bytes_sent < len(msg):
            total_bytes_sent +=\
                user.sock.send(msg[total_bytes_sent:])

def send_socket_msg(user: User, msg):
    json_str = {
        "type": "status",
        "message": msg
    }
    send_socket(user, json.dumps(json_str))

def send_socket_data(type: str, user: User, data):
    json_msg: str
    match type:
        case "%users" | "%groupusers":

            data: List[str]
            json_str = {
                "type": "user",
                "data": data
            }
            json_msg = json.dumps(json_str)

        case "%message" | "%groupmessage":
            data: List[Message]
            sanitized_data = []
            for msg in data:
                sanitized_data.append({
                    "id": msg.id,
                    "timestamp": datetime.datetime.fromtimestamp(msg.post_date).strftime('%c'),
                    "sender": str(msg.sender),
                    "subject": msg.subject,
                    "body": msg.body
                })
            json_str = {
                "type": "user",
                "data": sanitized_data
            }
            json_msg = json.dumps(json_str)

        case "%groups":
            data: List[Group]
            data = [f"Group {i+1} id - {v.id}" for i, v in enumerate(data)]
            json_str = {
                "type": "groups",
                "data": data
            }
            json_msg = json.dumps(json_str)
    send_socket(user, json_msg)


username_pool = []
username_pool_lock = Lock()

singleboard: Group = Group(1)
multiboards: Group = [Group(i) for i in range(5)]

# singleboard_lock: Lock = Lock()
# multiboards_lock: Lock = Lock()

id = 0
id_lock: Lock = Lock()

def handleConnection(c):
    conn, addr = c
    sock_lock: Lock = Lock()
    user: User = User(conn, sock_lock)
    
    finished = False
    while not finished:
        try:
            msg, finished = read_socket(conn)
            if finished: continue
        except:
            #TODO: support bad message handling
            pass
        
        try:
            msg = json.load(msg)
        except:
            #TODO: support bad json format handling
            pass

        #TODO: handle json missing info
        if "command" not in msg.keys(): 
            pass
        if "args" not in msg.keys():
            pass

        if user.username == None and msg.command != "%username":
            send_socket_msg(user, "Error: No username selected")
        
        match msg.command:
            case "%username":
                username = msg.args.name
                with username_pool_lock:
                    if username not in username_pool:
                        username_pool.append(username)
                        user.username = username
                    else:
                        send_socket_msg(user, "Error: Username already in use")
            
            case "%join":
                if user.in_group(singleboard):
                    send_socket_msg(user, "You are already a member of that group")
                else:
                    user.leave_all_groups()
                    res: Response = user.join_group(singleboard)
                    if res.is_Ok():
                        send_socket_msg(user, "Successfully joined group")
                    else:
                        send_socket_msg(user, f"Error: {res.msg}")
            
            case "%post":
                with id_lock:
                    my_id = id
                    id += 1
                usrmsg: Message = Message(my_id, user, msg.args.subject, msg.args.body)
                res: Response = user.post_message(usrmsg)
                if res.is_OK():
                    send_socket_msg(user, "Successfully posted message")
                else:
                    send_socket_msg(user, "Error: Failed to post message")
            
            case "%users":
                send_socket_data("%users", user, user.get_users[1])
            
            case "%leave":
                res: Response = user.leave_group(singleboard)
                if res.is_Ok():
                    send_socket_msg(user, "Successfully left group")
                else:
                    send_socket_msg(user, f"Error: {res.msg}")
            
            case "%message":
                res: Response
                messages: List[Message]
                res, messages = user.get_messages()
                if res.is_Ok():
                    send_socket_data("%message", user, messages)
                else:
                    send_socket_msg(user, f"Error: {res.msg}")

            case "%exit":
                finished = True
            
            case "%groups":
                send_socket_data("%groups", user, user.get_all_groups())
            
            case "%groupjoin":
                try:
                    i = next(i for i, _ in enumerate(multiboards) if lambda x: x.id == msg.args.groupid)
                    user.join_group(multiboards[i])
                    send_socket_msg(user, f"Successfully joined group")
                except:
                    send_socket_msg(user, f"Failed to join group")

            
            case "%grouppost":
                with id_lock:
                    my_id = id
                    id += 1
                usrmsg: Message = Message(my_id, user, msg.args.subject, msg.args.body)
                res: Response = user.post_message(usrmsg)
                if res.is_OK():
                    send_socket_msg(user, "Successfully posted message")
                else:
                    send_socket_msg(user, "Error: Failed to post message")
            
            case "%groupusers":
                send_socket_data("%groupusers", user, user.get_users[1])
            
            case "%groupleave":
                try:
                    i = next(i for i, _ in enumerate(multiboards) if lambda x: x.id == msg.args.groupid)
                    user.leave_group(multiboards[i])
                    send_socket_msg(user, f"Successfully left group")
                except:
                    send_socket_msg(user, f"Failed to leave group")
            
            case "%groupmessage":
                res: Response
                messages: List[Message]
                res, messages = user.get_messages()
                if res.is_Ok():
                    send_socket_data("%groupmessage", user, messages)
                else:
                    send_socket_msg(user, f"Error: {res.msg}")
            
            case _:
                send_socket_msg(user, f"Error: unrecognized command")

    user.leave_all_groups()
    with username_pool_lock:
        username_pool.remove(user.username)

    return

if __name__ == "__main__":
    BulletinBoardListener = Server.Server(HOST, PORT, handleConnection)
    
    with BulletinBoardListener as BBL:
        t = 0
        while True:
            print(f"Server has been running for {t} seconds")
            time.sleep(10)
            t += 10