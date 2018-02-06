import collections
import random

class SongRequestList:
    "Represents a queue of songs that can be manipulated"

    def __init__(self):
        self.shuffle = False
        self.loop = False

        # Contain the list of songs and upcoming songs.
        # The original list is kept to support looping (aka reloading)
        self.current = None
        self.songs = []
        self.song_queue = collections.deque()

    def add(self, song):
        "Adds a single song request to the queue"
        self.songs.append(song)
        self.song_queue.append(song)

    def extend(self, songs):
        "Adds multiple song requests to the queue"
        self.songs.extend(songs)
        self.song_queue.extend(songs)

    def reset(self, songs, *, loop=False, shuffle=False):
        self.clear()
        self.extend(songs)
        self.loop = loop
        if shuffle:
            self.shuffle_queue()

    def clear(self):
        self.songs.clear()
        self.song_queue.clear()

    def shuffle_queue(self):
        'Randomizes the upcoming songs and enables shuffling'
        self.shuffle = True
        shuffled_items = list(self.song_queue)
        random.shuffle(shuffled_items)
        self.song_queue.clear()
        self.song_queue.extend(shuffled_items)

    def __len__(self):
        return len(self.songs)

    def __iter__(self):
        return self.songs.__iter__()

    def next(self):
        '''Returns the next song, or None if there are no more.

        Will loop if 'loop' is enabled, and will shuffle if 'shuffle' is enabled.
        If there is more than one item and both options are enabled, next()
        will avoid re-playing the last played song.
        '''
        try:
            self.current = self.song_queue.popleft()
            return self.current
        except IndexError:
            if not self.loop or not self.songs:
                return None

            # looping is on, so recreate the list
            new_queue = list(self.songs)

            # shuffle
            if self.shuffle and len(new_queue) > 1:
                random.shuffle(new_queue)

                # prevent double play
                if new_queue[0] == self.current:
                    idx = random.randint(1, len(new_queue) - 1)
                    new_queue[0], new_queue[idx] = new_queue[idx], new_queue[0]

            self.song_queue.extend(new_queue)
            return self.next()
