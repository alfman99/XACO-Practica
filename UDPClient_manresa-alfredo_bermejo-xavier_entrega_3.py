from socket import *
import os
import math
import random

class Client:

  def __init__(self, serverAddr, serverPort, blockSize, timeout):
    self.socket = socket(AF_INET, SOCK_DGRAM)
    self.serverAddr = serverAddr
    self.serverPort = serverPort
    self.defaultBlockSize = 512
    self.blockSize = blockSize
    self.timeout = timeout

  def GET(self, filename: str, modo: str):
    packet = self.createRRQ(filename, modo) + self.createOPTIONS(['blksize', str(self.blockSize)])
    print(packet)
    self.sendPacket(packet)

    print('OACK packet: ', self.recvPacket(4))

    file = open(filename + ".2", "wb")

    while True:
      data = self.recvPacket(4)
      packetType = data[:2]
      packetNum = int.from_bytes(data[2:4], 'big')
      packetData = data[4:]

      if packetType == b'03':
        print('Num seq:', packetNum)

        file.write(packetData)

        packet = self.createACK(packetNum)
        self.sendPacket(packet)

        if len(data) < (self.blockSize + 4):
          file.close()
          break

      elif packetType == b'05':
        print('error')
    
    print('Got file:', filename, 'from:', self.serverAddr, self.serverPort)

  def PUT(self, filename: str, modo: str):
    packet = self.createWRQ(filename, modo) + self.createOPTIONS(['blksize', str(self.blockSize)])
    self.sendPacket(packet)

    print('OACK packet: ', self.recvPacket(4))

    contadorPaquetesEnviados = 0
    contadorACK = 1

    packets = self.howManyPackets(filename)

    file = open(filename, 'rb')
    
    while contadorPaquetesEnviados < packets:

      data = file.read(self.blockSize)
      
      packet = self.createDATA(contadorACK, data)
      self.sendPacket(packet)

      serverACK = self.recvPacket(4)

      print('Num seq:', int.from_bytes(serverACK[2:4], 'big'))
      
      contadorACK = (contadorACK % pow(2, 16)) + 1
      contadorPaquetesEnviados += 1

    if self.extraEmpty(filename):
      packet = self.createDATA(contadorACK, b'')
      self.sendPacket(packet)
      serverACK = self.recvPacket(4)
      print('Num seq:', int.from_bytes(serverACK[2:4], 'big'))

  def extraEmpty(self, filename: str) -> bool:
    return (os.path.getsize(filename) % self.blockSize) == 0

  def howManyPackets(self, filename: str) -> int:
    return math.ceil(os.path.getsize(filename) / self.blockSize)

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

  def createOACK(self, blksize) -> bytearray:
    packet = b''
    packet += b'06'
    packet += str(blksize).encode()
    packet += b'\0'
    return packet

  def createOPTIONS(self, options: list) -> bytearray:
    packet = b''
    for i in range(0, len(options), 2):
      packet += options[i].encode()
      packet += b'\0'
      packet += options[i+1].encode()
      packet += b'\0'
    return packet

  def deserializeRQ(self, packet: bytearray):
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

  ipServer = "127.0.0.1" #input('ip server: ')
  portServer = 12000 #int(input('port server: '))

  
  try:
    command = "GET a.txt 32" #input('Command: ')
    params = command.split(' ')

    if len(params) != 3:
      print('Please use this format: <method> <filename> <blocksize>')
      print('Methods: GET, PUT')
      return
    
    method = params[0].upper()
    filename = params[1]
    blocksize = int(params[2])

    client = Client(ipServer, portServer, blocksize, 1000)

    if method == 'GET':
      client.GET(filename, 'netascii')
    elif method == 'PUT':
      client.PUT(filename, 'netascii')
    else:
      print('That method doesn\'t exist')
      

  except KeyboardInterrupt:
    print('Client closed')


if __name__ == "__main__":
  main()