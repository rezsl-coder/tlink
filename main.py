import sys

from tlp import *


def documentation() -> bool:
    status = True
    try:
        with open('README.md', 'r') as file:
            print(file.read())
    except Exception:
        status = False

    return status


def send_message(address: tuple, message: str) -> bool:
    '''Sends the passed message.'''
    with get_socket() as sock:
        send_file_data(message.encode('utf-8'), TypeData.message, sock, address)


def send_file(address: tuple, path: str):
    '''Reads a file from the provided path and sends it.'''
    with open(path, '+rb') as file:
        data = file.read()
    with get_socket() as sock:
        send_file_data(data, path.split('/')[-1], sock, address)


def server(address: tuple) -> bool:
    '''Starts the server.'''
    status = False
    with get_socket() as server:
        server.bind(address)
        print('START SERVER:' f'{address[0]}:{address[1]}')
        try:
            data, fullfilename = accept_file_data(server)
            print(fullfilename, len(data))
            match fullfilename:
                case [TypeData.message]:
                    print(data.decode('utf-8'))
                case fullfilename:
                    with open(fullfilename, '+wb') as file:
                        file.write(data)
            status = True
        except socket.timeout as error:
            print(sender, ', не доступен!')
        except KeyboardInterrupt:
            status = True

    return status


def main(tcommand: list[str]):
    if tcommand[0][0] == '-':
        tcommand = ['0.0.0.0:0'] + tcommand

    status = None
    ip, port = tuple(tcommand[0].split(':'))
    address = (ip, int(port))

    match tcommand[1:]:
        case ['-m', message] if message:
            status = send_message(address, message)
        case ['-f', path] if path:
            status = send_file(address, path)
        case ['-h']:
            status = documentation()
        case ['-m']:
            status = server(address)
        case ['-f']:
            status = server(address)
        case _:
            status = server(address)

    if status:
        print('\r' + f'Status: [ {status} ]')


if __name__ == '__main__':
    main(sys.argv[1:])
