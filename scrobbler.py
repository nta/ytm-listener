import pylast
import time, threading, traceback, os

def convert_track(track):
    return {
        'artist': track['artistNames'],
        'title': track['title'],
        'album': track['albumName'],
        'album_artist': track['artists'][0]['name'],
        'duration': track['duration_seconds']
    }

class Scrobbler:
    def __init__(self):
        self.network = pylast.LastFMNetwork(os.getenv("LASTFM_API_KEY", ""), os.getenv("LASTFM_API_SECRET", ""))
        self.network.session_key = os.getenv("LASTFM_SESSION_KEY", "")

        self.exit_event = threading.Event()

        self.cur_track = None

        self.scrobble_at = 0
        self.track_start = 0

        self.listener = threading.Thread(target=self.run)
        self.listener.start()

    def quit(self, *args):
        self.exit_event.set()

    # TODO: bunch of shared logic, hm-
    def run(self):
        while not self.exit_event.is_set():
            try:
                self.update()
            except Exception as e:
                traceback.print_exc()

            self.exit_event.wait(1)

    def scrobble(self, track):
        print("scrobbling:", track['title'])

        self.network.scrobble(
            **convert_track(track),
            timestamp = int(self.track_start)
        )

    def update(self):
        if self.scrobble_at > 0 and time.time() > self.scrobble_at:
            self.scrobble_at = 0

            self.scrobble(self.cur_track)

    def update_track(self, track):
        # cancel any pending track timer (.. we better not be missing a track here! hard to align updates)
        self.scrobble_at = 0

        # a <30s track should not count
        if track['duration_seconds'] < 30:
            return

        # store the time for later
        self.track_start = time.time()

        # say we're playing a track!
        self.network.update_now_playing(
            **convert_track(track)
        )

        # queue the scrobble
        self.cur_track = track
        self.scrobble_at = time.time() + (track['duration_seconds'] / 2)