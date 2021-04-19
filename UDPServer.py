# TCP server program that upper cases text sent from the client
from socket import *

# Default port number server will listen on
serverPort = 12000
CHUNK_SIZE = 2048

# Request IPv4 and TCP communication
serverSocket = socket(AF_INET, SOCK_DGRAM)

# The welcoming port that clients first use to connect
serverSocket.bind(('', serverPort))

print ('El Servidor esta listo para recibir')
while True:
	clientMSG, clientAddr = serverSocket.recvfrom(128) # tamaño arbitrariamente grande
	clientMSG = clientMSG.decode().split(" ")

	method = clientMSG[0]
	filename = clientMSG[1]
	CHUNK_SIZE = int(clientMSG[2])

	if method.upper() == "GET":
		# queremos mandar el archivo al cliente
		try:
			file = open(filename, "rb")
			data = file.read(CHUNK_SIZE)
			print("UPLOADING BYTES: ")
			while data:
				print(data)
				serverSocket.sendto(data, clientAddr)
				data = file.read(CHUNK_SIZE)
			file.close()
			serverSocket.sendto("END".encode(), clientAddr)
		except:
			serverSocket.sendto("ERROR_NO_FILE".encode(), clientAddr)

	elif method.upper() == "PUT":
		# queremos recibir el archivo que nos manda el cliente
			data, clientAddr = serverSocket.recvfrom(CHUNK_SIZE)
			dData = None
			try:
				dData = data.decode()
			except:
				pass
			if dData != "ABORT":
				file = open(filename, "wb")
				dData = None
				print("DOWNLOADING BYTES: ")
				while data and dData != "END":
					print(data)
					file.write(data)
					data, clientAddr = serverSocket.recvfrom(CHUNK_SIZE)
					try:
						dData = data.decode()
					except:
						pass
				file.close()
	else:
		serverSocket.sendto("Error, invalid method".encode(), clientAddr)
		# error no deberia pasar
