# Pi Jukebox

A Raspberry Pi video jukebox controller. Press a letter then a number on a keyboard to play a video. Press a physical GPIO button to fade the video out smoothly.

---

## Hardware

- Raspberry Pi 5
- Keyboard (USB or Bluetooth)
- Physical stop button wired to GPIO 17 and GND

---

## Requirements

- Raspberry Pi OS (64-bit recommended)
- VLC installed system-wide
- Python 3 with a virtual environment

### Install system dependencies

```bash
sudo apt install vlc python3-lgpio swig
```

### Set up the virtual environment

```bash
python3 -m venv ~/jukebox-env --system-site-packages
source ~/jukebox-env/bin/activate
pip install python-vlc pygame gpiozero
```

---

## Video files

Place `.mp4` files in a folder called `videos/` in the same directory as the script. Name them using a letter followed by a number, e.g.:

```
videos/
  A1.mp4
  A2.mp4
  B1.mp4
```

Valid letters: `A B C D E F G H J K L M N Q R S T U V`  
Valid numbers: `0–9`

---

## Running

```bash
source ~/jukebox-env/bin/activate
python jukebox.py
```

Or use the included launch script:

```bash
chmod +x run_jukebox.sh
~/run_jukebox.sh
```

---

## Controls

| Input | Action |
|---|---|
| Letter key | Select letter |
| Number key | Play video (e.g. A + 1 plays A1.mp4) |
| GPIO 17 button | Fade out and stop current video |
| ESC | Quit |

---

## Configuration

Edit the top of `jukebox.py` to change:

| Variable | Default | Description |
|---|---|---|
| `VIDEO_DIR` | `videos` | Folder containing video files |
| `GPIO_STOP_PIN` | `17` | GPIO pin for the stop button |
| `FADE_DURATION` | `5` | Fade out duration in seconds |
| `FADE_STEPS` | `100` | Smoothness of the fade |

---

## Notes

- VLC handles video decode using hardware acceleration where available
- The fade reduces brightness, contrast, saturation and audio volume simultaneously for a clean fade to black
- Videos are expected to handle their own fade-in via video editing
