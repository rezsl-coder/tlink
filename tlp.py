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


def add_interval(interval, current_number) -> list:            
    max_position = (len(interval) - 1)
    current_position = max_position

    while current_position > 0:
        big_offset, small_offset = current_position - 1, current_position    

        if (interval[small_offset] - 1) == current_number:
            interval[small_offset] = current_number
            break
        elif (interval[big_offset] + 1) == current_number:
            next_small_offset = big_offset - 1
            if (interval[next_small_offset] - current_number) == 1:
                interval[next_small_offset:small_offset] = []
                max_position -= 2
            else: interval[big_offset] = current_number
            break
        elif interval[big_offset] >= current_number >= interval[small_offset]:
            break
        elif interval[big_offset] > current_number:
            interval[small_offset + 1:small_offset + 1] = [current_number]*2
            max_position += 2
            break

        current_position -= 2
    else:
        if current_number > interval[0]: 
            interval[0:0] = [current_number]*2
            max_position += 2

    return interval


def remove_interval(interval, current_number) -> list:    
    max_position = (len(interval) - 1)
    current_position = max_position

    while current_position >= 0: 
        big_offset, small_offset = (
            current_position - 1,
            current_position
        )
        if current_number == interval[big_offset] \
        and current_number == interval[small_offset]:
            interval[big_offset:small_offset + 1] = []
            break
        elif current_number == interval[big_offset]:
            interval[big_offset] = current_number - 1
            break       
        elif current_number == interval[small_offset]:
            interval[small_offset] = \
            current_number + 1
            break

        elif interval[big_offset] > \
        current_number > interval[small_offset]:
            interval[small_offset:small_offset]= [
                current_number + 1,
                current_number - 1
            ]
            break
        current_position -= 2
    else: raise Exception('Not, number')
    return interval


def segmentation_file_data(
    data: bytes,
    data_size: int,
    segment_size: int,
    segment_number_size: int
    ) -> list[bytes]:
    '''...'''
    segments = []
    segments_number_max: int = (data_size // segment_size) 

    for sequence_number, start_offset in enumerate(range(0, data_size, segment_size)):
        end_offset: int = start_offset + segment_size

        subdata: bytes = data[start_offset:end_offset]
        subheader: bytes = (segments_number_max - sequence_number).to_bytes(segment_number_size, byteorder='big') # segment invert number
 
        segment: bytes = subheader + subdata
        segments.append(segment)

    return segments 


def send_file_data(data: bytes, fullfilename: str, sock: socket.socket, address: tuple) -> int:
    '''...'''

    header_offset_end_size: int = 1 # size argument 1 byte    
    segment_number_size: int = 2 # size argument 2 byte

    header_offset_end: bytes = (
        header_offset_end_size + segment_number_size + len(fullfilename)
    ).to_bytes(header_offset_end_size, byteorder='big')
    fullfilename: bytes = fullfilename.encode('utf-8') 
    data: bytes = header_offset_end + fullfilename + data

    data_size: int = len(data)
    segment_size = (1024*32) - segment_number_size
    segments_number_max: int = (data_size // segment_size) 
#    segments: list[bytes] = segmentation_file_data(data, data_size, segment_size, segment_number_size)

    sock.settimeout(1)
    sequence_number = 0
    failed = 0

    while sequence_number < segments_number_max:
        offset_start = sequence_number * segment_size
        offset_end = offset_start + segment_size

        segment_number: bytes = (segment_number_max - sequence_number).to_bytes(segment_number_size)
        segment_data: bytes = data[offset_start:offset_end]
        segment = segment_number + segment_data

        sock.sendto(segment, address)

        sequence_number += 1
    
        if sequence_number % 10 == 0 or sequence_number == 0:
            try: response = sock.recv(1024)
            except:

#    while sequence_number < len(segments) and failed < 10:
#        segment = segments[sequence_number]
#        sock.sendto(segment, address)
#        try:
#            response = sock.recv(2)
#        except socket.timeout:
#            failed += 1
#        else:
#            sequence_number += 1
#            accept_bar(sequence_number, len(segments))
#
#    return sequence_number  


def accept_file_transfer(sock: socket.socket) -> tuple[bytes, int, str, tuple[str, int]]: 
    '''...'''
    segment_main, sender = sock.recvfrom(1024*32)

    segment_number: int = int.from_bytes(segment_main[:2], byteorder='big')
    header_offset_end: int = int.from_bytes(segment_main[2:3])
    fullfilename: str = segment_main[3:header_offset_end].decode('utf-8')
    subdata: bytes = segment_main[header_offset_end:]

    sock.sendto(segment_number.to_bytes(2) + segment_number.to_bytes(2), sender)

    return subdata, segment_number, fullfilename, sender


def accept_file_data(sock: socket.socket) -> tuple[bytes, str]:
    ...   


def accept_file_data(sock: socket.socket) -> tuple[bytes, str]:
    '''...'''
    buffer = []
    interval = []

#    segment_data, segment_number, fullfilename, sender = accept_file_transfer(sock)
#    segment_number_old = segment_number
#    segment_number_max = segment_number
#    buffer = [segment_data] + ([None] * segment_number_max)
#    sock.settimeout(1)

    start_offset = None
    end_offset = None
    previous_offset = None

    increase_buffer: list = lambda: [None] * (segment_number - segment_number_max) + buffer

    request = b''
    while segment_number != 0:
        try:
            segment: bytes = sock.recv(1024*32)
            segment_number = int.from_bytes(segment[:2], byteorder='big')
        except socket.timeout:
            sock.send_to(interval.from_bytes())
#            if not request:
#                sock.sendto(segment_number.to_bytes(byteorder='big'), sender)
#                if failed == 10:
#                    buffer = None
#                    break
        else:
            if segment_number_max == 0 or segment_number_max < segment_number:
                buffer = increase_buffer()
                segment_number_max = segment_number
         
            segment_position = segment_number_max - segment_number
            buffer[segment_position] = segment[2:]
            interval = add_interval(interval, segment_number)
            accept_bar(
                (segment_number_max - segment_number) + 1,
                segment_number_max + 1
            )

    return buffer, fullfilename


