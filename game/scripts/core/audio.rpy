################################################################################
### UI SOUND EFFECTS
################################################################################
# One-shot UI sounds live in game/audio/sfx/ (procedurally generated, quiet by
# design). The button click is wired globally through the button style; every
# other cue goes through play_ui_sound(), which degrades to silence if a file
# is missing instead of erroring.
#
# Cues:
#   ui_click   - any button activation (global style)
#   day_chime  - day transition (main_flow: label next_day)
#   coin       - reserved for shop/economy hooks
#   notify     - reserved for notification hooks
#
# Channel routing (audit note): BGM is on the "music" channel; per-event music
# is on the "sound" channel (main_flow). play_ui_sound() uses renpy.play(),
# whose default channel is "audio", keeping the day chime independent of music.
# The button click (style activate_sound) is a 60ms, peak-0.15, pop-free clip
# (fade-in + near-zero tail, verified) so rapid overlapping clicks neither pop
# nor clip.

init python:
    def play_ui_sound(name):
        """Play a one-shot UI sound from audio/sfx/, silently skipping missing files."""
        path = "audio/sfx/%s.wav" % name
        try:
            if renpy.loadable(path):
                renpy.play(path)
        except Exception as e:
            renpy.log(f"AUDIO: could not play {path}: {e}")

# Late offset so this wins over the default style definitions.
init offset = 5

style button:
    activate_sound "audio/sfx/ui_click.wav"
