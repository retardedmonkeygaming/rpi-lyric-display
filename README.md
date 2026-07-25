# rpi-lyric-display

A Raspberry Pi lyric display and editor for 1602A character LCDs.

This project turns a Raspberry Pi into a smart lyric sync engine with a web dashboard, touch button controls, auto-formatted 16x2 lyric rendering, and remote recording triggers.

## Features

- 1602A LCD playback engine with timed lyric synchronization
- Web-based upload, song library, editor, and remote play controls
- Automatic `.lrc` parsing into timed 16x2 lines for LCD display
- Touch-button navigation for menu browsing, selection, stop, and reset
- Sentiment-based mood analysis and emoji suggestions
- Automatic line emoji injection and timestamp nudging
- Plugin loader for custom extensions in `plugins/`
- Lightweight SQLite database storage with schema initialization from `database/schema.sql`

## Hardware Requirements

- Raspberry Pi with Python 3
- 1602A character LCD in 4-bit mode
- Single touch/tactile button on GPIO 27 for navigation
- Optional peripherals (not required): buzzer, DHT sensor

## Pin Configuration

The default GPIO pin mapping is defined in `config.py`:

- LCD RS: GPIO 22
- LCD EN: GPIO 17
- LCD D4: GPIO 25
- LCD D5: GPIO 24
- LCD D6: GPIO 23
- LCD D7: GPIO 18
- Touch input button: GPIO 27

Optional reserved pins:

- BUZZER_PIN = GPIO 2
- DHT_SENSOR_PIN = GPIO 4

## Software Requirements

Install dependencies from `requirements.txt`:

```bash
python3 -m pip install -r requirements.txt
```

Required Python packages:

- Flask >= 3.0.0
- Adafruit-Blinka >= 8.0.0
- adafruit-circuitpython-charlcd >= 3.5.0
- RPi.GPIO >= 0.7.0
- pydantic >= 2.0.0

## Getting Started

1. Clone the repository:

```bash
git clone https://github.com/retardedmonkeygaming/rpi-lyric-display.git
cd rpi-lyric-display
```

2. Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

3. Run the application:

```bash
python3 app.py
```

4. Open the web dashboard from another device on the same network:

```text
http://<raspberry-pi-ip>:5000
```

The app will also print the active local IP address and dashboard URL in the console.

## Web Dashboard

The web UI provides:

- Track upload via `.lrc` files
- Song library browsing and search
- Track editing and timestamp adjustment
- Live lyric preview in a simulated 1602 display
- Sentiment analysis and auto-emoji assignment
- Remote recording trigger for hardware playback

### Uploading Tracks

Upload a track using the library page form with:

- Song title
- Artist name
- Optional tags
- `.lrc` lyrics file

The app parses the `.lrc` file into a timed lyric timeline and saves it to SQLite.

### Editor Page

The editor page allows you to:

- review and edit lyric timestamps
- adjust both 16-character LCD lines per timestamp
- nudge all timestamps by ±200 ms
- trigger sentiment analysis and emoji suggestions
- auto-inject emojis for each lyric line
- preview playback timing in the browser simulator

## Touch Controls

The onboard touch button supports gestures:

- Short Press: open the song menu / advance selection
- Double Tap: select the highlighted song and start countdown playback
- Triple Tap: stop playback / cancel
- Long Press: reset to idle menu or stop playback

## LCD Playback

`core/lcd_engine.py` drives the 1602A LCD and includes:

- boot animation
- two-line rendering with padding
- custom character support for icons
- wall-clock lyric synchronization

Lyrics are rendered as time-aligned 16x2 pages using `core/lrc_parser.py`, which supports standard LRC timestamp formats and pagination for longer text.

## Database

`database/db.py` manages the SQLite database at `data/lyrics.db` and automatically initializes the schema from `database/schema.sql`.

Stored tables include:

- `songs` for track metadata
- `song_lyrics` for timed lyric pages
- `song_tags` for simple filtering

## Plugin Support

A lightweight plugin loader scans `plugins/*.py` on startup. Create a `plugins/` directory and add Python modules to extend the app without modifying core code.

## API Endpoints

The backend exposes endpoints for remote control and editing, including:

- `POST /upload` — upload and parse a new `.lrc` track
- `POST /api/recording/start` — start LCD recording countdown playback
- `POST /api/remote/play` — remote playback trigger
- `POST /api/songs/<id>/nudge` — shift timestamps by milliseconds
- `POST /api/songs/<id>/auto-emoji-lines` — add emoji icons to lyric lines
- `GET /api/songs/<id>/analyze-sentiment` — analyze mood and suggest an emoji

## Configuration

Update `config.py` to customize:

- GPIO pin assignments
- SQLite database path
- Flask host and port

## Development Notes

- `app.py` builds the Flask app and manages the LCD, database, and touch input loop.
- `core/touch_input.py` handles button gesture detection using `RPi.GPIO`.
- `core/emoji_engine.py` and `core/sentiment.py` provide lyric mood enhancement helpers.
- `web/routes.py` contains the web UI routes and REST API.

## Notes

- If you run the app on a non-Raspberry Pi environment, the hardware-specific imports (`RPi.GPIO`, `digitalio`, `adafruit_character_lcd`) may fail.
- The database and `data/` directory are created automatically when the app starts.

## License

No license is specified in this repository.

