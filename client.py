import socket
import threading
import json

from ServerIO import send_socket
#usage send_socket(sock, json.dumps(dict))

class Client:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.username = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self):
        self.socket.connect((self.server_host, self.server_port))
        print("Connected to the server.")


    def send_message(self, command: str):
        # parse into arguments
        
        listofargs = command.split(" ")
        
        #["%post", "id", "subject"]
        match listofargs[0].removeprefix("%"):
            case "connect":
                try:
                    self.connect_to_server(listofargs[1], listofargs[2])                    
                except:
                    print("Failed to connect to server")

                try:
                    self.send_message(listofargs[3])
                except:
                    pass

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
                command = "exit"
                args = {}
                
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
        while True:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                print(data.decode())
            except ConnectionResetError:
                print("Connection to the server lost.")
                break
            
            
    
    def run(self):
        self.connect_to_server()

        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()

        while True:
            command = input("Enter a command: %join, %leave, %post, %retrieve, %exit: \n").upper()
            try:
                self.send_message(command)
            except:
                if command == "%join":
                    self.username = input("Enter a non-existent username to join: ")
                    self.send_message(f"%join {self.username}")

                elif command == "%leave":
                    self.send_message("%leave")
                    break

                elif command == "%post":
                    message_content = input("Enter your message: ")
                    self.send_message(f"%post {message_content}")

                elif command == "%retrieve":
                    message_id = input("Enter the message ID to retrieve: ")
                    self.send_message(f"%retrieve {message_id}")

                elif command == "%exit":
                    self.send_message("%exit")
                    break

                else:
                    print("Invalid command. Please enter: %join, %leave, %post, %retrieve, %exit")

if __name__ == "__main__":
    server_host = "localhost"  
    server_port = 65100  

    client = Client(server_host, server_port)
    client.run()
