from socket import *
import os
import math

triggerTimeout = False
discPle = True

class Server:

  def __init__(self, serverPort, blockSize, timeout):
    self.socket = socket(AF_INET, SOCK_DGRAM)
    self.serverPort = serverPort
    self.defaultBlockSize = 512
    self.blockSize = self.defaultBlockSize
    self.timeout = timeout
    self.clientAddr = None
    self.socket.bind(('', self.serverPort))

  # Encargado de activar el bucle de recepcion de paquetes del cliente
  def setupHandler(self) -> None:
    while True:
      
      data = self.recvPacket(4)

      print(data)
      
      packetData = self.deserializeRQ(data)
      packetType = packetData[0]
      filename = packetData[1]
      mode = packetData[2]
      if len(packetData) == 5:
        self.blockSize = int(packetData[4])
        self.sendPacket(self.createOACK(self.blockSize))

      if packetType == '01':
        print('GET')
        self.handleGET(filename)
      elif packetType == '02':
        print('PUT')
        self.handlePUT(filename)

      self.blockSize = self.defaultBlockSize
  
  def handleGET(self, filename: str) -> None:
    contadorPaquetesEnviados = 0
    contadorACK = 1

    if __debug__:
      filename = filename + ".server"
    
    file = None
    try:
      file = open(filename, "rb")
    except FileNotFoundError:
      print('Error, File does not exist')
      self.sendPacket(self.createERROR('01', 'File does not exist'))
      return

    packets = self.howManyPackets(filename)

    while contadorPaquetesEnviados < packets:

      data = file.read(self.blockSize)

      packet = self.createDATA(contadorACK, data)
      self.sendPacket(packet)

      if triggerTimeout:
        self.recvPacket(4)
      
      clientACK = self.recvPacket(4)
      print('Num seq:', int.from_bytes(clientACK[2:4], 'big'))
      
      contadorACK = (contadorACK % pow(2, 16)) + 1
      contadorPaquetesEnviados += 1

    file.close()

    if self.extraEmpty(filename):
      packet = self.createDATA(contadorACK, b'')
      self.sendPacket(packet)
      clientACK = self.recvPacket(4)
      print('Num seq:', int.from_bytes(clientACK[2:4], 'big'))
    
    print('Ended sending file:', filename, 'to client:', self.clientAddr)

  def handlePUT(self, filename: str) -> None:

    if __debug__:
      filename = filename + ".server"

    file = open(filename + ".2", 'wb')

    while True:

      if triggerTimeout:
        self.recvPacket(4)

      data = self.recvPacket(4)

      print(data)

      if discPle:
        self.sendPacket(self.createERROR('03', 'Disk full'))
        return

      packetNum = int.from_bytes(data[2:4], 'big')
      packetData = data[4:]

      print ('Num seq: ', packetNum)

      file.write(packetData)

      packet = self.createACK(packetNum)
      self.sendPacket(packet)

      if len(data) < (self.blockSize + 4):
        file.close()
        break      

    print('Ended reciving file:', filename, 'from client:', self.clientAddr)  

  def extraEmpty(self, filename: str) -> bool:
    return (os.path.getsize(filename) % self.blockSize) == 0

  def howManyPackets(self, filename: str) -> int:
    return math.ceil(os.path.getsize(filename) / self.blockSize)

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

  def createOACK(self, blksize: int) -> bytearray:
    packet = b''
    packet += b'06'
    packet += str(blksize).encode()
    packet += b'\0'
    return packet

  def deserializeRQ(self, packet: bytearray) -> list[bytearray]:
    packet = packet.decode('utf-8')
    value = [packet[:2]]

    last = 2
    contador = 1
    for i in range(2, len(packet)):
      if packet[i] == '\0':
        if contador == 1:
          value.append(packet[last:i])
        else:
          value.append(packet[last+1:i])
        contador += 1
        last = i

    return value


def main():
  server = Server(12000, 512, 1000)
  server.setupHandler()

if __name__ == "__main__":
  main()