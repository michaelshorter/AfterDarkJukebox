# 🎬 Pi Jukebox

A coin-operated video jukebox built on a Raspberry Pi 5. Press a letter and number on a keyboard to play a video. Drop a coin through an IR break beam sensor to trigger a smooth fade to black. Videos and assets are stored on a USB drive for easy content updates.

---

## How It Works

1. The jukebox starts automatically on boot and displays an idle screen
2. Press a letter key followed by a number key to select and play a video (e.g. `A` + `1` plays `A1.mp4`)
3. While a video is playing, keyboard selections are ignored
4. Drop a coin through the IR sensor to fade the video out smoothly and return to the idle screen
5. Videos end naturally and the idle screen is restored automatically

---

## Hardware Required

| Component | Notes |
|---|---|
| Raspberry Pi 5 | Main controller |
| Official Pi 27W USB-C PSU | 5V 5A — do not use underpowered supplies |
| USB keyboard | Wired or wireless |
| HDMI display or projector | Any resolution |
| IR break beam sensor (3mm) | Signal wire to GPIO 18, powered at 5V |
| USB drive | Labelled `JUKEBOX`, contains videos and assets |

---

## Wiring

**IR Break Beam Sensor**
| Sensor wire | Pi connection |
|---|---|
| Emitter red | 5V |
| Emitter black | GND |
| Receiver red | 5V |
| Receiver black | GND |
| Receiver white (signal) | GPIO 18 |

---

## USB Drive Structure

Format a USB drive, label it `JUKEBOX`, and create this folder structure:

```
JUKEBOX/
├── videos/
│   ├── A1.mp4
│   ├── A2.mp4
│   ├── B1.mp4
│   └── ...
└── idle.png
```

**Valid letters:** `A B C D E F G H J K L M N Q R S T U V`  
**Valid numbers:** `0–9`

### Generating idle.png

Run this once with the USB drive mounted to generate a 1280×720 idle screen:

```bash
python3 -c "
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (1280, 720), (0, 0, 0))
draw = ImageDraw.Draw(img)
font = ImageFont.load_default(size=48)
text = 'Please make your selection'
bbox = draw.textbbox((0, 0), text, font=font)
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text(((1280 - w) // 2, (720 - h) // 2), text, fill=(255, 255, 255), font=font)
img.save('/media/jukebox/JUKEBOX/idle.png')
print('idle.png saved')
"
```

---

## Installation

```bash
# Install git if needed
sudo apt install git

# Clone the repo
git clone https://github.com/YOUR_USERNAME/pi-jukebox.git
cd pi-jukebox

# Run the setup script
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Install all system dependencies
- Create a Python virtual environment
- Install all Python packages
- Set up autostart on boot

---

## Pi OS Configuration

Add the following to `/boot/firmware/config.txt` under `[all]`:

```ini
[all]
hdmi_force_hotplug=1
hdmi_drive=2
avoid_warnings=1
gpu_mem=128
```

This forces HDMI output on boot regardless of display type, suppresses low voltage warnings, and reduces GPU memory usage.

---

## Reduce System Load

Run these once to disable unused services and reduce power draw:

```bash
sudo systemctl disable bluetooth
sudo systemctl disable wpa_supplicant
sudo systemctl disable cups
sudo systemctl disable avahi-daemon
```

---

## Running

The jukebox starts automatically on boot once autostart is configured. To run manually:

```bash
~/run_jukebox.sh
```

The script will wait for the USB drive to mount before starting.

---

## Configuration

All settings are at the top of `jukebox.py`:

| Variable | Default | Description |
|---|---|---|
| `VIDEO_DIR` | `/media/jukebox/JUKEBOX/videos` | Folder containing video files |
| `IDLE_IMAGE` | `/media/jukebox/JUKEBOX/idle.png` | Idle screen image |
| `BEAM_PIN` | `18` | GPIO pin for IR beam signal wire |
| `FADE_DURATION` | `3` | Fade out duration in seconds |
| `FADE_STEPS` | `100` | Number of steps in the fade (higher = smoother) |
| `WINDOW_WIDTH` | `1280` | Display width in pixels |
| `WINDOW_HEIGHT` | `720` | Display height in pixels |

---

## Controls

| Input | Action |
|---|---|
| Letter key | Select letter |
| Number key | Play video (e.g. `A` + `1` → `A1.mp4`) |
| Coin drop (IR beam) | Smooth fade to black and return to idle |
| `ESC` | Quit the application |

---

## Dependencies

| Package | Purpose |
|---|---|
| `python-vlc` | Video playback with hardware acceleration |
| `pygame` | Keyboard input and display window |
| `gpiozero` | GPIO button/sensor interface |
| `lgpio` | GPIO backend for Raspberry Pi 5 |
| `Pillow` | Idle image generation |

---

## Troubleshooting

**No video plays** — check the file exists on the USB drive with the correct name format (e.g. `A1.mp4`)

**No audio** — check VLC audio output; the script uses auto-detection

**HDMI not detected on boot** — ensure `hdmi_force_hotplug=1` is in `config.txt` and power the display before the Pi

**Low voltage warning** — use the official Raspberry Pi 27W USB-C power supply

**Script won't start on boot** — check the USB drive is inserted and labelled `JUKEBOX` correctly
