import socket
import threading
import json

from ServerIO import send_socket
#usage send_socket(sock, json.dumps(dict))

class Client:
    def __init__(self, server_host, server_port):
        self.username = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.receive_thread = None

    def connect_to_server(self, host, port):
        self.socket.connect((host, int(port)))
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.start()
        self.connected = True
        print("Connected to the server.")

    def disconnect_from_server(self):
        self.connected = False

    def send_message(self, command: str):
        # parse into arguments
        
        listofargs = command.split(" ")
        
        #["%post", "id", "subject"]
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
                    self.send_message(" ".join(["%username", listofargs[2]]))
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
                    "id": listofargs[1]
                }

            case "exit":
                self.socket.close()
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connected = False
                print("Successfully disconnected from server")
                return
                
            case "groups": # begin group section
                command = "groups"
                args = {}

            case "groupjoin":
                command = "groupjoin"
                args = {
                    "groupid": listofargs[1]
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
                    "groupid": listofargs[1]
                }

            case "groupleave":
                command = "groupleave"
                args = {
                    "groupid": listofargs[1]
                }
            case "groupmessage":
                command = "groupmessage"
                args = {
                    "groupid": listofargs[1],
                    "msgid": listofargs[2]
                }
            case _:
                pass
        
        # create dictionary
        json_str = json.dumps({
            "command": command,
            "args": args
        })
        send_socket(self.socket, json_str)

    def receive_messages(self):
        while self.connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                print(data.decode())
            except ConnectionResetError:
                print("Connection to the server lost.")
                break
        self.socket.close()

    def run(self):
        while True:
            command = input("Enter a command: %join, %leave, %post, %retrieve, %exit: \n")
            try:
                self.send_message(command)
            except:
                print("Invalid Command")
                

if __name__ == "__main__":
    server_host = "localhost"  
    server_port = 65100  

    client = Client(server_host, server_port)
    client.run()
