
class OutBuffer:
    def __init__(self, buffer: bytearray):
        self.buffer = buffer

    def write(self, b: bytes):
        if isinstance(b, str):
            b = b.encode()
        self.buffer.extend(b)

    def flush(self):
        pass
