# Example TCP socket client that connects to a server that upper cases text
from socket import *

# Default to running on localhost, port 12000
serverName = '192.168.60.254'
serverPort = 12000

# Request IPv4 and TCP communication
clientSocket = socket(AF_INET, SOCK_STREAM)

# Open the TCP connection to the server at the specified port 
clientSocket.connect((serverName,serverPort))

condiciones = False
while not condiciones:
    # Read in some text from the user
    sendPack = input("Input (Example: GET hola.txt 32): ")

    commands = sendPack.split(" ")
    
    method = commands[0]
    filename = commands[1]
    CHUNK_SIZE = int(commands[2])

    if CHUNK_SIZE == 32 or CHUNK_SIZE == 64 or CHUNK_SIZE == 128 or CHUNK_SIZE == 256 or CHUNK_SIZE == 512 or CHUNK_SIZE == 1024 or CHUNK_SIZE == 2048:
        condiciones = True

clientSocket.send(sendPack.encode())

if method.upper() == "GET":
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
        file = open(filename + ".2", "wb")
        print("DOWNLOADING BYTES: ")
        while data:
            print("nueva iteracion")
            print(data)
            file.write(data)
            data = clientSocket.recv(CHUNK_SIZE)
        file.close()

elif method.upper() == "PUT":
        # queremos mandar un archivo al servidor
        try:
            file = open(filename, "rb")
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
