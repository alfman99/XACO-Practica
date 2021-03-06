#!/usr/bin/env python
# -*- coding: utf-8 -*-

####
####  Importante este cliente NO funciona con nuestro Servidor, solamente funciona con servidores comerciales tal como:
####    - Tftpd64
####

from socket import *
import os
import math

localMode = False

class Client:

  def __init__(self, serverAddr, serverPort, blockSize, timeout, maxRetries):
    self.socket = socket(AF_INET, SOCK_DGRAM)
    self.serverAddr = serverAddr
    self.serverPort = serverPort
    self.defaultBlockSize = 512
    self.blockSize = blockSize
    self.timeout = timeout
    self.lastPacket = None
    self.retryNumber = 0
    self.maxRetries = maxRetries


  def GET(self, filename: str, modo: str) -> None:
    """
    Descripción:
      Procesar la función GET, descargando trozo por trozo del servidor el archivo pedido  

    Parametros:
      filename (str): nombre del archivo que queremos descargar del servidor
      modo (str): Modo de la descarga del archivo (netascii / octet), solamente está implementada la opción de octet
    """

    packet = self.createRRQ(filename, modo) + self.createOPTIONS(['blksize', str(self.blockSize)])
    self.sendPacket(packet)

    data = self.recvPacket(4)
    packetType = int.from_bytes(data[:2], 'big')

    if packetType == 6:
      print('OACK packet: ', data)
    elif packetType == 5:
      errorType = int.from_bytes(data[2:4], 'big') 
      errorMessage = data[4:]
      print('Server Error')
      print('Error Code:', str(errorType), 'Message:', errorMessage.decode('utf-8'))
      return

    if localMode:
      filename = filename + ".client"

    self.sendPacket(self.createACK(0))

    file = open(filename, "wb")

    while True:
      data = self.recvPacket(4)
      packetType = int.from_bytes(data[:2], 'big')
      packetNum = int.from_bytes(data[2:4], 'big')
      packetData = data[4:]

      if packetType == 3:
        print('Num seq:', packetNum)

        file.write(packetData)

        if len(data) < (self.blockSize + 4):
          file.close()
          break

        packet = self.createACK(packetNum)
        self.sendPacket(packet)

      elif packetType == 5:
        errorType = int.from_bytes(data[2:4], 'big') 
        errorMessage = data[4:]
        print('Server Error')
        print('Error Code:', str(errorType), 'Message:', errorMessage.decode('utf-8'))
        return
    
    print('Got file:', filename, 'from:', self.serverAddr, self.serverPort)

  def PUT(self, filename: str, modo: str) -> None:
    """
    Descripción:
      Procesa la función POST, subir trozo por trozo al servidor el archivo  

    Parametros:
      filename (str): nombre del archivo que queremos subir del servidor
      modo (str): Modo de la subida del archivo (netascii / octet), solamente está implementada la opción de octet
    """

    packet = self.createWRQ(filename, modo) + self.createOPTIONS(['blksize', str(self.blockSize)])
    self.sendPacket(packet)

    data = self.recvPacket(4)

    packetType = int.from_bytes(data[:2], 'big')

    if packetType == 6:
      print('OACK packet: ', data)
    elif packetType == 5:
      errorType = int.from_bytes(data[2:4], 'big') 
      errorMessage = data[4:]
      print('Server Error')
      print('Error Code:', str(errorType), 'Message:', errorMessage.decode('utf-8'))
      return

    contadorPaquetesEnviados = 0
    contadorACK = 1

    packets = self.howManyPackets(filename)

    file = open(filename, 'rb')
    
    while contadorPaquetesEnviados < packets:

      data = file.read(self.blockSize)
      
      packet = self.createDATA(contadorACK, data)
      self.sendPacket(packet)

      data = self.recvPacket(4)

      packetType = data[:2]

      if packetType == b'05':
        errorType = int.from_bytes(data[2:4], 'big') 
        errorMessage = data[4:]
        print('Server Error')
        print('Error Code:', str(errorType), 'Message:', errorMessage.decode('utf-8'))
        return

      print('Num seq:', int.from_bytes(data[2:4], 'big'))
      
      contadorACK = (contadorACK % pow(2, 16)) + 1
      contadorPaquetesEnviados += 1

    if self.extraEmpty(filename):
      packet = self.createDATA(contadorACK, b'')
      self.sendPacket(packet)
      data = self.recvPacket(4)
      print('Num seq:', int.from_bytes(data[2:4], 'big'))

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
      Guarda el ultimo paquete enviado en una variable y lo manda al servidor  

    Parametros:
      packet (bytearray): bytes del paquete que se quiere enviar
    """
    
    self.lastPacket = packet
    self.socket.sendto(packet, (self.serverAddr, self.serverPort))

  def recvPacket(self, headerSize: int) -> bytes:
    """
    Descripción:
      Recibe un paquete desde el servidor, también se encarga de administrar el timeout, porque lo que si el
      timeout se excede en el tiempo definido, reenviará el ultimo paquete enviado previamente.

    Parametros:
      headerSize (int): tamaño extra de la cabecera

    Return:
      Datos recividos del servidor
    """
    
    self.socket.settimeout(self.timeout)
    try:
      data, (_, self.serverPort) = self.socket.recvfrom(self.blockSize + headerSize)
      self.retryNumber = 0
      return data
    except timeout:
      print('Timeout exceeded, resending packet...')
      self.retryNumber += 1
      if self.retryNumber <= self.maxRetries:
        self.sendPacket(self.lastPacket)
        return self.recvPacket(4)
      else:
        print('Max retries reached exiting client.')
        exit(0)

  def createRRQ(self, nombrefichero: str, modo: str) -> bytearray:
    """
    Descripción:
      Forja el paquete RRQ con los parametros dados

    Parametros:
      nombrefichero (str): nombre del fichero que queremos leer
      modo (str): Modo de la subida del archivo (netascii / octet), solamente está implementada la opción de octet

    Return:
      Paquete GET en forma de array de bytes
    """

    packet = b''
    packet += int(1).to_bytes(2, 'big')
    packet += nombrefichero.encode()
    packet += b'\0'
    packet += modo.encode()
    packet += b'\0'
    return packet

  def createWRQ(self, nombrefichero: str, modo: str) -> bytearray:
    """
    Descripción:
      Forja el paquete WRQ con los parametros dados

    Parametros:
      nombrefichero (str): nombre del fichero que queremos escribir
      modo (str): Modo de la subida del archivo (netascii / octet), solamente está implementada la opción de octet

    Return:
      Paquete PUT en forma de array de bytes
    """

    packet = b''
    packet += int(2).to_bytes(2, 'big')
    packet += nombrefichero.encode()
    packet += b'\0'
    packet += modo.encode()
    packet += b'\0'
    return packet

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

  def createOPTIONS(self, options: list) -> bytearray:
    """
    Descripción:
      Forja el paquete OPTIONS con los parametros dados

    Parametros:
      options (list): array con pares de opciones, ejemplo: (['blksize', 512])

    Return:
      Paquete de OPTIONS en forma de array de bytes
    """

    packet = b''
    for i in range(0, len(options), 2):
      packet += options[i].encode()
      packet += b'\0'
      packet += options[i+1].encode()
      packet += b'\0'
    return packet


def main():

  ipServer = input('ip server: ')
  portServer = int(input('port server: '))

  try:
    command = input('Command (<method> <filename> <blocksize> <timeout> <retryTimes>): ') #"PUT a.txt 32" 
    params = command.split(' ')

    if len(params) != 5:
      print('Please use this format: <method> <filename> <blocksize> <timeout> <retryTimes>')
      return

    method = params[0].upper()
    filename = params[1]
    blocksize = int(params[2])
    timeout = int(params[3])
    retryTimes = int(params[4])
    
    if blocksize != 32 and blocksize != 64 and blocksize != 128 and blocksize != 256 and blocksize != 512 and blocksize != 1024 and blocksize != 2048 and blocksize != 4096 and blocksize != 8192:
      print('<blocksize> tiene que ser potencia de 2 (32 - 8192)')
      return

    if timeout < 1:
      print('<timeout> tiene que ser mayor o igual a 1')
      return

    if retryTimes < 1:
      print('<retryTimes> tiene que ser mayor o igual a 1')
      return
    

    client = Client(ipServer, portServer, blocksize, timeout, retryTimes)

    if method == 'GET':
      client.GET(filename, 'octet')
    elif method == 'PUT':
      client.PUT(filename, 'octet')
    else:
      print('That method doesn\'t exist')

    input("Enter para cerrar...")
      

  except KeyboardInterrupt:
    print('Client closed')

if __name__ == "__main__":
  main()
