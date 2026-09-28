import socket, sys, json

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


def accept_bar(value: int, max: int) -> None:
    '''
    int((value/max)*100)
    '''
    value += 1
    k = int((value/max)*100)
    print('\r' + '[' + ('▮'*(k//5)) + ('*'*((100//5)-(k//5))) + '] ', k, end=f'% {value}:{max}', sep='')
    if max == value:
        print()


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
    segment_count = (len(bdata)//segment_size_data) + 1

    for index in range(0, segment_count):
        header = (segment_count - index).to_bytes(segment_size_header)
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
            accept_bar(index, len(segments))
            index += 1
    print('SEND:', len(data), 'FAILED:', request_failed)


def accept_data(sock: socket.socket) -> str:
    '''
    LOGIC: Receives data in the form of segments (pieces of data) and collects them into a single
    OUT: Data
    '''
    buffer: bytes = b''
    segment_count_max = None
    segment_number_old = None
    while True:
        try:
            segment, sender = sock.recvfrom(1024*32)
        finally:
            segment_number: int = int.from_bytes(segment[:2])
            if segment_number != segment_number_old:
                buffer = buffer + segment[2:]
                segment_number_old = segment_number
            if segment_count_max == None:
                segment_count_max = segment_number
            accept_bar(
                (segment_count_max - segment_number),
                segment_count_max
            )
            sock.sendto(segment[:2], sender)
            if segment_number == 1:
                break
    print('ACCEPT:', len(buffer))

    return buffer


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
        data = file.read()
    with get_socket() as sock:
        send_data(sock, address, data)


def server(address: tuple) -> None:
    with get_socket() as server:
        server.bind(address)
        print('START SERVER:' f'{address[0]}:{address[1]}')
        data = accept_data(server)

    with open('y.png', '+wb') as file:
        file.write(data)


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
