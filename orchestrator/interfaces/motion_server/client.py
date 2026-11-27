import asyncio
import json
from itertools import count


class MotionRejected(Exception):
    pass


class MotionServerInterface:
    def __init__(self, host, port, heartbeat_timeout, feedback, disconnected):
        self.host = host
        self.port = port
        self.heartbeat_timeout = heartbeat_timeout
        self.feedback = feedback
        self.disconnected = disconnected
        self.writer = None
        self.requests = {}
        self.ids = count(1)

    @property
    def connected(self):
        return self.writer is not None and not self.writer.is_closing()

    async def run(self):
        while True:
            try:
                async with asyncio.timeout(3):
                    reader, self.writer = await asyncio.open_connection(
                        self.host, self.port, limit=1024 * 1024
                    )
                await self.receive(reader)
            except (OSError, ValueError, TimeoutError) as error:
                self.disconnected(str(error) or 'Motion Server 연결 시간 초과')
            finally:
                writer, self.writer = self.writer, None
                if writer:
                    writer.close()
                pending = list(self.requests.values())
                self.requests.clear()
                for future in pending:
                    if not future.done():
                        future.set_exception(ConnectionError('Motion Server 연결 종료'))
                if writer:
                    try:
                        await writer.wait_closed()
                    except OSError:
                        pass
            await asyncio.sleep(0.5)

    async def receive(self, reader):
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self.heartbeat_timeout
        while True:
            async with asyncio.timeout_at(deadline):
                line = await reader.readline()
            if not line:
                raise ConnectionError('Motion Server 연결 종료')
            message = json.loads(line)
            kind = message.get('type')
            if kind == 'system/heartbeat':
                sequence = message.get('sequence')
                if type(sequence) is not int or not 0 <= sequence < 2**32:
                    raise ValueError('잘못된 Motion Server Heartbeat')
                self.write({'type': 'system/heartbeat/ack',
                            'sequence': (sequence + 1) % 2**32})
                deadline = loop.time() + self.heartbeat_timeout
            elif kind == 'system/feedback':
                self.feedback(message)
            else:
                future = self.requests.get(message.get('request_id'))
                if future is not None and not future.done():
                    future.set_result(message)

    def write(self, message):
        if not self.connected:
            raise ConnectionError('Motion Server 연결 없음')
        self.writer.write((json.dumps(message, allow_nan=False) + '\n').encode('utf-8'))

    async def request(self, cmd, **fields):
        key = f'dt-demo-{next(self.ids)}'
        future = asyncio.get_running_loop().create_future()
        self.requests[key] = future
        try:
            self.write({'cmd': cmd, 'request_id': key, **fields})
            response = await future
        finally:
            self.requests.pop(key, None)
        if response.get('type') != cmd:
            raise ValueError(f'예상하지 않은 응답: {response.get("type")}')
        if response.get('result') == 'fail':
            raise MotionRejected(response.get('failure', {}).get('message', cmd))
        if response.get('result') != 'success':
            raise ValueError(f'잘못된 Motion Server 응답: {cmd}')
        return response.get('data', {})
