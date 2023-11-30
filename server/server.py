import socket, threading, select
from typing import List

class Server:
    """
        Initialize the Server object.

        Parameters:
        - HOST: The host address to bind the server to.
        - PORT: The port number to bind the server to.
        - HANDLER: The handler function to be executed for each incoming connection.
        - MAX_BACKLOG: Maximum number of queued connections (default is 5).
        """
        
    def __init__(self, HOST, PORT, HANDLER, MAX_BACKLOG = 5):
        self.HOST = HOST
        self.PORT = PORT
        self.MAX_BACKLOG = MAX_BACKLOG
        self.HANDLER = HANDLER
        self.running_handlers: List[threading.Thread] = []
        self.lock: threading.Lock = threading.Lock()
        self.__listener__: threading.Thread = None
        self.__running__: bool = False

    def start(self):
        """
        Start the server by creating a socket, binding to the specified address and port,and listening for incoming connections. Also, start a separate thread to handle incoming connections concurrently.
        """
        if self.__running__:
            raise RuntimeError("Server already started")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.HOST, self.PORT))
        self.socket.listen(self.MAX_BACKLOG)
        self.__listener__ = threading.Thread(
            target=self.__listen_and_disbatch
        )
        self.__running__ = True
        self.__listener__.start()

    def __listen_and_disbatch(self):
        """
        Listen for incoming connections and dispatch them to handler threads.
        """
        while self.__running__:
            readable, writable, errored = select.select([self.socket], [], [], 1)
            if self.socket not in readable:
                continue
            conn = self.socket.accept()
            ct = threading.Thread(target=self.HANDLER, args=conn)
            print(f"New connection from {conn[1]} accepted")
            ct.start()
            with self.lock:
                self.running_handlers.append(ct)

    def stop(self):
        """
        Stop the server by setting the running flag to False, joining the listener thread, and joining all the running handler threads.
        """
        self.__running__ = False
        if self.__listener__.is_alive():
            self.__listener__.join()
        for i in self.running_handlers:
            i.join()

    def __enter__(self):
        """
        Enter method for context management. Start the server when entering a block.
        """
        self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit method for context management. Stop the server when exiting a block.
        """
        self.stop()

