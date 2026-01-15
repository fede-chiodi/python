import socket

HOST = "0.0.0.0"
PORT = 50000

class SocketServer:
  def __init__(self, HOST, PORT, clientClass):
    self.HOST = HOST
    self.PORT = PORT
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.clients = []
    self.clientClass = clientClass

  def activate(self):
    self.socket.bind((self.HOST, self.PORT))
    self.socket.setblocking(False)
    self.socket.listen()
    print(f"Waiting for connections on port {self.HOST}:{self.PORT}...")
    try:
       while True:
         conn = None
         try:    
           conn, addr = self.socket.accept()
         except BlockingIOError:
           pass

         if conn:
            self.clients.append(self.clientClass(conn, addr, self.clients))
            print(f"New connection from {addr}")

         for client in self.clients[:]:  
             r = client.receive()
             if r != b'':
                 client.manage(r.decode().strip())
                 print(str(r)+f" from {client.addr}")
             if r == b'end':
                 client.close()
                 self.clients.remove(client) 
    except KeyboardInterrupt:
        print("Server is shutting down")

    for client in self.clients: 
        client.close()
    self.socket.close()

class SocketClient:
  def __init__(self, conn, addr, clients):
    self.conn = conn
    self.addr = addr
    self.clients = clients
    self.conn.setblocking(False)

  def receive(self):
    data = b''
    try:
      data = self.conn.recv(1024)
    except BlockingIOError:
      return b''
    if data != b'\r\n':
      return data
    else:
      return b''

  def send(self, text):
    self.conn.sendall(text.encode())

  def close(self):
    print(f"Closing connection from {self.addr}")
    self.conn.close()

  def manage(self, text):
    pass