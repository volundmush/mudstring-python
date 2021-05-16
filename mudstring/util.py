
class OutBuffer:
    def __init__(self, buffer: bytearray):
        self.buffer = buffer

    def write(self, b: bytes):
        self.buffer.extend(b)

    def flush(self):
        pass
