import time
import python3_midi as midi
from pynput.keyboard import Key, Controller
from tkinter import *
from tkinter import filedialog
from tkinter import ttk

notes_to_keys = {
    0: ("z", False),
    1: ("z", True),
    2: ("x", False),
    3: ("x", True),
    4: ("c", False),
    5: ("v", False),
    6: ("v", True),
    7: ("b", False),
    8: ("b", True),
    9: ("n", False),
    10: ("n", True),
    11: ("m", False)
}
transpose_selection = (
    "0 (key c)",
    "-1 (key c#)",
    "-2 (key d)",
    "-3 (key d#)",
    "-4 (key e)",
    "-5 (key f)",
    "-6 (key f#)",
    "+6 (key f#)",
    "+5 (key g)",
    "+4 (key g#)",
    "+3 (key a)",
    "+2 (key a#)",
    "+1 (key b)"
)

current_pattern = None
track_tickers = None
playing = False
tempo = 120
transpose = 0

last_ticked = 0
keyboard = Controller()

# the actual ui stuff
root = Tk()
root.title("let's lute!")
root.wm_attributes(topmost=True)
root.resizable(width=False, height=False)
root.wm_iconphoto(False, PhotoImage(file="icon.png"))
# hi
transpose_contents = StringVar(value=transpose_selection[0])
entry_contents = StringVar()
playback_button = None
stop_button = None

def run_event(event):
    # its just 3 events i guess
    match type(event):
        case midi.SetTempoEvent:
            vals = [event.data[x] << (16 - (8 * x)) for x in range(3)]
            global tempo
            tempo = float(6e7) / sum(vals)
            print(tempo)
        case midi.NoteOnEvent:
            key = notes_to_keys[(event.get_pitch() + transpose) % 12]
            # This Sucks Lol (not really)
            if key[1]:
                with keyboard.pressed(Key.shift):
                    keyboard.tap(key[0])
            else:
                keyboard.tap(key[0])

def set_playing(value):
    if value and current_pattern is None:
        return
    global playing
    playing = value

    playback_button["text"] = "Pause" if playing else "Play"
    if playing:
        stop_button["state"] = "normal"

def toggle_playing():
    set_playing(not playing)

def stop_pattern():
    if current_pattern is None:
        return

    global track_tickers
    track_tickers = [[0 for i in range(2)] for i in range(len(current_pattern))]
    global playing
    set_playing(False)
    global tempo
    tempo = 120
    stop_button["state"] = "disabled"

def transpose_updated(_, __, ___):
    index = transpose_selection.index(transpose_contents.get())
    global transpose
    transpose = -index if index < 7 else 13 - index
    print(transpose)

def select_midi():
    selected_filename = filedialog.askopenfilename(
        filetypes=[
            ("MIDI files", ".mid .midi")
        ]
    )
    with open(selected_filename, mode="rb") as selected_file:
        global current_pattern
        current_pattern = midi.read_midifile(selected_file)
        entry_contents.set(selected_filename)

    stop_pattern()
    playback_button["state"] = "normal"

ftop = ttk.Frame(root, padding=5)
ftop.grid(column=0, row=0, pady=2, sticky="w")
ttk.Label(ftop, text="Choose a MIDI file to play:").grid(column=0, row=0)
ttk.Entry(ftop, state="readonly", width=40, textvariable=entry_contents).grid(column=1, row=0, padx=5)
ttk.Button(ftop, text="Browse", command=select_midi).grid(column=2, row=0)

fmid = ttk.Frame(root, padding=5)
fmid.grid(column=0, row=1, pady=2, sticky="w")
ttk.Label(fmid, text="Transpose:").grid(column=0, row=0)
ttk.Combobox(fmid, textvariable=transpose_contents, values=transpose_selection, state="readonly", width=30).grid(column=1, row=0, padx=5)
transpose_contents.trace_add("write", transpose_updated)

fbottom = ttk.Frame(root, padding=5)
fbottom.grid(column=0, row=2, sticky="w")
playback_button = ttk.Button(fbottom, text="Play", command=toggle_playing, width=20, padding=5, state="disabled")
playback_button.grid(column=1, row=0, padx=2)
stop_button = ttk.Button(fbottom, text="Stop", command=stop_pattern, state="disabled", width=20, padding=5)
stop_button.grid(column=2, row=0, padx=2)

def update():
    global last_ticked

    if current_pattern is not None and playing and not root.focus_get():
        delta = time.time() - last_ticked
        all_finished = True
        for i, track in enumerate(current_pattern):
            track_ticker = track_tickers[i]
            while track_ticker[0] < len(track) and track[track_ticker[0]].tick <= track_ticker[1]:
                run_event(track[track_ticker[0]])
                track_ticker[1] -= track[track_ticker[0]].tick
                track_ticker[0] += 1

            if track_ticker[0] < len(track):
                all_finished = False
                track_ticker[1] += delta * current_pattern.resolution * (tempo / 60)

        if all_finished:
            stop_pattern()

    last_ticked = time.time()
    root.after(1, func=update)

set_playing(False)

update()
root.mainloop()