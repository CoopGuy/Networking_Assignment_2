import time
import json
from threading import Lock
from typing import List

import socket
import Server
from BulletinBoard import User, Message, Group, Response

HOST = "localhost"
PORT = 65100

def read_socket(conn: socket.socket):
    num = conn.recv(4)
    #TODO: convert num bytes to an int
    msg = conn.recv(num)
    #TODO: convert msg from bytes to string
    return msg

def send_socket_msg(user: User, msg):
    pass

def send_socket_data(user: User, *kwargs):
    pass

username_pool = []
username_pool_lock = Lock()

singleboard: Group = Group(1)
multiboards: Group = [Group(i) for i in range(5)]

singleboard_lock: Lock = Lock()
multiboards_lock: Lock = Lock()

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
            case ["%username"]:
                username = msg.args.name
                with username_pool_lock:
                    if username not in username_pool:
                        username_pool.append(username)
                        user.username = username
                    else:
                        send_socket_msg(user, "Error: Username already in use")
            
            case ["%join"]:
                if user.in_group(singleboard):
                    send_socket_msg(user, "You are already a member of that group")
                else:
                    user.leave_all_groups()
                    res: Response = user.join_group(singleboard)
                    if res.is_Ok():
                        send_socket_msg(user, "Successfully joined group")
                    else:
                        send_socket_msg(user, f"Error: {res.msg}")
            
            case ["%post"]:
                usrmsg: Message = Message(user, msg.args.subject, msg.args.body)
                res: Response = user.post_message(usrmsg)
                if res.is_OK():
                    send_socket_msg(user, "Successfully posted message")
                else:
                    send_socket_msg(user, "Error: Failed to post message")
            
            case ["%users"]:
                send_socket_data(user, user.get_users[1])
            
            case ["%leave"]:
                res: Response = user.leave_group(singleboard)
                if res.is_Ok():
                    send_socket_msg(user, "Successfully left group")
                else:
                    send_socket_msg(user, f"Error: {res.msg}")
            
            case ["%message"]:
                res: Response
                messages: List[Message]
                res, messages = user.get_messages()
                if res.is_Ok():
                    send_socket_data(user, messages)
                else:
                    send_socket_msg(user, f"Error: {res.msg}")

            case ["%exit"]:
                finished = True
            
            case ["%groups"]:
                send_socket_data(user, user.get_all_groups())
            
            case ["%groupjoin"]:
                try:
                    i = next(i for i, _ in enumerate(multiboards) if lambda x: x.id == msg.args.groupid)
                    user.join_group(multiboards[i])
                    send_socket_msg(user, f"Successfully joined group")
                except:
                    send_socket_msg(user, f"Failed to join group")

            
            case ["%grouppost"]:
                usrmsg: Message = Message(user, msg.args.subject, msg.args.body)
                res: Response = user.post_message(usrmsg)
                if res.is_OK():
                    send_socket_msg(user, "Successfully posted message")
                else:
                    send_socket_msg(user, "Error: Failed to post message")
            
            case ["%groupusers"]:
                send_socket_data(user, user.get_users[1])
            
            case ["%groupleave"]:
                try:
                    i = next(i for i, _ in enumerate(multiboards) if lambda x: x.id == msg.args.groupid)
                    user.leave_group(multiboards[i])
                    send_socket_msg(user, f"Successfully left group")
                except:
                    send_socket_msg(user, f"Failed to leave group")
            
            case ["%groupmessage"]:
                res: Response
                messages: List[Message]
                res, messages = user.get_messages()
                if res.is_Ok():
                    send_socket_data(user, messages)
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