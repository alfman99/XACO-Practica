
# Example TCP socket client that connects to a server that upper cases text
from socket import *

# Default to running on localhost, port 12000
serverName = '192.168.60.254'
serverPort = 12000

# Request IPv4 and TCP communication
clientSocket = socket(AF_INET, SOCK_DGRAM)

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



if method.upper() == "GET":

    clientSocket.sendto(createRRQ(filename, 'netascii').encode(), (serverName, serverPort))

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
        file = open(filename, "wb")
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

elif method.upper() == "PUT":
        # queremos mandar un archivo al servidor
        try:
            file = open(filename, "rb")
            data = file.read(CHUNK_SIZE)
            print("UPLOADING BYTES: ")
            while data:
                print(data)
                clientSocket.sendto(data, (serverName,serverPort))
                data = file.read(CHUNK_SIZE)
            clientSocket.sendto("END".encode(), (serverName,serverPort))
            file.close()
        except Exception as e:
            print("404, The file doesn't exist")
            clientSocket.sendto("ABORT".encode(), (serverName,serverPort))
else:
    print("Error unknown method")
    # error no deberia pasar

clientSocket.close()




def createRRQ(nombrefichero, modo):
    packet = ''
    packet += '01'
    packet += nombrefichero
    packet += '0'
    packet += modo
    packet += '0'
    return packet

def createWRQ(nombrefichero, modo):
    packet = ''
    packet += '02'
    packet += nombrefichero
    packet += '0'
    packet += modo
    packet += '0'
    return packet

def createDATA(numbloque, data):
    packet = ''
    packet += '03'
    packet += numbloque
    packet += data
    return packet
    
def createACK(numbloque):
    packet = ''
    packet += '04'
    packet += numbloque
    return packet