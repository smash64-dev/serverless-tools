from enum import Enum

from message import Message
import primitives as types


class MessageType(Enum):
    CLIENT_QUIT = 1
    CLIENT_JOIN = 2
    CLIENT_INFO = 3
    SERVER_STATUS = 4
    SERVER_ACK = 5
    CLIENT_ACK = 6
    CHAT_GLOBAL = 7
    CHAT_GAME = 8
    KEEP_ALIVE = 9
    GAME_CREATE = 10
    GAME_QUIT = 11
    GAME_JOIN = 12
    GAME_PLAYER = 13
    GAME_STATUS = 14
    GAME_KICK = 15
    GAME_CLOSE = 16
    GAME_START = 17
    GAME_DATA = 18
    GAME_CACHE = 19
    GAME_DROP = 20
    GAME_READY = 21
    SERVER_REJECT = 22
    SERVER_NOTICE = 23
    UNKNOWN = 100


class KailleraMessage(Message):
    def __init__(self, id: int = None, size: int = 0,
                 type_: MessageType = MessageType.UNKNOWN,
                 data: bytes = b''):
        super().__init__(id=id, size=size, type_=type_, data=data)

    def __repr__(self):
        return f"{MessageType(self.type_)} (len = {self.size}): {self.data}"

    @classmethod
    def decode(self, stream: bytes) -> Message:
        id = int.from_bytes(stream[0:1], types.ORDER)
        size = int.from_bytes(stream[2:3], types.ORDER)
        type_ = MessageType(int.from_bytes(stream[4:5], types.ORDER))
        data = stream[5:(4+size)]   # type is included in size
        return KailleraMessage(id=id, size=size, type_=type_, data=data)

    def encode(self):
        return b''.join([
            self.id.to_bytes(2, types.ORDER),
            self.size.to_bytes(2, types.ORDER),
            int(self.type_.value).to_bytes(1, types.ORDER),
            self.data
        ])


class ChatGlobal(KailleraMessage):
    def __init__(self, message: str, username: str = '', id: int = None):
        super().__init__(id=id, type_=MessageType.CHAT_GLOBAL, data=b''.join([
            types.stringz(username),
            types.stringz(message),
        ]))


class ClientAck(KailleraMessage):
    def __init__(self, id: int = None):
        values = [types.uint(i, 4) for i in range(4)]
        data = b'\0' + b''.join(values)
        super().__init__(id=id, type_=MessageType.CLIENT_ACK, data=data)


class ClientInfo(KailleraMessage):
    def __init__(self, username: str, client_name: str,
                 connection_type: int = 1, id: int = None):
        super().__init__(id=id, type_=MessageType.CLIENT_INFO, data=b''.join([
            types.stringz(username),
            types.stringz(client_name),
            types.uint(connection_type, 1),
        ]))


class ClientQuit(KailleraMessage):
    def __init__(self, message: str, id: int = None):
        super().__init__(id=id, type_=MessageType.CLIENT_QUIT, data=b''.join([
            bytes([0, 255, 255]),
            types.stringz(message)
        ]))


class ServerFullException(Exception):
    pass


class ServerRejectException(Exception):
    def __init__(self, username: str, user_id: int, reason: str):
        self.username = username
        self.user_id = user_id
        self.reason = reason


class ServerNoHelloException(Exception):
    pass


class P2PType(Enum):
    CLIENT_REQUEST = 0
    PING_PING = 1
    PLAYER_READY = 2
    SYNC = 3
    SYNC_DELAY = 4
    GAME_LOAD = 5
    GAME_START = 6
    GAME_DATA = 7
    GAME_DROP = 8
    PLAYER_CHAT = 9
    CLIENT_EXIT = 10
    CLIENT_ACCEPT = 16
    PING_ECHO = 17
    PLAYER_NOT_READY = 18
    SYNC_INIT = 19
    GAME_LOADING = 21
    CLIENT_REJECT = 32
    SYNC_GUESS = 35
    SYNC_ADJUST = 67
    UNKNOWN = 100


class P2PMessage(Message):
    def __init__(self, id: int = None, size: int = 0,
                 type_: P2PType = P2PType.UNKNOWN,
                 data: bytes = b''):
        super().__init__(id=id, size=size, type_=type_, data=data)

    def __repr__(self):
        return f"{P2PType(self.type_)} (len = {self.size}): {self.data}"

    @classmethod
    def decode(self, stream: bytes) -> Message:
        id = int(stream[0])
        size = int(stream[1])
        type_ = P2PType(int(stream[2]))
        data = stream[3:(3+size)]   # type is included in size
        return P2PMessage(id=id, size=size, type_=type_, data=data)

    def encode(self):
        return b''.join([
            self.id.to_bytes(1, types.ORDER),
            self.size.to_bytes(1, types.ORDER),
            int(self.type_.value).to_bytes(1, types.ORDER),
            self.data
        ])


class P2PChat(P2PMessage):
    def __init__(self, message: str, frame: int = 5, id: int = None):
        super().__init__(
            id=id,
            type_=P2PType.PLAYER_CHAT,
            data=b''.join([
                types.uint(frame, 4),
                types.stringz(message),
            ]))


class P2PClientAccept(P2PMessage):
    def __init__(self, id: int = None):
        super().__init__(
            id=id,
            type_=P2PType.CLIENT_ACCEPT,
            data=b'')


class P2PClientExit(P2PMessage):
    def __init__(self, id: int = None):
        super().__init__(
            id=id,
            type_=P2PType.CLIENT_EXIT,
            data=b'')


class P2PClientRequest(P2PMessage):
    def __init__(self, username: str, client_name: str, id: int = None):
        super().__init__(id=id, type_=P2PType.CLIENT_REQUEST,
                         data=b''.join([
                            types.stringn(username, 32),
                            types.stringn(client_name, 128),
                         ]))


class P2PRejectException(Exception):
    pass
