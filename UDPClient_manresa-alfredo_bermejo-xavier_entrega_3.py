from socket import *
import os

def main():

  clientSocket = socket(AF_INET, SOCK_DGRAM)

  serverName = 'localhost'#input('ip servidor: ')
  serverPort = 12000#input('puerto servidor: ')

  condiciones = False
  while not condiciones:
      # Read in some text from the user
      sendPack = input("Input (Example: GET hola.txt 32): ")

      commands = sendPack.split(" ")
      
      method = commands[0]
      filename = commands[1]
      CHUNK_SIZE = int(commands[2])

      if CHUNK_SIZE == 32 or CHUNK_SIZE == 64 or CHUNK_SIZE == 128 or CHUNK_SIZE == 256 or CHUNK_SIZE == 512 or CHUNK_SIZE == 1024 or CHUNK_SIZE == 2048:
          condiciones = True

  clientSocket.sendto(str(CHUNK_SIZE).encode(), (serverName, serverPort))

  if method.upper() == 'GET':

    clientSocket.sendto(createRRQ(filename, 'netascii'), (serverName, serverPort))

    file = open(filename + ".2", "wb")

    while True:

      data, _ = clientSocket.recvfrom(CHUNK_SIZE)

      packetType = data[:2]

      if packetType == b'03':  # DATA
        # guardamos datos
        file.write(data[4:])
        clientSocket.sendto(createACK(data[2:4]), (serverName, serverPort))
      elif packetType == b'05':  # ERR
        # error
        file.close()
        print('Code: Message:', data[2:4].decode(), data[4:].decode())

      print("packet size recv:", len(data))

      if len(data) < CHUNK_SIZE:
        # sabemos que es el ultimo paquete enviado para que se para de guardar en el archivo
        file.close()
        break

  elif method.upper() == 'PUT':
    
    clientSocket.sendto(createWRQ(filename, 'netascii'), (serverName, serverPort))

    serverACK, _ = clientSocket.recvfrom(CHUNK_SIZE)

    print(serverACK)

    contador = 1
    file = open(filename, "rb")
    data = file.read(CHUNK_SIZE - 4)
    while data:
      clientSocket.sendto(createDATA(contador, data), (serverName, serverPort))
      contador = (contador % 65535) + 1
      serverACK, _ = clientSocket.recvfrom(CHUNK_SIZE)
      print(serverACK)
      data = file.read(CHUNK_SIZE - 4)
      
    if (os.path.getsize(filename) % CHUNK_SIZE) == 0:
        clientSocket.sendto(createDATA(contador, ''), (serverName, serverPort))
      
    file.close()

  clientSocket.close()
      

def createRRQ(nombrefichero, modo):
  packet = b''
  packet += b'01'
  packet += nombrefichero.encode()
  packet += b'0'
  packet += modo.encode()
  packet += b'0'
  return packet

def createWRQ(nombrefichero, modo):
  packet = b''
  packet += b'02'
  packet += nombrefichero.encode()
  packet += b'0'
  packet += modo.encode()
  packet += b'0'
  return packet

def createDATA(numbloque, data):
  packet = b''
  packet += b'03'
  packet += "{:02d}".format(numbloque).encode()
  packet += data  # is already encoded
  return packet
    
def createACK(numbloque):
  packet = b''
  packet += b'04'
  packet += "{:02d}".format(int(numbloque)).encode()
  return packet

def createERROR(codigoerror, mensajeerror):
  packet = b''
  packet += b'05'
  packet += codigoerror.encode()
  packet += mensajeerror.encode()
  packet += b'0'
  return packet

if __name__ == "__main__":
  main()