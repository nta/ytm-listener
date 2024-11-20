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

### wsgi thing
to use gunicorn, you can do the following:
1. `pip install -e .[gunicorn]`
2. make a systemd user service (`~/.config/systemd/user/ytm-listener.service`):
    ```ini
    [Install]
    WantedBy=default.target

    [Service]
    WorkingDirectory=/home/nta/dev/ytm-listener/
    Environment=PATH=/home/nta/dev/ytm-listener/venv/bin/:$PATH
    ExecStart=/home/nta/dev/ytm-listener/venv/bin/gunicorn --workers 1 --bind 127.0.0.1:8173 app:app
    ExecReload=/bin/kill -s HUP $MAINPID
    KillMode=mixed
    TimeoutStopSec=5
    Restart=on-failure
    RestartSec=10s
    ```
3. enable and/or start it: `systemctl --user enable ytm-listener && systemctl --user start ytm-listener`

## usage
you can `GET /state` or `GET /state/now`, the latter will do an instant refresh

there's no way to tell if playback stopped, so there's a bit of a heuristic

### homeassistant sensor
for validation/logging, i've got this storing state to a homeassistant sensor- here's the config
```yaml
sensor:
  - platform: rest
    resource: http://driftveil:8073/state
    name: ytm_nta
    value_template: "{{ value_json.artistNames }} - {{ value_json.title }}"
    availability: "{{ value_json is not none }}"
    json_attributes:
      - albumName
      - artistNames
      - videoId
      - duration
      - likeStatus
      - thumbnailUrl
```
