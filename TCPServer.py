# TCP server program that upper cases text sent from the client
from socket import *

# Default port number server will listen on
serverPort = 12000
CHUNK_SIZE = 2048

# Request IPv4 and TCP communication
serverSocket = socket(AF_INET, SOCK_STREAM)

# The welcoming port that clients first use to connect
serverSocket.bind(('', serverPort))

# Start listening on the welcoming port
serverSocket.listen(1)
print ('El Servidor esta listo para recibir')
while True:
	connectionSocket, addr = serverSocket.accept()

	clientMSG = connectionSocket.recv(CHUNK_SIZE).decode()
	clientMSG = clientMSG.split(" ")

	if clientMSG[0].upper() == "GET":
		# queremos mandar el archivo al cliente
		try:
			file = open(clientMSG[1], "rb")
			data = file.read(CHUNK_SIZE)
			print("UPLOADING BYTES: ")
			while data:
				print(data)
				connectionSocket.send(data)
				data = file.read(CHUNK_SIZE)
			file.close()
		except:
			connectionSocket.send("ERROR_NO_FILE".encode())

	elif clientMSG[0].upper() == "PUT":
		# queremos recibir el archivo que nos manda el cliente
			data = connectionSocket.recv(CHUNK_SIZE)

			error = None

			try:
				error = data.decode()
			except:
				pass

			if error != "ABORT":
				file = open(clientMSG[1], "wb")
				print("DOWNLOADING BYTES: ")
				while data:
					print(data)
					file.write(data)
					data = connectionSocket.recv(CHUNK_SIZE)
				file.close()
	else:
		connectionSocket.send("Error, invalid method".encode())
		# error no deberia pasar
	
	connectionSocket.close()
