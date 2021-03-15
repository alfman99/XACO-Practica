# Example TCP socket client that connects to a server that upper cases text
from socket import *

# Default to running on localhost, port 12000
serverName = 'localhost'
serverPort = 12000
CHUNK_SIZE = 2048

# Request IPv4 and TCP communication
clientSocket = socket(AF_INET, SOCK_STREAM)

# Open the TCP connection to the server at the specified port 
clientSocket.connect((serverName,serverPort))

# Read in some text from the user
sendPack = input("Input (Example: GET hola.txt): ")

commands = sendPack.split(" ")

clientSocket.send(sendPack.encode())

if commands[0].upper() == "GET":
    # queremos recibir un archivo del servidor
    data = clientSocket.recv(CHUNK_SIZE)

    error = None

    try:
        error = data.decode()
    except:
        pass

    # If the file dosen't exist on the server
    if error == "ERROR_NO_FILE":
        print("404, The file doesn't exist")
    else:
        file = open(commands[1], "wb")
        print("DOWNLOADING BYTES: ")
        while data:
            print(data)
            file.write(data)
            data = clientSocket.recv(CHUNK_SIZE)
        file.close()

elif commands[0].upper() == "PUT":
        # queremos mandar un archivo al servidor
        try:
            file = open(commands[1], "rb")
            data = file.read(CHUNK_SIZE)
            print("UPLOADING BYTES: ")
            while data:
                print(data)
                clientSocket.send(data)
                data = file.read(CHUNK_SIZE)
            file.close()
        except:
            print("404, The file doesn't exist")
            clientSocket.send("ABORT".encode())
else:
    print("Error unknown method")
    # error no deberia pasar

clientSocket.close()