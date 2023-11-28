import time
import Server

HOST = "localhost"
PORT = 65100

def handleConnection(c):
    conn, addr = c
    faddr = f"{conn}:{addr}"
    for i in range(5):
        print(f"Hi from thread handling {faddr}")
        time.sleep(10)
    print(f"Thread handling {faddr} closing")
    return

if __name__ == "__main__":
    BulletinBoardListener = Server.Server(HOST, PORT, handleConnection)
    
    with BulletinBoardListener as BBL:
        t = 0
        while t < 50:
            print(f"Server has been running for {t} seconds")
            time.sleep(10)
            t += 10