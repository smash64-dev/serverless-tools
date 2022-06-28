from argparse import ArgumentError
import copy
import socket
import time
from enum import Enum

from util.message import MessageBuffer
import kaillera.models as Kaillera
from kaillera.models import (
    KailleraMessage,
    MessageType,
    ServerFullException,
    ServerNoHelloException,
    ServerRejectException
)


class ConnType(Enum):
    LAN = 1
    EXCELLENT = 2
    GOOD = 3
    AVERAGE = 4
    LOW = 5
    BAD = 6


class Client:
    def __init__(self, host: str, port: int, retry: int = 1, timeout: int = 2):
        self.host = host
        self.server_port = port
        self.user_port = 0
        self.retry = retry
        self.timeout = timeout

        self.type_ = KailleraMessage
        self.client_buffer = MessageBuffer(manage=True, as_=self.type_)
        self.server_buffer = MessageBuffer(as_=self.type_)

        self.pub_sock = self.__socket_connect(host, self.server_port)
        self.priv_sock = None

    def send_message(self, message: KailleraMessage) -> MessageBuffer:
        if not self.priv_sock:
            # Explicitly require a connect() call first
            raise ArgumentError("You must connect() run first")

        self.client_buffer.add(message)
        raw = self.__send_raw(self.priv_sock, self.client_buffer.encode())

        response = MessageBuffer(buffer=raw, as_=self.type_)
        [self.server_buffer.add(m) for m in response]
        return response

    def connect(self, username: str, client: str,
                conn: ConnType = None) -> MessageBuffer:
        if not self.priv_sock:
            self.__hello()

        join_buffer = MessageBuffer([], as_=self.type_)
        join_types = [
            MessageType.CLIENT_JOIN, MessageType.SERVER_REJECT,
            MessageType.SERVER_NOTICE, MessageType.SERVER_STATUS,
        ]

        client_info = Kaillera.ClientInfo(username, client, conn.value)
        response: MessageBuffer = self.send_message(client_info)

        while type(response) == MessageBuffer:
            message: KailleraMessage
            for message in response:
                if MessageType(message.type_) in join_types:
                    join_buffer.add(message)

                if MessageType(message.type_) == MessageType.CLIENT_JOIN:
                    return join_buffer
                elif MessageType(message.type_) == MessageType.SERVER_REJECT:
                    user, id, reason, _ = message.data.decode().split('\0')
                    raise ServerRejectException(user, ord(id), reason)

            response = self.send_message(copy.deepcopy(Kaillera.ClientAck()))
        return join_buffer

    def chat(self, message: str = '') -> MessageBuffer:
        return self.send_message(Kaillera.ChatGlobal(message))

    def disconnect(self, message: str = '') -> MessageBuffer:
        return self.send_message(Kaillera.ClientQuit(message))

    def ping(self, count: int = 3) -> tuple[int, int]:
        rtts = []
        while len(rtts) < count:
            try:
                rrt = None
                send_time = time.time()
                pong = self.__send_raw(self.pub_sock, b'PING\0')
                recv_time = time.time()

                if pong == b'PONG\0':
                    rrt = int((recv_time - send_time) * 1000)
            except socket.timeout:
                pass

            rtts.append(rrt)

        success = [i for i in rtts if i is not None]
        if not success:
            raise socket.timeout

        average = int(sum(success) / len(success)) if len(success) else None
        return average, len(rtts)-len(success)

    def __hello(self) -> int:
        try:
            response = self.__send_raw(self.pub_sock, b'HELLO0.83\0')
        except socket.timeout:
            # TODO: figure out why the server does this
            if self.ping(1)[1] == 0:
                msg = "Server is refusing to respond to a hello packet"
                raise ServerNoHelloException(msg)
            else:
                raise

        port = response.decode().rstrip('\0').replace('HELLOD00D', '')
        if port != 'TOO':
            self.user_port = int(port)
            self.priv_sock = self.__socket_connect(self.host, self.user_port)
            return port
        else:
            raise ServerFullException(port)

    def __send_raw(self, client: socket.socket, message: bytes,
                   retry: bool = False) -> bytes:
        attempts = 0
        while attempts < self.retry:
            try:
                client.sendall(message)
                recv, _, _, _ = client.recvmsg(4096)
                return recv
            except socket.timeout:
                if retry and attempts < self.retry:
                    attempts += 1
                else:
                    raise

    def __socket_connect(self, host: str, port: int):
        attempts = 0

        while attempts < self.retry:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                client.settimeout(self.timeout)
                client.connect((host, port))
                return client
            except socket.timeout:
                if self.retry and attempts < self.retry:
                    attempts += 1
                else:
                    raise
