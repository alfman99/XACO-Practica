# Example TCP socket client that connects to a server that upper cases text
from socket import *

# Default to running on localhost, port 12000
serverName = 'localhost'
serverPort = 12000
CHUNK_SIZE = 2048

# Request IPv4 and TCP communication
clientSocket = socket(AF_INET, SOCK_DGRAM)

# Read in some text from the user
command = ""

while command.upper() != "GET" and command.upper() != "PUT":
    command = input('Command: ')

fileName = input("Filename: ")

sendPack = command + " " + fileName

clientSocket.sendto(sendPack.encode(), (serverName,serverPort))

if command.upper() == "GET":
    # queremos recibir un archivo del servidor
    data, _ = clientSocket.recvfrom(CHUNK_SIZE)

    error = None

    try:
        error = data.decode()
    except:
        pass

    # If the file dosen't exist on the server
    if error == "ERROR_NO_FILE":
        print("404, The file doesn't exist")
    else:
        file = open(fileName + "2", "wb")
        dData = None
        print("DOWNLOADING BYTES: ")
        while data and dData != "END":
            print(data)
            file.write(data)
            data, _ = clientSocket.recvfrom(CHUNK_SIZE)
            try:
                dData = data.decode()
            except:
                pass
        file.close()

elif command.upper() == "PUT":
        # queremos mandar un archivo al servidor
        try:
            file = open(fileName, "rb")
            data = file.read(CHUNK_SIZE)
            print("UPLOADING BYTES: ")
            while data:
                print(data)
                clientSocket.sendto(data, (serverName,serverPort))
                data = file.read(CHUNK_SIZE)
            clientSocket.sendto("END", (serverName,serverPort))
            file.close()
        except Exception as e:
            print(str(e))
            print("404, The file doesn't exist")
            clientSocket.sendto("ABORT".encode(), (serverName,serverPort))
else:
    print("Error unknown method")
    # error no deberia pasar

clientSocket.close()