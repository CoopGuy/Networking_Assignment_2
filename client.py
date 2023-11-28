import socket
import threading
import json

BUFFER_SIZE = 1024
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def handle_server_messages():
    while True:
        try:
            msg = client.recv(BUFFER_SIZE)
            if msg:
                msg_json = json.loads(msg)
                if msg_json.get("type") == "exit":
                    print("[DISCONNECTED] Disconnected from the server.")
                    break
                elif msg_json.get("type") == "message":
                    print(f"Message ID: {msg_json['message_id']}, Sender: {msg_json['sender']}, Post Date: {msg_json['post_date']}, Subject: {msg_json['subject']}")
                elif msg_json.get("type") == "user_list":
                    print(f"Users in the group: {', '.join(msg_json['users'])}")
                elif msg_json.get("type") == "group_list":
                    print(f"Available groups: {', '.join(msg_json['groups'])}")
                elif msg_json.get("type") == "group_message":
                    print(f"Group Message ID: {msg_json['message_id']}, Sender: {msg_json['sender']}, Post Date: {msg_json['post_date']}, Subject: {msg_json['subject']}")
                else:
                    print(f"[UNKNOWN MESSAGE] {msg_json}")
            else:
                break
        except Exception as e:
            print(f"[ERROR] {e}")
            break

def send_message(msg_type, **kwargs):
    message = {"type": msg_type, **kwargs}
    client.send(json.dumps(message).encode())

def connect_to_server(address, port):
    try:
        client.connect((address, port))
        print(f"[CONNECTED] Successfully connected to {address}:{port}")
        server_thread = threading.Thread(target=handle_server_messages)
        server_thread.start()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to {address}:{port}. Error: {e}")
        return False

def main():
    connected = False
    while not connected:
        cmd = input()
        if cmd.startswith("%connect"):
            _, address, port_str = cmd.split()
            port = int(port_str)
            print(f"[CONNECTING] Trying to connect to {address}:{port}...")
            connected = connect_to_server(address, port)

    while True:
        user_input = input("Enter command: ")
        if user_input.startswith("%post"):
            _, subject, content = user_input.split(" ", 2)
            send_message("post", subject=subject, content=content)
        elif user_input == "%users":
            send_message("get_users")
        elif user_input == "%leave":
            send_message("leave")
        elif user_input == "%message":
            message_id = input("Enter message ID: ")
            send_message("get_message", message_id=message_id)
        elif user_input == "%groups":
            send_message("get_groups")
        elif user_input.startswith("%groupjoin"):
            _, group_id = user_input.split()
            send_message("join_group", group_id=group_id)
        elif user_input.startswith("%grouppost"):
            _, group_id, subject, content = user_input.split(" ", 3)
            send_message("post_group", group_id=group_id, subject=subject, content=content)
        elif user_input == "%groupusers":
            send_message("get_group_users")
        elif user_input.startswith("%groupleave"):
            _, group_id = user_input.split()
            send_message("leave_group", group_id=group_id)
        elif user_input.startswith("%groupmessage"):
            _, group_id, message_id = user_input.split()
            send_message("get_group_message", group_id=group_id, message_id=message_id)
        elif user_input == "%exit":
            send_message("exit")
            break
        else:
            print("[UNKNOWN COMMAND]")

if __name__ == "__main__":
    main()
