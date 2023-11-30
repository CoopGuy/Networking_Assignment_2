import time
import json
from threading import Lock
from typing import List, Dict
import socket
import select

import Server
from BulletinBoard import User, Message, Group, Response
from ServerIO import send_socket_msg, send_socket_data, read_socket

username_pool = []
username_pool_lock = Lock()

singleboard: Group = Group(0)
multiboards: List[Group] = [Group(i) for i in range(1,6)]

def handleConnection(conn: socket.socket, addr):
    global process_exiting

    sock_lock: Lock = Lock()
    user: User = User(conn, sock_lock)
    buf = b""

    finished = False
    while not finished and not process_exiting:
        try:
            try:
                readable, writable, errored = select.select([conn], [], [], 1)
                skip = conn not in readable and conn not in errored
                if skip: continue
                msg, not_ok, buf = read_socket(conn, buf)
                if not_ok:
                    finished = True
                    continue
            except Exception as e:
                #TODO: support bad message handling
                continue
            
            try:
                msg: Dict = json.loads(msg)
            except:
                #TODO: support bad json format handling
                continue

            #TODO: handle json missing info
            if "command" not in msg.keys(): 
                continue
            if "args" not in msg.keys():
                continue

            if user.username == None and msg["command"] != "username":
                send_socket_msg(user, "Error: No username selected")
                continue
            
            match msg["command"]:
                case "username":
                    username = msg["args"]["name"]
                    with username_pool_lock: 
                        if username not in username_pool:
                            if user.username != None:
                                username_pool.remove(user.username)
                            username_pool.append(username)
                            user.username = username
                            send_socket_msg(user, "Successfully set username")
                        else:
                            send_socket_msg(user, "Error: Username already in use")
                
                case "join":
                    if user.in_group(singleboard):
                        send_socket_msg(user, "You are already a member of that group")
                    else:
                        user.leave_all_groups()
                        res: Response = user.join_group(singleboard)
                        if res.is_OK():
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
                    res, usrs = user.get_users(singleboard)
                    if len(usrs) == 0:
                        send_socket_msg(user, "No users connected to that group")
                    else:
                        send_socket_data("users", user, usrs)
                
                case "leave":
                    res: Response = user.leave_group(singleboard)
                    if res.is_OK():
                        send_socket_msg(user, "Successfully left group")
                    else:
                        send_socket_msg(user, f"Error: {res.msg}")
                
                case "message":
                    res: Response
                    message: Message
                    res, message = user.get_message(singleboard, msg["args"]["id"])

                    if res.is_OK():
                        send_socket_data("message", user, [message])
                    else:
                        send_socket_msg(user, f"Error: {res.msg}")

                case "exit":
                    finished = True
                
                case "groups":
                    send_socket_data("groups", user, multiboards)
                
                case "groupjoin":
                    try:
                        i = next(i for i, x in enumerate(multiboards) if x.id == msg["args"]["groupid"])
                        res: Message = user.join_group(multiboards[i])
                        if res.is_OK():
                            send_socket_msg(user, f"Successfully joined group {multiboards[i].id}")
                        else:
                            send_socket_msg(user, f"Error: {res.msg}")
                    except Exception as e:
                        send_socket_msg(user, f"Failed to join group")
                
                case "grouppost":
                    try:
                        i = next(i for i, x in enumerate(multiboards) if x.id == msg["args"]["groupid"])
                    except Exception as e:
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
                        res: Response = user.leave_group(multiboards[i])
                        if res.is_OK():
                            send_socket_msg(user, "Successfully left group")
                        else:
                            send_socket_msg(user, f"Error: {res.msg}")
                    except:
                        send_socket_msg(user, f"Error: Failed to leave group")

                case "groupmessage":
                    try:
                        i = next(i for i, x in enumerate(multiboards) if x.id == msg["args"]["groupid"])
                    except:
                        send_socket_msg(user, f"Error: Invalid group")
                        continue

                    res: Response
                    message: Message
                    res, message = user.get_message(multiboards[i], msg["args"]["msgid"])
                    
                    if res.is_OK():
                        send_socket_data("groupmessage", user, message)
                    else:
                        send_socket_msg(user, f"Error: {res.msg}")
                
                case _:
                    send_socket_msg(user, f"Error: unrecognized command")
        except ConnectionResetError as e:
            print(f"User {user.username} forcibly disconnected")
            with username_pool_lock: 
                if user.username in username_pool:
                    username_pool.remove(user.username)

        except Exception as e:
            send_socket_msg(user, f"Error: Failed to execute %{msg['command']}")
            pass

    user.leave_all_groups()
    with username_pool_lock:
        username_pool.remove(user.username)
    
    conn.close()
    print(f"{user.username} has disconnected")
    return

process_exiting = False
if __name__ == "__main__":
    HOST = "localhost"
    PORT = 65100

    BulletinBoardListener = Server.Server(HOST, PORT, handleConnection)
    with BulletinBoardListener as BBL:
        try:
            while True:
                time.sleep(10)
        except Exception as e:
            pass
    process_exiting = True