import socket, sys, json


class SockType:
    MESSAGE = 'massage'


def get_socket() -> socket.socket:
    return socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )


def send_message(recipient: tuple, message: str) -> None:
    request = json.dumps(
        [{'type': SockType.MESSAGE, 'data': message}]
    )
    with get_socket() as sock:
        sock.sendto(
            request.encode('utf-8'),
            recipient
        )


def server(recipient: tuple) -> None:
    with get_socket() as server:
        server.bind(recipient)
        print('start server')

        while True:
            response = server.recv(1024)
            print(json.loads(response.decode('utf-8')))


def main(tcomand: list[str]):
    ip, port = tcomand[0].split(':')
    recipient = (ip, int(port))

    match tcomand[1:]:
        case ['-m', message]:
            send_message(recipient, message)
        case _:
            server(recipient)


if __name__ == '__main__':
    main(sys.argv[1:])
