#!/usr/bin/env python
# -*- coding: utf-8 -*-

from socket import *
import os
import math

localMode = True
triggerTimeout = False
discPle = False

class Server:

  def __init__(self, serverPort, blockSize, timeout):
    self.socket = socket(AF_INET, SOCK_DGRAM)
    self.serverPort = serverPort
    self.defaultBlockSize = 512
    self.blockSize = self.defaultBlockSize
    self.timeout = timeout
    self.clientAddr = None
    self.socket.bind(('', self.serverPort))

  def setupHandler(self) -> None:
    """
    Descripción:
      Encargado de activar el bucle de recepcion de paquetes del cliente
    """
    
    print ('Servidor listo esperando conexion del cliente...')
    
    while True:
      
      data = self.recvPacket(4)

      print('REQUEST packet sent from client', data)
      
      packetData = self.deserializeRQ(data)
      packetType = packetData[0]
      filename = packetData[1]
      mode = packetData[2]

      print(packetData)
      
      if len(packetData) > 4:
        self.blockSize = int(packetData[4])
        self.sendPacket(self.createOACK(self.blockSize))

      if packetType == 1:
        print('GET')
        self.handleGET(filename)
      elif packetType == 2:
        print('PUT')
        self.handlePUT(filename)

      self.blockSize = self.defaultBlockSize
  
  def handleGET(self, filename: str) -> None:
    """
    Descripción:
      Encargado de hacer el proceso de enviar un archivo al cliente trozo por trozo
    """
    """data = self.recvPacket(4)
    packetType = int.from_bytes(data[:2], 'big')

    if packetType == 6:
      print('OACK packet: ', data)
    elif packetType == 5:
      errorType = int.from_bytes(data[2:4], 'big') 
      errorMessage = data[4:]
      print('Server Error')
      print('Error Code:', str(errorType), 'Message:', errorMessage.decode('utf-8'))
      return
      """

    contadorPaquetesEnviados = 0
    contadorACK = 1
    
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
    """
    Descripción:
      Encargado de hacer el proceso de recibir un archivo del cliente trozo por trozo
    """

    if localMode:
      filename = filename + ".server"

    file = open(filename, 'wb')

    while True:

      if triggerTimeout:
        self.recvPacket(4)

      data = self.recvPacket(4)

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
    """
    Descripción:
      Indicar si hay que mandar un archivo vacio para la finalización explicita de la subida  

    Parametros:
      filename (str): nombre del archivo que queremos comprobar si es multiplo del tamaño del paquete

    Return:
      Si hay que terminar de manera explicita o no
    """
    
    return (os.path.getsize(filename) % self.blockSize) == 0

  def howManyPackets(self, filename: str) -> int:
    """
    Descripción:
      Indica cuantos paquetes harán falta para enviar el archivo al servidor 

    Parametros:
      filename (str): nombre del archivo que queremos ver en cuantos paquetes se debe mandar
    
    Return:
      Numero de paquetes maximo en el que se puede dividir el archivo
    """

    return math.ceil(os.path.getsize(filename) / self.blockSize)

  def sendPacket(self, packet: bytearray) -> None:
    """
    Descripción:
      Manda el paquete al cliente

    Parametros:
      packet (bytearray): bytes del paquete que se quiere enviar
    """

    self.socket.sendto(packet, self.clientAddr)

  def recvPacket(self, headerSize: int) -> bytes:
    """
    Descripción:
      Recibe un paquete del cliente

    Parametros:
      headerSize (int): tamaño extra de la cabecera

    Return:
      Datos recibidos del cliente
    """
    
    data, clientAddr = self.socket.recvfrom(self.blockSize + headerSize)
    self.clientAddr = clientAddr
    return data

  def createDATA(self, numbloque: int, data: bytearray) -> bytearray:
    """
    Descripción:
      Forja el paquete DATA con los parametros dados

    Parametros:
      numbloque (int): numero de bloque
      data (bytearray): array de bytes que queremos mandar

    Return:
      Paquete de datos en forma de array de bytes
    """

    packet = b''
    packet += int(3).to_bytes(2, 'big')
    packet += numbloque.to_bytes(2, 'big')
    packet += data
    return packet

  def createACK(self, numbloque: int) -> bytearray:
    """
    Descripción:
      Forja el paquete ACK con los parametros dados

    Parametros:
      numbloque (int): numero de bloque

    Return:
      Paquete de ACK en forma de array de bytes
    """

    packet = b''
    packet += int(4).to_bytes(2, 'big')
    packet += numbloque.to_bytes(2, 'big')
    return packet

  def createERROR(self, codigoerror: str, mensajeerror: str) -> bytearray:
    """
    Descripción:
      Forja el paquete ACK con los parametros dados

    Parametros:
      numbloque (int): numero de bloque
      mensajeerror (str): mensaje de error

    Return:
      Paquete de ERROR en forma de array de bytes
    """

    packet = b''
    packet += int(5).to_bytes(2, 'big')
    packet += codigoerror.encode()
    packet += mensajeerror.encode()
    packet += b'\0'
    return packet

  def createOACK(self, blksize: int) -> bytearray:
    """
    Descripción:
      Forja el paquete OACK con los parametros dados

    Parametros:
      blksize (int): negociacion del tamaño del bloque

    Return:
      Paquete de OACK en forma de array de bytes
    """

    packet = b''
    packet += int(6).to_bytes(2, 'big')
    packet += str(blksize).encode()
    packet += b'\0'
    return packet

  def deserializeRQ(self, packet: bytearray):
    """
    Descripción:
      Coge el paquete RQ y lo transforma en un lista con todos los datos del RQ (request), sirve tanto para WRQ como RRQ

    Parametros:
      packet (bytearray): paquete tanto WRQ como RRQ que queremos transformar en una lista

    Return:
      Lista con todos los datos de la request por campos para mas facil acceso
    """

    value = [int.from_bytes(packet[:2], 'big')]

    packet = packet.decode('utf-8')
    
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
  port = int(input('Port to listen to: '))
  server = Server(port, 512, 1000)
  server.setupHandler()

if __name__ == "__main__":
  main()