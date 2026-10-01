import socket, sys, json


def accept_bar(value: int, max: int) -> None:
    '''
    Creates a progress bar in the terminal based on the current value and the maximum value.
    '''
    k = int((value/max)*100)
    bar = '\r' + '[' + ('▮'*(k//5)) + ('*'*((100//5)-(k//5))) + ']'
    print(bar, str(k) + '%', f'{value}/{max}', end='')
    if max == value:
        print()


def get_socket() -> socket.socket:
    '''Create socket'''
    return socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

def documentation() -> bool:
    status = True
    try:
        with open('README.md', 'r') as file:
            print(file.read())
    except Exception:
        status = False

    return status


def send_segment(sock: socket.socket, address: tuple, segment: bytes) -> tuple[bool, int]:
    '''
    Guarantees delivery of the segment to the recipient
    if the recipient is available (by waiting for an acknowledgment).
    '''
    status = False
    failed = 0
    sock.settimeout(2)

    while failed < 10:
        sock.sendto(segment, address)
        try:
            response = sock.recv(2)
        except socket.timeout:
            failed += 1
        else:
            status = True
            break

    return status, failed


def data_segmentation(data: bytes, size_segment: int = 1024) -> list[bytes]:
    '''
    It segments the data (breaking it into smaller chunks) and adds a header to them.
    The header consists of a 16-bit field storing the segment's sequence number,
    where the first segment is numbered "x" and subsequent ones are x-1, x-2, x-3... down to zero,
    with "x" representing the "number of segments - 1".
    '''

    data_size = len(data)
    segment_size_header = 2 # size in bates (16-bit)
    segment_size_data = size_segment - segment_size_header

    segments = []
    segment_max_number = (data_size // segment_size_data)
    segment_current_number = 0

    while segment_current_number <= segment_max_number:
        data_offset_start = segment_current_number * segment_size_data
        data_offset_end = data_offset_start + segment_size_data

        segment_header = (segment_max_number - segment_current_number).to_bytes(segment_size_header)
        segment_data = data[data_offset_start:data_offset_end]

        segment = segment_header + segment_data
        segments.append(segment)

        segment_current_number += 1

    return segments


def send_data(sock: socket.socket, address: tuple, data: bytes) -> None:
    '''
    Sends data to the recipient in the form of many segments (pieces of data)
    '''
    segments: list = data_segmentation(data, 1024*32)
    unsuccessful_attempts = 0

    for sequence_number, segment in enumerate(segments):
        status, failed = send_segment(sock, address, segment)
        unsuccessful_attempts += failed
        if status:
            accept_bar(sequence_number + 1, len(segments))
        else:
            raise socket.timeout('Сервер не доступен, сделанно попыток:', unsuccessful_attempts)

    print('SEND:', len(data), 'FAILED:', unsuccessful_attempts)


def accept_data(sock: socket.socket) -> bytes:
    '''
    It receives data in the form of segments (data fragments) and assembles them into a single whole,
    while sending an acknowledgment of receipt to the sender for each segment.
    '''
    buffer: bytes = b''
    segment_old: bytes = b''

    segment_start, sender = sock.recvfrom(1024*32)
    sock.sendto(segment_start[:2], sender)

    buffer += segment_start[2:]
    segment_old = segment_start

    sock.settimeout(10)
    while int.from_bytes(segment_old[:2]) != 0:
        try:
            segment_current, sender_current = sock.recvfrom(1024*32)
        except socket.timeout as error:
            raise error(sender, ', не доступен!')
        else:
            segment_current_number: bytes = segment_current[:2]
            segment_old_number: bytes = segment_old[:2]

            if segment_current_number != segment_old_number:
                buffer += segment_current[2:]
                segment_old = segment_current
                segments_max = int.from_bytes(segment_start[:2]) + 1
                accept_bar(
                    (segments_max - int.from_bytes(segment_current_number)),
                    segments_max
                )
            sock.sendto(segment_current_number, sender_current)

    print('ACCEPT:', len(buffer))

    return buffer


def send_message(address: tuple, message: str) -> bool:
    '''Sends the passed message.'''
    ...


def send_file(address: tuple, path: str):
    '''Reads a file from the provided path and sends it.'''
    with open(path, '+rb') as file:
        data = file.read()
    with get_socket() as sock:
        send_data(sock, address, data)


def server(address: tuple) -> None:
    '''Starts the server.'''
    with get_socket() as server:
        server.bind(address)
        print('START SERVER:' f'{address[0]}:{address[1]}')
        data = accept_data(server)

    with open('y.png', '+wb') as file:
        file.write(data)


def main(tcommand: list[str]):
    if tcommand[0][0] == '-':
        tcommand = ['0.0.0.0:0'] + tcommand

    status = None
    ip, port = tuple(tcommand[0].split(':'))
    address = (ip, int(port))

    match tcommand[1:]:
        case ['-m', message]:
            status = send_message(address, message)
        case ['-f', path]:
            status = send_file(address, path)
        case ['-h']:
            status = documentation()
        case _:
            status = server(address)

    if status:
        print(f'Status: [ {status} ]')


if __name__ == '__main__':
    main(sys.argv[1:])
