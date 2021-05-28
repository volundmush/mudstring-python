
class OutBuffer:
    def __init__(self, buffer: bytearray):
        self.buffer = buffer

    def write(self, b: str):
        self.buffer.extend(b.encode())

    def flush(self):
        pass
