# -*- coding: utf-8 -*-
"""Player thread from the lecture materials (first8.py): a Python class that extends java.lang.Thread.

Usage: music_player.py [file.wav] [--info]
`--info` opens the audio stream and prints its format without playing it.
"""
from __future__ import print_function

import sys

from java.io import File
from java.lang import Thread
from javax.sound.sampled import AudioSystem, UnsupportedAudioFileException
import java.io.IOException


class MusicPlayer(Thread):
    def __init__(self, audio_file_path):
        Thread.__init__(self)
        self.audio_file_path = audio_file_path

    def run(self):
        try:
            print("Attempting to play audio...")
            audio_file = File(self.audio_file_path)
            audio_input_stream = AudioSystem.getAudioInputStream(audio_file)
            clip = AudioSystem.getClip()
            clip.open(audio_input_stream)
            print("Audio clip opened, starting playback...")
            clip.start()

            # Keep the thread alive while the music plays
            while clip.isRunning():
                Thread.sleep(100)
            clip.close()
            print("Playback finished.")
        except UnsupportedAudioFileException:
            print("Error: The audio file format is not supported.")
        except java.io.IOException:
            print("Error: An I/O error occurred while trying to access the audio file.")
        except Exception as e:
            print("Error playing audio:", e)


def describe(path):
    stream = AudioSystem.getAudioInputStream(File(path))
    audio_format = stream.getFormat()
    seconds = stream.getFrameLength() / audio_format.getFrameRate()
    print("audio " + File(path).getName() + ": " + str(audio_format.getSampleRate()) + " Hz, "
          + str(audio_format.getChannels()) + " channel(s), " + str(round(seconds, 2)) + " s")
    stream.close()


if __name__ == "__main__":
    music_file_path = [a for a in sys.argv[1:] if not a.startswith("--")][0]
    if "--info" in sys.argv:
        describe(music_file_path)
    else:
        music_player = MusicPlayer(music_file_path)
        music_player.start()

        # Keep the main thread alive for a while
        while music_player.isAlive():
            Thread.sleep(100)
