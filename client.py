import socket
import threading
import json
import select

from ServerIO import send_socket, read_socket

class Client:
    def __init__(self, server_host, server_port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_thread: threading.Thread = None
        self.connected = False
        self.should_disconnect = False

    def connect_to_server(self, host, port):
        self.socket.connect((host, int(port)))
        self.connected = True
        try:
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.start()
        except:
            self.connected = False
            raise
        print("Connected to the server.")

    def disconnect_from_server(self, noprint=False):
        self.connected = False
        self.receive_thread.join()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_thread = None
        if not noprint: print("Successfully disconnected from server")

    def send_message(self, command: str):
        # parse into arguments
        if self.should_disconnect:
            self.should_disconnect = False
            self.disconnect_from_server(noprint=True)

        listofargs = command.split(" ")
        
        if not self.connected and listofargs[0].removeprefix("%").lower() != "connect":
            print("Must connect to server first")
            return

        match listofargs[0].removeprefix("%").lower():
            case "connect":
                try:
                    self.connect_to_server(listofargs[1], listofargs[2])               
                except:
                    print("Failed to connect to server")

                try:
                    self.send_message(" ".join(["%username", listofargs[3]]))
                except:
                    pass
                return

            case "username":
                command = "username"
                args = {
                    "name": listofargs[1]
                }

            case "join":
                command = "join"
                args = {}

            case "post":
                command = "post"
                args = {
                    "subject": listofargs[1],
                    "body": " ".join(listofargs[2:])
                }

            case "users":
                command = "users"
                args = {}
                
            case "leave":
                command = "leave"
                args = {}
                
            case "message":
                command = "message"
                args = {
                    "id": int(listofargs[1])
                }

            case "exit":
                self.disconnect_from_server()
                return
                
            case "groups":
                command = "groups"
                args = {}

            case "groupjoin":
                command = "groupjoin"
                args = {
                    "groupid": int(listofargs[1])
                }

            case "grouppost":
                command = "grouppost"
                args = {
                    "groupid": listofargs[1],
                    "subject": listofargs[2],
                    "body": " ".join(listofargs[3:])
                }
                
            case "groupusers":
                command = "groupusers"
                args = {
                    "groupid": int(listofargs[1])
                }

            case "groupleave":
                command = "groupleave"
                args = {
                    "groupid": int(listofargs[1])
                }
            
            case "groupmessage":
                command = "groupmessage"
                args = {
                    "groupid": int(listofargs[1]),
                    "msgid": int(listofargs[2])
                }
            
            case _:
                raise Exception("Invalid command")
        
        # create str for sending to server
        json_str = json.dumps({
            "command": command,
            "args": args
        })

        send_socket(self.socket, json_str)

    def receive_messages(self):
        global process_exiting
        buf = b""
        while self.connected and not process_exiting:
            try:
                readable, writable, errored = select.select([self.socket], [], [], 1)
                if self.socket not in readable and self.socket not in errored:
                    continue
                msg, not_ok, buf = read_socket(self.socket, buf)
                if not_ok:
                    raise ConnectionResetError()
                else:
                    msg = json.loads(msg)
                    if msg["type"] == "status":
                        print(msg["data"])
                    elif msg["type"] == "user":
                        print(msg["data"][0])
                    elif msg["type"] == "groups":
                        print(msg["data"])
                    else:
                        msg["type"] == "messages"
                        msgData = msg["data"][0]
                        for x in msgData.keys():
                            print(f"{x.capitalize()}: {msgData[x]}")
                        print("")
            except ConnectionResetError:
                print("Connection to the server lost.")
                self.should_disconnect = True
                break
            except Exception as e:
                pass
        self.socket.close()

    def run(self):
        while True:
            command = input("\nEnter a command: %join, %leave, %post, %message, %exit: \n")
            try:
                self.send_message(command)
            except:
                print("Invalid Command")
                
process_exiting = False
if __name__ == "__main__":
    server_host = "localhost"  
    server_port = 65101 

    client = Client(server_host, server_port)
    try:
        client.run()
    except KeyboardInterrupt:
        process_exiting = True
