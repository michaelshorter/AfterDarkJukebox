import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import vlc
import pygame
import threading
import time
from gpiozero import Button

# -----------------------------
# CONFIG
# -----------------------------
VIDEO_DIR     = "/media/jukebox/JUKEBOX/videos"
VALID_LETTERS = set("ABCDEFGHJKLMNQRSTUV")
VALID_NUMBERS = set("0123456789")
BEAM_PIN      = 18
GPIO_STOP_PIN = 17       # kept in case you want to re-enable the button
FADE_DURATION = 3        # seconds
FADE_STEPS    = 100
WINDOW_WIDTH  = 1280
WINDOW_HEIGHT = 720
IDLE_IMAGE    = "/media/jukebox/JUKEBOX/idle.png"
# -----------------------------

current_letter  = None
player          = None
fade_lock       = threading.Lock()
# Flag set by background threads to request idle screen from main loop
show_idle_flag  = threading.Event()

vlc_instance = vlc.Instance("--quiet", "--codec=avcodec,none", "--mouse-hide-timeout=0")
beam_sensor  = Button(BEAM_PIN, pull_up=True)

# -----------------------------
# PYGAME SETUP
# -----------------------------
pygame.init()
pygame.mouse.set_visible(False)
os.environ['SDL_VIDEO_CENTERED'] = '1'
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Pi Jukebox")

if os.path.exists(IDLE_IMAGE):
    idle_surface = pygame.transform.scale(
        pygame.image.load(IDLE_IMAGE), (WINDOW_WIDTH, WINDOW_HEIGHT)
    )
else:
    idle_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    idle_surface.fill((0, 0, 0))

def show_idle():
    """Call only from the main thread."""
    screen.blit(idle_surface, (0, 0))
    pygame.display.flip()

show_idle()

# -----------------------------
# FADE HELPER
# -----------------------------
def _set_video_level(p, frac):
    p.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, frac)
    p.video_set_adjust_float(vlc.VideoAdjustOption.Contrast,   frac)
    p.video_set_adjust_float(vlc.VideoAdjustOption.Saturation, frac)
    p.audio_set_volume(int(frac * 100))

# -----------------------------
# FADE
# -----------------------------
def _fade(p, direction="out", block=False):
    def _run():
        with fade_lock:
            if not p:
                return
            delay = FADE_DURATION / FADE_STEPS
            rng = range(FADE_STEPS, -1, -1) if direction == "out" else range(FADE_STEPS + 1)
            for i in rng:
                if not p.is_playing() and direction == "out":
                    break
                _set_video_level(p, i / FADE_STEPS)
                time.sleep(delay)
            if direction == "out":
                p.stop()
                show_idle_flag.set()
                print("Fade out complete, video stopped.")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    if block:
        t.join()

# -----------------------------
# VIDEO CONTROL
# -----------------------------
def play_video(filename):
    global player

    path = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(path):
        print(f"File not found: {filename}")
        return

    if player and player.is_playing():
        print("Video already playing, selection ignored.")
        return

    print(f"Playing: {filename}")
    media  = vlc_instance.media_new(path)
    player = vlc_instance.media_player_new()
    player.set_media(media)

    wm_info = pygame.display.get_wm_info()
    player.set_xwindow(wm_info["window"])

    player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
    _set_video_level(player, 1.0)
    player.play()

def stop_video():
    global player
    if player:
        player.stop()
        player = None
    show_idle()

# -----------------------------
# IR BEAM
# -----------------------------
def on_beam_broken():
    global player
    if player and player.is_playing():
        p = player
        threading.Thread(target=_fade, kwargs={"p": p, "direction": "out"}, daemon=True).start()
    else:
        print("No video playing.")

beam_sensor.when_pressed = on_beam_broken

# -----------------------------
# MAIN LOOP
# -----------------------------
print("Press a LETTER then a NUMBER to play a video")
print(f"Insert a coin (IR beam on GPIO {BEAM_PIN}) to fade out")
print("Press ESC to quit")

running = True
while running:
    # Keep cursor hidden (VLC can reset it)
    pygame.mouse.set_visible(False)

    # Show idle screen if requested by a background thread
    if show_idle_flag.is_set():
        show_idle()
        show_idle_flag.clear()

    # Clean up player if video ended naturally
    if player and player.get_state() == vlc.State.Ended:
        player.stop()
        player = None
        show_idle()
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

    time.sleep(0.1)

pygame.quit()    player.audio_set_volume(int(frac * 100))

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
