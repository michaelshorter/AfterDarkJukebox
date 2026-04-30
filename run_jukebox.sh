#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=/home/jukebox/.Xauthority

# Hide the cursor at OS level so VLC can't bring it back
unclutter -idle 0 -root &

# Wait for USB drive to mount
echo "Waiting for USB drive..."
while [ ! -d "/media/jukebox/JUKEBOX/videos" ]; do
    sleep 1
done
echo "USB drive found, starting jukebox..."

source /home/jukebox/jukebox-env/bin/activate
python /home/jukebox/jukebox.py
