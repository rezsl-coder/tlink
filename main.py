import socket, sys, json, time, base64

"""
request info
1. id: 0 - 100 (message), 101 - 255 (file)
2. count: 0 - 255
3. data: 65535
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


def data_segmentation(bdata: bytes, size_segment: int = 1024) -> list[bytes]:
    '''
    LOGIC: Breaks data bytes into segments (pieces of data)
    OUT: Segment list
    '''
    segments = []
    segment_size_header = 2
    segment_size_data = size_segment - segment_size_header

    for index in range(0, (len(bdata)//segment_size_data)+1):
        header = index.to_bytes(segment_size_header)
        data = bdata[segment_size_data*index:(segment_size_data*index)+segment_size_data]
        segment = header + data
        segments.append(segment)

    return segments


def send_data(sock: socket.socket, address: tuple, data) -> None:
    '''
    LOGIC: Sends data to the recipient in the form of many segments (pieces of data)
    '''
    segments: list = data_segmentation(data, 1024*32)
    sock.settimeout(2)

    index: int = 0
    request_failed = 0
    while index < len(segments):
        segment = segments[index]
        request = send_segment(sock, address, segment)

        try:
            response = sock.recv(2)
        except socket.timeout:
            request_failed += 1
        else:
            index += 1
            print(f'segment-{int.from_bytes(segment[:2])}:', request_failed, 'failed')


def accept_data(sock: socket.socket) -> str:
    '''
    LOGIC: Receives data in the form of segments (pieces of data) and collects them into a single
    OUT: Data
    '''
    buffer: bytes = b''
    sock.settimeout(10)
    segment_number_old = None
    while True:
        try:
            segment, sender = sock.recvfrom(1024*32)
        except socket.timeout:
            print('timeout')
            break
        else:
            segment_number = segment[:2]
            if segment_number != segment_number_old:
                buffer = buffer + segment[2:]
                print(f'segment-{int.from_bytes(segment_number)}:', sender)
            segment_number_old = segment_number
            sock.sendto(segment_number, sender)

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
        send_data(sock, address, data.encode('utf-8'))


def server(address: tuple) -> None:
    with get_socket() as server:
        server.bind(address)
        print('start server')
        while True:
            data = accept_data(server)
            if data:
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

    if False:
        print(f'Status: [ {response} ]')


if __name__ == '__main__':
    main(sys.argv[1:])
