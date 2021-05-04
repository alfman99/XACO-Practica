from socket import *
import os

class Server:

  def __init__(self, serverPort, blockSize, timeout):
    self.socket = socket(AF_INET, SOCK_DGRAM)
    self.serverPort = serverPort
    self.blockSize = blockSize
    self.timeout = timeout
    self.clientAddr = None
    self.socket.bind(('', self.serverPort))

  def setupHandler(self):
    data = self.recvPacket(4)
    packetType = data[:2]
    filename = data.decode('utf-8')[2:2+data[2:].decode().index('\0')]

    if packetType == b'01':
      print('GET')
      self.handleGET(filename)
      print('Ended sending file:', filename, 'to client:', self.clientAddr)
    elif packetType == b'02':
      print('PUT')
      self.handlePUT(filename)
      print('Ended reciving file:', filename, 'from client:', self.clientAddr)


  def handleGET(self, filename):

    contador = 1

    file = open(filename, "rb")

    data = file.read(self.blockSize)

    while data != b'':
      packet = self.createDATA(contador, data)
      self.sendPacket(packet)

      clientACK = self.recvPacket(4)

      print('Num seq:', contador)
      contador = (contador % pow(2, 16)) + 1

      data = file.read(self.blockSize)

      if data == b'' and self.extraEmpty(filename):
        packet = self.createDATA(contador, b'')
        self.sendPacket(packet)

  def handlePUT(self, filename):
    packet = self.createACK(0)
    self.sendPacket(packet)

    

    file = open(filename, 'wb')

    while True:

      data = self.recvPacket(4)

      packetNum = int.from_bytes(data[2:4], 'big')
      packetData = data[4:]

      file.write(packetData)

      packet = self.createACK(packetNum + 1)
      self.sendPacket(packet)


      if len(data) < (self.blockSize + 4):
        file.close()
        break


  def extraEmpty(self, filename: str) -> bool:
    return (os.path.getsize(filename) % self.blockSize) == 0

  def sendPacket(self, packet: bytearray) -> None:
    self.socket.sendto(packet, self.clientAddr)

  def recvPacket(self, headerSize: int) -> bytes:
    data, clientAddr = self.socket.recvfrom(self.blockSize + headerSize)
    self.clientAddr = clientAddr
    return data

  def createRRQ(self, nombrefichero: str, modo: str) -> bytearray:
    packet = b''
    packet += b'01'
    packet += nombrefichero.encode()
    packet += b'0'
    packet += modo.encode()
    packet += b'0'
    return packet

  def createWRQ(self, nombrefichero: str, modo: str) -> bytearray:
    packet = b''
    packet += b'02'
    packet += nombrefichero.encode()
    packet += b'0'
    packet += modo.encode()
    packet += b'0'
    return packet

  def createDATA(self, numbloque: int, data: bytearray) -> bytearray:
    packet = b''
    packet += b'03'
    packet += numbloque.to_bytes(2, 'big')
    packet += data
    return packet

  def createACK(self, numbloque: int) -> bytearray:
    packet = b''
    packet += b'04'
    packet += numbloque.to_bytes(2, 'big')
    return packet

  def createERROR(self, codigoerror: str, mensajeerror: str) -> bytearray:
    packet = b''
    packet += b'05'
    packet += codigoerror.encode()
    packet += mensajeerror.encode()
    packet += b'0'
    return packet


def main():
  server = Server(12000, 512, 1000)
  server.setupHandler()

if __name__ == "__main__":
  main()