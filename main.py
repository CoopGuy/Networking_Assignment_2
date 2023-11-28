import time
import json
import datetime
from threading import Lock
from typing import List

import socket
import Server
from BulletinBoard import User, Message, Group, Response
from ServerIO import send_socket_msg, send_socket_data
HOST = "localhost"
PORT = 65100

def read_socket(conn: socket.socket):
    num = conn.recv(4)
    num = int.from_bytes(num, byteorder='big')
    if num > 100000: print("Large message from client received")
    msg = conn.recv(num).decode("utf-8")
    return msg


username_pool = []
username_pool_lock = Lock()

singleboard: Group = Group(1)
multiboards: List[Group] = [Group(i) for i in range(5)]

# singleboard_lock: Lock = Lock()
# multiboards_lock: Lock = Lock()

def handleConnection(c):
    conn, addr = c
    sock_lock: Lock = Lock()
    user: User = User(conn, sock_lock)
    
    finished = False
    while not finished:
        try:
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

            if user.username == None and msg.command != "username":
                send_socket_msg(user, "Error: No username selected")
            
            match msg.command:
                case "username":
                    username = msg["args"]["name"]
                    with username_pool_lock:
                        if username not in username_pool:
                            username_pool.append(username)
                            user.username = username
                        else:
                            send_socket_msg(user, "Error: Username already in use")
                
                case "join":
                    if user.in_group(singleboard):
                        send_socket_msg(user, "You are already a member of that group")
                    else:
                        user.leave_all_groups()
                        res: Response = user.join_group(singleboard)
                        if res.is_Ok():
                            send_socket_msg(user, "Successfully joined public group")
                        else:
                            send_socket_msg(user, f"Error: {res.msg}")
                
                case "post":
                    usrmsg: Message = Message(None, user, msg["args"]["subject"], msg["args"]["body"])
                    res: Response = user.post_message(singleboard, usrmsg)
                    if res.is_OK():
                        send_socket_msg(user, "Successfully posted message")
                    else:
                        send_socket_msg(user, f"Error: {res.msg}")
                
                case "users":
                    send_socket_data("users", user, user.get_users(singleboard)[1])
                
                case "leave":
                    res: Response = user.leave_group(singleboard)
                    if res.is_Ok():
                        send_socket_msg(user, "Successfully left group")
                    else:
                        send_socket_msg(user, f"Error: {res.msg}")
                
                case "message":
                    res: Response
                    message: Message
                    res, message = user.get_message(singleboard, msg["args"]["id"])

                    if res.is_Ok():
                        send_socket_data("message", user, message)
                    else:
                        send_socket_msg(user, f"Error: {res.msg}")

                case "exit":
                    finished = True
                
                case "groups":
                    send_socket_data("groups", user, user.get_all_groups())
                
                case "groupjoin":
                    try:
                        i = next(i for i, x in enumerate(multiboards) if x.id == msg["args"]["groupid"])
                        user.join_group(multiboards[i])
                        send_socket_msg(user, f"Successfully joined group")
                    except:
                        send_socket_msg(user, f"Failed to join group")
                
                case "grouppost":
                    try:
                        i = next(i for i, x in enumerate(multiboards) if x.id == msg["args"]["groupid"])
                    except:
                        send_socket_msg(user, "Error: Invalid group")
                        continue
                    usrmsg: Message = Message(None, user, msg["args"]["subject"], msg["args"]["body"])
                    res: Response = user.post_message(multiboards[i], usrmsg)
                    if res.is_OK():
                        send_socket_msg(user, "Successfully posted message")
                    else:
                        send_socket_msg(user, "Error: Failed to post message")
                
                case "groupusers":
                    try:
                        i = next(i for i, x in enumerate(multiboards) if x.id == msg["args"]["groupid"])
                    except:
                        send_socket_msg(user, "Error: Invalid group")
                        continue

                    send_socket_data("groupusers", user, user.get_users(multiboards[i])[1])
                
                case "groupleave":
                    try:
                        i = next(i for i, x in enumerate(multiboards) if x.id == msg["args"]["groupid"])
                        user.leave_group(multiboards[i])
                        send_socket_msg(user, f"Successfully left group")
                    except:
                        send_socket_msg(user, f"Error: Failed to leave group")
                
                case "groupmessage":
                    res: Response
                    messages: List[Message]
                    try:
                        i = next(i for i, x in enumerate(multiboards) if x.id == msg["args"]["groupid"])
                    except:
                        send_socket_msg(user, f"Error: Invalid group")

                    res, messages = user.get_message(multiboards[i], msg["args"]["msgid"])

                    if res.is_Ok():
                        send_socket_data("groupmessage", user, messages)
                    else:
                        send_socket_msg(user, f"Error: {res.msg}")
                
                case _:
                    send_socket_msg(user, f"Error: unrecognized command")
        except:
            send_socket_msg(user, f"Error: Failed to execute %{msg['command']}")
            pass


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