import socket, sys, json, base64


class SocketType:
    STATUS = 'status'
    MESSAGE = 'massage'
    FILE = 'file'


def get_socket() -> socket.socket:
    return socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )


def send_status(address: tuple, sock: socket.socket) -> None:
    request = json.dumps([{'type': SocketType.STATUS, 'data': True}])
    sock.sendto(request.encode('utf-8'), address)


def send_file(address: tuple, path: str) -> bool:
    with open(path, '+rb') as file:
        data_file = file.read()
    request = json.dumps([{
        'type': SocketType.FILE,
        'data': base64.b64encode(data_file).decode('ascii'),
        'name': path.split('/')[-1]
    }])
    with get_socket() as sock:
        sock.sendto(
            request.encode('utf-8'),
            address
        )

        response: dict = json.loads(sock.recv(1024).decode('utf-8'))[0]
        if response.get('type') == SocketType.STATUS:
            status = response.get('data')

        return status


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


def server(address: tuple) -> None:
    with get_socket() as server:
        server.bind(address)
        print('start server')

        response, sender = server.recvfrom(1024)
        response: dict = json.loads(response.decode('utf-8'))[0]
        match response:
            case {'type': SocketType.MESSAGE, 'data': data}:
                print(data)
                send_status(sender, server)
            case {'type': SocketType.FILE, 'data': data, 'name': name}:
                with open(name, '+wb') as file:
                    file.write(base64.b64decode(data))
                print('[' + '▮'*10 + ']', '100%', name)
                send_status(sender, server)


def main(tcomand: list[str]):
    ip, port = tcomand[0].split(':')
    address = (ip, int(port))

    match tcomand[1:]:
        case ['-m', message]:
            response = send_message(address, message)
        case ['-f', path]:
            response = send_file(address, path)
        case _:
            response = server(address)

    if response:
        print(f'Status: [ {response} ]')


if __name__ == '__main__':
    main(sys.argv[1:])
