from __future__ import annotations
from typing import TypeVar, Union

import enum
import util.primitives as types


class Message:
    def __init__(self, id: int = None, size: int = 0,
                 type_: enum.Enum = None, data: bytes = b''):
        if type_ is None:
            self.__decode(data)
        else:
            self.id = id
            self.size = size if size else len(data) + 1
            self.type_ = type_
            self.data = data.ljust(size-1, b'\0') if size else data

    def __repr__(self):
        return f"{self.type_} (len = {self.size}): {self.data}"

    @classmethod
    def decode(self, stream: bytes) -> bytes:
        raise NotImplementedError

    def encode(self) -> bytes:
        raise NotImplementedError

    def __decode(self, stream: bytes):
        message: Message = self.decode(stream)
        self.id = message.id
        self.size = message.size
        self.type_ = message.type_
        self.data = message.data


class MessageBuffer:
    T = TypeVar("T")

    def __init__(self, buffer: Union[list[T], bytes] = [], tx_size: int = 5,
                 manage: bool = False, as_: T = Message):
        self.manage = manage
        self.tx_size = tx_size
        self.type_ = as_

        if type(buffer) == bytes:
            self.buffer = self.decode(buffer, manage, as_)
        else:
            self.buffer = buffer

    def __getitem__(self, item):
        return self.buffer[item]

    def __iter__(self):
        return iter(self.buffer)

    def __len__(self):
        return len(self.buffer)

    def __repr__(self):
        return f"Messages: {len(self.buffer)}:\n" + '\n'.join([
            f"  {m.id:0>3}: {m}" for m in self.buffer
        ])

    def __reversed__(self):
        return iter(reversed(self.buffer))

    def add(self, message: Message, manage: bool = None) -> int:
        self.buffer.sort(key=lambda m: m.id, reverse=True)
        manage = manage if manage is not None else self.manage

        if manage:
            message.id = self.buffer[0].id + 1 if self.buffer else 0

        if not any(m.id == message.id for m in self.buffer):
            self.buffer.insert(0, message)
        return message.id

    @classmethod
    def decode(self, stream: bytes, manage: bool = False,
               as_: T = Message) -> MessageBuffer:
        messages = []
        count = int.from_bytes(stream[0:1], types.ORDER)

        offset = 1
        message: Message
        for _ in range(count):
            message = as_.decode(stream[offset:])
            messages.append(message)
            offset = offset + 4 + message.size

        return MessageBuffer(messages, tx_size=count, manage=manage, as_=as_)

    def encode(self) -> bytes:
        messages = []
        size = max([len(self.buffer), self.tx_size])
        self.buffer.sort(key=lambda m: m.id, reverse=True)

        message: Message
        for _, message in zip(range(size), self.buffer):
            messages.append(message.encode())

        count = len(messages).to_bytes(1, types.ORDER)
        return count + b''.join(messages)
