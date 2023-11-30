from typing import List

import json
import datetime
import socket

# Function to read data from a socket
def read_socket(conn: socket.socket, buf=b""):
    # Read the length of the message
    while len(buf) < 4:
        tbuf = conn.recv(1024)
        if len(tbuf) == 0:
            return "", True, b""
        buf += tbuf

    num = int.from_bytes(buf[0:4], byteorder='big')

    buf = buf[4:]
    
    # Read the actual message data
    while len(buf) < num:
        tdata = conn.recv(1024)
        if len(tdata) == 0:
            return "", True, b""
        buf += tdata

    msg = buf[0:num].decode("utf-8")

    buf = buf[num:]

    return msg, False, buf


# Send the length of the message
def send_socket(sock, json_str: str):
    msg = json_str.encode('utf-8')
    total_bytes_sent = 0
    msglen = len(msg).to_bytes(4, byteorder = 'big')
    
    
    # Send the length of the message
    while total_bytes_sent < 4:
        total_bytes_sent +=\
            sock.send(msglen[total_bytes_sent:])

    total_bytes_sent = 0

    # Send the actual message data
    while total_bytes_sent < len(msg):
        total_bytes_sent +=\
            sock.send(msg[total_bytes_sent:])
    

# Function to send data through a socket for a specific user
def send_socket_user(user, json_str: str):
    with user.sock_lock:
        if not user.connected:
            return
        send_socket(user.sock, json_str)


# Function to send a status message to a user
def send_socket_msg(user, msg):
    json_str = {
        "type": "status",
        "data": msg
    }
    send_socket_user(user, json.dumps(json_str))

# Function to send different types of data to a user
def send_socket_data(type: str, user, data):
    json_msg: str
    match type:
        # Message or Group Message data
        case "users" | "groupusers":
            data: List[str]
            json_str = {
                "type": "user",
                "data": data
            }
            json_msg = json.dumps(json_str)

        case "message" | "groupmessage":
            data: List
            sanitized_data = []
            try:
                # format each message in the list
                for msg in data:
                    sanitized_data.append({
                        "id": msg.id,
                        "timestamp": datetime.datetime.fromtimestamp(msg.post_date).strftime("%Y-%m-%d %H:%M:%S"),
                        "sender": str(msg.sender),
                        "subject": msg.subject,
                        "body": msg.body
                    })
            except Exception as e:
                return
            json_str = {
                "type": "messages",
                "data": sanitized_data
            }
            json_msg = json.dumps(json_str)


        # Group data
        case "groups":
            data: List
            # Format group data
            data = [f"Group {i+1} id - {v.id}" for i, v in enumerate(data)]
            json_str = {
                "type": "groups",
                "data": data
            }
            json_msg = json.dumps(json_str)
    
    # Send the formatted data to the user
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