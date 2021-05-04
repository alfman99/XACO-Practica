from socket import *
import os

class Client:

  def __init__(self, serverAddr, serverPort, blockSize, timeout):
    self.socket = socket(AF_INET, SOCK_DGRAM)
    self.serverAddr = serverAddr
    self.serverPort = serverPort
    self.blockSize = blockSize
    self.timeout = timeout

  def GET(self, filename: str, modo: str):
    packet = self.createRRQ(filename, modo)
    self.sendPacket(packet)
    data = self.recvPacket(4)
    packetType = data[:2]
    file = None
    if packetType == b'03':
      file = open(filename, "wb")
    elif packetType == b'05':
      print('error')
      return

    while data:
      packetType = data[:2]
      packetNum = int.from_bytes(data[2:4], 'big')
      packetData = data[4:]
      print('Num seq:', packetNum)
      if packetType == b'03':
        # handle DATA packet
        packet = self.createACK(packetNum + 1)
        self.sendPacket(packet)
        file.write(packetData)
        if len(data) < (self.blockSize + 4):
          file.close()
          break
        else:
          data = self.recvPacket(4)

      elif packetType == b'05':
        # handle ERR packet
        print('err')
    
    print('Got file:', filename, 'from:', self.serverAddr, self.serverPort)

  def PUT(self, filename: str, modo: str):
    packet = self.createWRQ(filename, modo)
    self.sendPacket(packet)

    serverACK = self.recvPacket(4)
    packetType = serverACK[:2]

    file = open(filename, 'rb')
    data = file.read(self.blockSize)

    contador = 1

    while data:
      
      packet = self.createDATA(contador, data)
      self.sendPacket(packet)

      serverACK = self.recvPacket(4)

      print('Num seq:', contador)
      contador = (contador % pow(2, 16)) + 1

      data = file.read(self.blockSize)

      if data == b'' and self.extraEmpty(filename):
        packet = self.createDATA(contador, b'')
        self.sendPacket(packet)

  def extraEmpty(self, filename: str) -> bool:
    return (os.path.getsize(filename) % self.blockSize) == 0

  def sendPacket(self, packet: bytearray) -> None:
    self.socket.sendto(packet, (self.serverAddr, self.serverPort))

  def recvPacket(self, headerSize: int) -> bytes:
    data, _ = self.socket.recvfrom(self.blockSize + headerSize)
    return data

  def createRRQ(self, nombrefichero: str, modo: str) -> bytearray:
    packet = b''
    packet += b'01'
    packet += nombrefichero.encode()
    packet += b'\0'
    packet += modo.encode()
    packet += b'\0'
    return packet

  def createWRQ(self, nombrefichero: str, modo: str) -> bytearray:
    packet = b''
    packet += b'02'
    packet += nombrefichero.encode()
    packet += b'\0'
    packet += modo.encode()
    packet += b'\0'
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
    packet += b'\0'
    return packet


def main():
  client = Client('localhost', 12000, 512, 1000)
  # client.GET('a.txt', 'netascii')
  client.PUT('a.txt', 'netascii')

if __name__ == "__main__":
  main()