import collections
import asyncio

class AsyncDeque:
    def __init__(self, loop=None):
        self._queue = collections.deque()
        self._getters = collections.deque()

    def __len__(self):
        return len(self._queue)

    def __iter__(self):
        return list(self._queue).__iter__()
        
    def _wake_next(self):
        while self._getters:
            future = self._getters.pop()
            if not future.done():
                future.set_result(None)
                break

    def append(self, x):
        self._queue.append(x)
        self._wake_next()

    def appendleft(self, x):
        self._queue.appendleft(x)
        self._wake_next()

    def extend(self, iterable):
        for x in iterable:
            self.append(x)

    def extendleft(self, iterable):
        for x in iterable:
            self.appendleft(x)

    def clear(self):
        self._queue.clear()

    async def pop(self):
        while not self._queue:
            getter = asyncio.Future()
            self._getters.appendleft(getter)
            await getter
        return self._queue.pop()

    async def popleft(self):
        while not self._queue:
            getter = asyncio.Future()
            self._getters.appendleft(getter)
            await getter
        return self._queue.popleft()
