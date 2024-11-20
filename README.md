# ytm-listener

a quick wrapper over [ytmusicapi](https://github.com/sigma67/ytmusicapi) to expose the latest track from listen history to other services

## installing
use a venv:

```bash
$ python -m venv venv
$ . venv/bin/activate.fish
$ pip install -r requirements.txt
```

## running

1. set up a `browser.json` with account cookies as defined in the [ytmusicapi docs](https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html)
   oauth login doesn't work anymore, a private firefox session is most reliable as the user agent remains static (close the session after you copy the cookies)
2. optionally set up a `.env` with a Sentry DSN, this is useful so you can tell if authentication fails
   ```ini
   USE_SENTRY=1
   SENTRY_DSN=https://UID@sentry/PID
   ```
3. run it using either the flask dev server (`flask run`), or some wsgi thing

## usage
you can `GET /state` or `GET /state/now`, the latter will do an instant refresh

there's no way to tell if playback stopped, so there's a bit of a heuristic
