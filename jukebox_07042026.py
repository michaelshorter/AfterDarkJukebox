import os
import vlc
import pygame
from gpiozero import Button
import threading
import time

# -----------------------------
# CONFIG
# -----------------------------
VIDEO_DIR = "videos"
VALID_LETTERS = set("ABCDEFGHJKLMNQRSTUV")
VALID_NUMBERS = set("0123456789")
GPIO_STOP_PIN = 17
FADE_DURATION = 5   # seconds
FADE_STEPS = 100
# -----------------------------

current_letter = None
player = None
fade_lock = threading.Lock()

# VLC instance — let VLC pick the audio output automatically
vlc_instance = vlc.Instance()

# GPIO button
stop_button = Button(GPIO_STOP_PIN)

# -----------------------------
# FADE HELPER
# -----------------------------
def _set_video_level(player, frac):
    """Fade brightness, contrast, saturation and volume together (0.0 = black/silent, 1.0 = normal)."""
    player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness,  frac)
    player.video_set_adjust_float(vlc.VideoAdjustOption.Contrast,    frac)
    player.video_set_adjust_float(vlc.VideoAdjustOption.Saturation,  frac)
    player.audio_set_volume(int(frac * 100))

# -----------------------------
# VIDEO CONTROL
# -----------------------------
def play_video(filename):
    """Stop any current video then play the new one, fading in from black."""
    global player

    path = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(path):
        print(f"File not found: {filename}")
        return

    # Fade out + stop whatever is playing first
    if player and player.is_playing():
        _fade(player, direction="out", block=True)
        player.stop()

    print(f"Playing: {filename}")
    media  = vlc_instance.media_new(path)
    player = vlc_instance.media_player_new()
    player.set_media(media)
    player.set_fullscreen(False)

    # Enable adjust filter at full brightness/volume from the start
    player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
    _set_video_level(player, 1.0)

    player.play()

def stop_video():
    """Immediately kill playback with no fade."""
    global player
    if player:
        player.stop()
        player = None

# -----------------------------
# FADE
# -----------------------------
def _fade(player, direction="in", block=False):
    """Fade brightness/contrast/volume in or out. Set block=True to wait for completion."""
    def _run():
        with fade_lock:
            if not player:
                return
            delay = FADE_DURATION / FADE_STEPS
            rng = range(FADE_STEPS + 1) if direction == "in" else range(FADE_STEPS, -1, -1)
            for i in rng:
                if not player.is_playing() and direction == "out":
                    break   # video already stopped externally
                _set_video_level(player, i / FADE_STEPS)
                time.sleep(delay)

            if direction == "out":
                player.stop()
                print("Fade out complete, video stopped.")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    if block:
        t.join()

# -----------------------------
# GPIO BUTTON
# -----------------------------
def on_stop_button():
    global player
    if player and player.is_playing():
        threading.Thread(target=_fade, kwargs={"player": player, "direction": "out"}, daemon=True).start()
    else:
        print("No video playing.")

stop_button.when_pressed = on_stop_button

# -----------------------------
# MAIN LOOP
# -----------------------------
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Pi Jukebox")

print("Press a LETTER then a NUMBER to play a video")
print(f"Press the GPIO button (GPIO {GPIO_STOP_PIN}) to fade out")
print("Press ESC to quit")

running = True
while running:
    # Clean up player if video has ended naturally
    if player and player.get_state() == vlc.State.Ended:
        player.stop()
        player = None
        print("Video ended.")

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            stop_video()
            break
        elif event.type == pygame.KEYDOWN:
            key_name = pygame.key.name(event.key).upper()
            if key_name == "ESCAPE":
                running = False
                stop_video()
                break
            if key_name in VALID_LETTERS:
                current_letter = key_name
                print(f"Letter selected: {current_letter}")
            elif key_name in VALID_NUMBERS and current_letter:
                filename = f"{current_letter}{key_name}.mp4"
                threading.Thread(target=play_video, args=(filename,), daemon=True).start()
                current_letter = None

    time.sleep(0.1)  # prevent busy-loop

pygame.quit()
