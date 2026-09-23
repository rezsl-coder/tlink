import socket, sys, json, time, base64

"""
request info
1. id: 0 - 100 (message), 101 - 255 (file)
2. count: 0 - 255
3. data:
response info
1. id: request id
2. count: 0 - 255
"""


class SocketType:
    STATUS = 'status'
    MESSAGE = (0, 100)
    FILE = 'file'


def get_socket() -> socket.socket:
    '''LOGIC: Create socket'''
    return socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )


def send_segment(sock: socket.socket, address: tuple, segment) -> int:
    '''
    LOGIC: Sends one data segment to the recipient
    OUT: Number of bytes sent
    '''
    return sock.sendto(
        segment,
        address
    )


def data_segmentation(bdata, size_segment: int = 1024) -> list:
    '''
    LOGIC: Breaks data bytes into segments (pieces of data)
    OUT: Segment list
    '''
    segments = []
    size_data = len(bdata)

    for offset in range(size_segment, size_data+size_segment, size_segment):
        segment = bdata[offset - size_segment:offset]
        segments.append(segment)

    return segments


def send_data(sock: socket.socket, address: tuple, data) -> None:
    '''
    LOGIC: Sends data to the recipient in the form of many segments (pieces of data)
    '''
    segments: list = data_segmentation(data, 1024*32)
    print('send_data:', segments)

    for segment in segments:
        print('send_data', send_segment(sock, address, segment.encode('utf-8')))
        time.sleep(0.01)


def accept_data(sock: socket.socket) -> str:
    '''
    LOGIC: Receives data in the form of segments (pieces of data) and collects them into a single
    OUT: Data
    '''
    buffer: bytes = b''
    sock.settimeout(5)
    while True:
        try:
            segment = sock.recv(1024*32)
        except socket.timeout:
            print('timeout')
            break
        else:
            print('segment:', len(segment))
            buffer = buffer + segment

    return buffer.decode('utf-8')


def send_message(address: tuple, message: str) -> bool:
    status = False
    request = json.dumps(
        [{'type': SocketType.MESSAGE, 'data': message}]
    )
    with get_socket() as sock:
        request = sock.sendto(
            request.encode('utf-8'),
            address
        )

        response: dict = json.loads(sock.recv(1024).decode('utf-8'))[0]
        if response.get('type') == SocketType.STATUS:
            status = response.get('data')

        return status


def send_status(address: tuple, sock: socket.socket) -> None:
    request = json.dumps([{'type': SocketType.STATUS, 'data': True}])
    sock.sendto(request.encode('utf-8'), address)


def send_file(address: tuple, path: str):
    with open(path, '+rb') as file:
        data_file = file.read()
    print('send_file:', len(data_file))
    data = base64.b64encode(data_file).decode('ascii')
    with get_socket() as sock:
        send_data(sock, address, data)


def server(address: tuple) -> None:
    with get_socket() as server:
        server.bind(address)
        print('start server')
        while True:
            data = accept_data(server)
            print('data1:', data)
            if data:
                print('data:' + data)
                break

    with open('y.png', '+wb') as file:
        file.write(base64.b64decode(data))


def main(tcomand: list[str]):
    ip, port = tcomand[0].split(':')
    address = (ip, int(port))

    match tcomand[1:]:
        case ['-m', message]:
            response = send_message(address, message)
        case ['-f', path]:
            response = send_file(address, path)
        case ['-t', path]:
            with open(path, '+rb') as file:
                data = file.read()
                segments = data_segmentation(data)
                response = segments
        case _:
            response = server(address)

    if response:
        print(f'Status: [ {response} ]')


if __name__ == '__main__':
    main(sys.argv[1:])
