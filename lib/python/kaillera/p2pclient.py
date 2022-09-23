import copy
import socket

from message import MessageBuffer

import kaillera.models as P2P
from kaillera.models import (
    P2PMessage,
    P2PType,
    P2PRejectException,
)


class P2PClient:
    def __init__(self, host: str, port: int, retry: int = 1, timeout: int = 2):
        self.host = host
        self.server_port = port
        self.user_port = 0
        self.retry = retry
        self.timeout = timeout

        self.type_ = P2PMessage
        self.client_buffer = MessageBuffer(manage=True, as_=self.type_,
                                           meta_size=2)
        self.server_buffer = MessageBuffer(as_=self.type_, meta_size=2)

        self.socket = self.__socket_connect(host, self.server_port)

    def send_message(self, message: P2PMessage,
                     wait: bool = True) -> MessageBuffer:
        self.client_buffer.add(message)
        raw = self.__send_raw(self.socket, self.client_buffer.encode(),
                              wait=wait)

        response = MessageBuffer(buffer=raw, as_=self.type_, meta_size=2)
        [self.server_buffer.add(m) for m in response]
        return response

    def connect(self, username: str,
                client: str) -> tuple[bool, MessageBuffer]:
        join_buffer = MessageBuffer([], as_=self.type_, meta_size=2)
        join_types = [
            P2PType.CLIENT_ACCEPT, P2PType.CLIENT_REJECT, P2PType.PLAYER_CHAT
        ]

        request = P2P.P2PClientRequest(username, client)
        response = self.send_message(request)

        attempts = 0
        while type(response) == MessageBuffer and attempts < 3:
            message: P2PMessage
            for message in response:
                if P2PType(message.type_) in join_types:
                    join_buffer.add(message)

                if P2PType(message.type_) == P2PType.CLIENT_ACCEPT:
                    self.send_message(P2P.P2PClientAccept())
                    return [True, join_buffer]
                elif P2PType(message.type_) == P2PType.CLIENT_REJECT:
                    raise P2PRejectException()

            attempts += 1
            response = self.send_message(copy.deepcopy(request))

        return [False, join_buffer]

    def chat(self, message: str = '', frame: int = 5,
             wait: bool = True) -> MessageBuffer:
        return self.send_message(P2P.P2PChat(message, frame), wait=wait)

    def disconnect(self) -> MessageBuffer:
        # there will not be a response
        return self.send_message(P2P.P2PClientExit(), wait=False)

    def get_host_info(self, buffer: MessageBuffer) -> tuple[str, str]:
        message: P2PMessage
        for message in buffer:
            if P2PType(message.type_) == P2PType.CLIENT_ACCEPT:
                return list(filter(len, message.data.decode().split('\0')))

        return [None, None]

    def __send_raw(self, client: socket.socket, message: bytes,
                   retry: bool = False, wait: bool = True) -> bytes:
        attempts = 0
        while attempts < self.retry:
            try:
                client.sendall(message)

                if wait:
                    recv, _, _, _ = client.recvmsg(8192)
                    return recv
                else:
                    return b''
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
