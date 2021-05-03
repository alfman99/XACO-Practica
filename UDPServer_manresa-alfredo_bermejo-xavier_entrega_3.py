from socket import *
import os


def main():

  serverPort = 12000#input('puerto servidor: ')

  CHUNK_SIZE = 512  # default value to get def size on first packet

  serverSocket = socket(AF_INET, SOCK_DGRAM)
  serverSocket.bind(('', serverPort))

  print ('El Servidor esta listo para recibir')
  while True:

    clientMSG, clientAddr = serverSocket.recvfrom(CHUNK_SIZE)
    CHUNK_SIZE = int(clientMSG.decode())

    clientMSG, clientAddr = serverSocket.recvfrom(CHUNK_SIZE)
   
    # Enviar info al cliente
    if clientMSG[0:2].decode() == '01':
      name = clientMSG.decode()[2:2+clientMSG[2:].decode().index('0')]
      contador = 1
      file = open(name, "rb")
      data = file.read(CHUNK_SIZE - 4)
      while data:
        serverSocket.sendto(createDATA(contador, data), clientAddr)
        contador = (contador % 65535) + 1
        clientACK, _ = serverSocket.recvfrom(CHUNK_SIZE)
        print(clientACK)
        data = file.read(CHUNK_SIZE - 4)
        

      if (os.path.getsize(name) % (CHUNK_SIZE - 4)) == 0:
        serverSocket.sendto(createDATA(contador, ''), clientAddr)

      file.close()

    # recibir info del cliente
    elif clientMSG[0:2].decode() == '02':
      name = clientMSG.decode()[2:2+clientMSG[2:].decode().index('0')]

      file = open(name + ".2", "wb")

      serverSocket.sendto(createACK('0'), clientAddr)

      
      while True:

        data, _ = serverSocket.recvfrom(CHUNK_SIZE)

        packetType = data[:2]

        if packetType == b'03':  # DATA
          # guardamos datos
          file.write(data[4:])
          serverSocket.sendto(createACK(data[2:4]), clientAddr)

        elif packetType == b'05':  # ERR
          # error
          file.close()
          print('Code: Message:',  data[2:4].decode(),  data[4:].decode())

        print("packet size recv: ", len(data))

        print(len(data))
        if len(data) < CHUNK_SIZE:
          # sabemos que es el ultimo paquete enviado para que se para de guardar en el archivo
          file.close()
          break

    # no es un put o un get en el momento adecuado
    else:
        pass




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