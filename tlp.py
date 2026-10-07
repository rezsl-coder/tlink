import socket


class TypeData:
    message: str = '.message'


def get_socket() -> socket.socket:
    '''Create socket'''
    return socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )


def accept_bar(value: int, max: int) -> None:
    '''
    Creates a progress bar in the terminal based on the current value and the maximum value.
    '''
    k = int((value/max)*100)
    bar = '[' + ('∎'*(k//5)) + (' '*((100//5)-(k//5))) + ']'
    print('\r' + bar, str(k) + '%', f'{value}/{max}', end='')
    if max == value:
        print('\r' + bar, str(k) + '%', f'{value}/{max}', end='\n')


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


def file_segmentation(data: bytes, fullfilename: bytes, segment_size: int = 1024) -> None:
    '''...'''
    segments = []    

    header = len(fullfilename).to_bytes(1) + fullfilename   
    data = header + data
    data_size = len(data)

    subheader_size = 2 # 16 bit
    subdata_size = (segment_size - subheader_size)
    segments_number_max = (data_size // subdata_size) 

    for number_current, start_offset in enumerate(range(0, data_size, subdata_size)):
        end_offset = start_offset + subdata_size

        subdata = data[start_offset:end_offset]
        subheader = (segments_number_max - number_current).to_bytes(subheader_size) # segment invert number
 
        segment: bytes = subheader + subdata
        segments.append(segment)

    return segments 


def send_data(sock: socket.socket, address: tuple, data: bytes, fullfilename: str ) -> None:
    '''
    Sends data to the recipient in the form of many segments (pieces of data)
    '''
    segments: list = file_segmentation(data, fullfilename.encode('utf-8'), segment_size=1024*32)
    unsuccessful_attempts = 0

    for sequence_number, segment in enumerate(segments):
        status, failed = send_segment(sock, address, segment)
        unsuccessful_attempts += failed
        if status:
            accept_bar(sequence_number + 1, len(segments))
        else:
            raise socket.timeout('Сервер не доступен, сделанно попыток:', unsuccessful_attempts)

    print('SEND:', len(data), 'FAILED:', unsuccessful_attempts)


def accept_data(sock: socket.socket) -> tuple[bytes, str]:
    '''
    It receives data in the form of segments (data fragments) and assembles them into a single whole,
    while sending an acknowledgment of receipt to the sender for each segment.
    '''
    buffer: bytes = b''
    segment_old: bytes = b''

    segment_start, sender = sock.recvfrom(1024*32)
    sock.sendto(segment_start[:2], sender)

    header_offset_end = int.from_bytes(segment_start[2:3]) + 3
    fullfilename = (segment_start[3:header_offset_end]).decode('utf-8')

    buffer += segment_start[header_offset_end:]
    segment_old = segment_start

    sock.settimeout(10)
    while int.from_bytes(segment_old[:2]) != 0:
        try:
            segment_current, sender_current = sock.recvfrom(1024*32)
        finally:
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

    return buffer, fullfilename

