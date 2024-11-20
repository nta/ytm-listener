from ytmusicapi import YTMusic
from ytmusicapi.exceptions import YTMusicServerError
from flask import Flask
import flask
import sentry_sdk

import os
import sys
import time
import threading
import signal
import traceback

from dotenv import load_dotenv
load_dotenv()

USE_SENTRY = os.getenv("USE_SENTRY", "0") == "1"

if USE_SENTRY:
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "dev")

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        environment=SENTRY_ENVIRONMENT,
    )

app = Flask(__name__)
ytmusic = YTMusic("browser.json")


class Listener:
    def __init__(self, ytmusic):
        self.ytmusic = ytmusic
        self.updating = False
        self.last_track = None
        self.track_end = 0

        self.exit_event = threading.Event()

        self.listener = threading.Thread(target=self.run)
        self.listener.start()

        signal.signal(signal.SIGINT, self.quit)

    def quit(self, *args):
        self.exit_event.set()

        # hack for development as flask's dev server doesn't really.. exit
        sys.exit()

    def run(self):
        while not self.exit_event.is_set():
            try:
                self.update()
            except Exception as e:
                traceback.print_exc()

                if USE_SENTRY:
                    sentry_sdk.capture_exception(e)

            self.exit_event.wait(60)

    def update(self):
        # if executed asynchronously, e.g. from an instant state request
        if self.updating:
            return

        # update!
        try:
            self.updating = True

            history = self.get_history()
            cur_track = history[0]

            # if the video id doesn't match the last track, it's probably a new track
            if self.last_track and cur_track["videoId"] != self.last_track["videoId"]:
                self.update_track(cur_track)

            # store the largest thumbnail image
            if 'thumbnails' in cur_track and cur_track['thumbnails']:
                largest_res = 0

                for thumbnail in cur_track['thumbnails']:
                    res = thumbnail['width'] * thumbnail['height']

                    if res > largest_res:
                        largest_res = res
                        cur_track['thumbnail'] = thumbnail

            # remove feedback tokens and whatnot as they.. change
            if 'feedbackToken' in cur_track:
                del cur_track['feedbackToken']

            if 'feedbackTokens' in cur_track:
                del cur_track['feedbackTokens']

            # store the last track for future reference
            self.last_track = cur_track
        finally:
            self.updating = False

    def update_track(self, track):
        print("new track:", track['title'])

        # add some leeway for pausing the track/repeats/.., since we can't reasonably detect stopping
        self.track_end = time.time() + (track['duration_seconds'] * 1.5)

    def get_current_track(self):
        if time.time() >= self.track_end:
            return None

        return self.last_track

    # wrapper to add error handling at some point
    def get_history(self):
        try:
            return self.ytmusic.get_history()
        except YTMusicServerError as e:
            # sigh- these actually don't retain any response data!
            # https://github.com/sigma67/ytmusicapi/blob/9ce284a7eae9c4cdc04bb098f7549cc5f1c80e22/ytmusicapi/ytmusic.py#L241

            # TODO: handle authorization errors separately

            raise
        except:
            raise


listener = Listener(ytmusic)

# a debug route to get raw history
@app.route("/history")
def history():
    return ytmusic.get_history()


@app.route("/state/now")
def now():
    listener.update()

    return flask.json.jsonify(listener.get_current_track())


@app.route("/state")
def state():
    return flask.json.jsonify(listener.get_current_track())


@app.route("/")
def root():
    return flask.json.jsonify("hello!~")
