import socket, threading, select
from typing import List

class Server:
    def __init__(self, HOST, PORT, HANDLER, MAX_BACKLOG = 5):
        self.HOST = HOST
        self.PORT = PORT
        self.MAX_BACKLOG = MAX_BACKLOG
        self.HANDLER = lambda self, *x: HANDLER(*x)
        self.running_handlers: List[threading.Thread] = []
        self.lock: threading.Lock = threading.Lock()
        self.__listener__: threading.Thread = None
        self.__socket__: socket.socket = None
        self.__running__: bool = False

    def start(self):
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
        while self.__running__:
            readable, writable, errored = select.select([self.socket], [], [], 1)
            if self.socket in readable:
                conn = self.socket.accept()
                ct = threading.Thread(target=self.HANDLER, args=(conn))
                print(f"New connection from {conn[1]} accepted")
                ct.start()
                with self.lock:
                    self.running_handlers.append(ct)
                

    def stop(self):
        self.__running__ = False
        if self.__listener__.is_alive():
            self.__listener__.join()
        for i in self.running_handlers:
            i.join()

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

