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


def segmentation_file_data(data: bytes, fullfilename: str, segment_size: int = 1024) -> list[bytes]:
    '''...'''
    segments = []
    fullfilename = fullfilename.encode('utf-8')

    header: bytes = len(fullfilename).to_bytes(1) + fullfilename   
    data: bytes = header + data

    data_size: int = len(data)
    subheader_size: int = 2 # 16 bit
    subdata_size: int = (segment_size - subheader_size)
    segments_number_max: int = (data_size // subdata_size) 

    for sequence_number, start_offset in enumerate(range(0, data_size, subdata_size)):
        end_offset: int = start_offset + subdata_size

        subdata: bytes = data[start_offset:end_offset]
        subheader: bytes = (segments_number_max - sequence_number).to_bytes(subheader_size, byteorder='big') # segment invert number
 
        segment: bytes = subheader + subdata
        segments.append(segment)

    return segments 


def send_file_data(data: bytes, fullfilename: str, sock: socket.socket, address: tuple) -> int:
    '''...'''
    segments: list[bytes] = segmentation_file_data(data, fullfilename, segment_size=1024*32)

    sock.settimeout(1)
    sequence_number = 0
    failed = 0
    
    while sequence_number < len(segments) and failed < 10:
        segment = segments[sequence_number]
        sock.sendto(segment, address)
        try:
            response = sock.recv(2)
        except socket.timeout:
            failed += 1
        else:
            sequence_number += 1
            accept_bar(sequence_number, len(segments))

    return sequence_number  


def accept_file_transfer(sock: socket.socket) -> tuple[bytes, int, str, tuple[str, int]]: 
    '''...'''
    segment_main, sender = sock.recvfrom(1024*32)

    header_number: int = int.from_bytes(segment_main[:2], byteorder='big')
    header_fullfilename_size: int = int.from_bytes(segment_main[2:3])
    header_fullfilename: str = segment_main[3:header_fullfilename_size + 3].decode('utf-8')
    subdata: bytes = segment_main[header_fullfilename_size + 3:]

    sock.sendto(header_number.to_bytes(2), sender)

    return subdata, header_number, header_fullfilename, sender


def accept_file_data(sock: socket.socket) -> tuple[bytes, str]:
    '''...'''
    buffer, segment_number_max, fullfilename, sender = accept_file_transfer(sock)
    segment_number_old = segment_number_max
    sock.settimeout(10)

    while segment_number_old != 0:
        try:
            segment: bytes = sock.recv(1024*32)
            segment_number = int.from_bytes(segment[:2], byteorder='big')
        except socket.timeout:
            buffer = None
        else:
            sock.sendto(segment_number.to_bytes(byteorder='big'), sender)
            if segment_number != segment_number_old:
                buffer += segment[2:]
                segment_number_old = segment_number
                accept_bar(
                    (segment_number_max - segment_number),
                    segment_number_max
                )

    return buffer, fullfilename


def accept_data(sock: socket.socket) -> tuple[bytes, str]:
    '''
    It receives data in the form of segments (data fragments) and assembles them into a single whole,
    while sending an acknowledgment of receipt to the sender for each segment.
    '''
    buffer: bytes = b''
    segment_old: bytes = b''

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

