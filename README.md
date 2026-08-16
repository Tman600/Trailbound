# Trailbound

A procedurally generated survival-journey game for your terminal, in the
spirit of *The Oregon Trail* -- but with five different genres, none of
which play out the same way twice, and every run genuinely ends.

Runs anywhere Python does: Windows Terminal, cmd.exe, PowerShell, macOS
Terminal, Linux terminals.

## Credits & license

Created by TMan600, with the
assistance of Claude (Anthropic). Licensed under the terms in `LICENSE`
(MIT-based, open source) -- forks and derivative works are welcome, but
must keep a visible credit to both the original creator and Anthropic. See
`LICENSE` for the exact wording to include.

## Genres

- **Overland Trail** -- a wagon party crossing the 19th-century frontier
- **Deep Space Convoy** -- a colony ship crossing the dark between stars
- **The Long Convoy** -- a rig of survivors crossing a post-collapse wasteland
- **The Kingsroad Caravan** -- a caravan crossing a fading fantasy kingdom
- **Voyage of the Restless** -- a ship crossing open ocean, age-of-sail style

Each genre reskins the same simulation with its own resources, hazards,
landmark names, and party roles, procedurally generated fresh each run
(distance, names, events, and outcome all vary).

Every run ends in one of five tiers per genre: **triumphant**, **success**,
**bittersweet**, **tragic**, or a rare **secret** ending if the party
stumbles onto something hidden along the way.

## Freeplay

A sixth mode, solo and fully free-form -- no fixed setting, no money/food/
vehicle economy. You describe how it opens (or say "surprise me") and
optionally set a goal, then every turn is just: type anything, and the
model narrates what happens, judged for plausibility. All you're tracking
is **Health** and a free-form **Inventory** -- items can carry their own
status detail (`gun (6 rounds)`, `torch (half burned)`) that updates as
you use them, rather than needing separate hardcoded stats for ammo vs.
fuel vs. anything else.

Freeplay has its own distinct look: green text, the screen clears on every
beat, and stats are hidden until you ask for them -- tap **Tab** any time
to check your health/inventory without needing to press Enter first (this
uses the standard library only, no extra dependency: `msvcrt` on Windows,
`termios`/`tty` on Mac/Linux). It always ends eventually -- either health
runs out, or you type `end` (or "end story", "quit", etc.) any time to get
a proper closing narration for wherever you've gotten to.

**Continuity:** every action sent to the model includes the last several
turns verbatim, plus a compact rolling summary of everything earlier that
gets refreshed automatically every few turns -- so a name, item, or plot
thread from turn 3 is still known at turn 50, without re-sending the
entire history every time (which would keep growing and slow things down).
The five structured genres get the same treatment on a smaller scale:
free-text actions there are told the party's recent events too, not just
the immediate situation, so the model isn't judging each action in a
vacuum.

**Freeplay only appears in the menu when local AI is detected** (see
below) -- there's no scripted content to fall back on for genuinely
open-ended input, so it's hidden rather than offered broken.

One current limitation: Freeplay sessions aren't autosaved/resumable the
way the five structured genres are -- if you quit mid-story, that run is
gone. Worth adding later if it'd be useful.

## Setup

Requires Python 3.9+.

```bash
pip install -r requirements.txt
python main.py
```

**On macOS** (and some Linux distros), there's often no plain `python`/`pip`
command -- use `python3`/`pip3` instead:

```bash
pip3 install -r requirements.txt
python3 main.py
```

If you don't have Python 3 at all on macOS: `brew install python3` (via
[Homebrew](https://brew.sh)), or grab the installer from
[python.org](https://www.python.org/downloads/macos/).

That's it -- the game is fully playable with its own built-in story text.
Want AI-enhanced narration and free-text actions too? Run `python3
setup_ai.py` first (see below) -- entirely optional.

## Optional: local AI narration & free-text actions

If you'd like richer, less repetitive narration -- and the ability to type
your own actions instead of picking from a menu -- run a local model
server before starting Trailbound. Two are supported, auto-detected in
this order:

### Option 1: Ollama

The easy way -- installs Ollama if needed and pulls the default model
(`gemma3:4b`, ~3.3GB) automatically:

```bash
python setup_ai.py
python main.py
```

Or set it up yourself with any model you prefer:

```bash
ollama pull gemma3:4b     # the default Trailbound looks for, or any small model you prefer
ollama serve              # usually starts automatically after install
python main.py
```

Trailbound checks `http://localhost:11434`, and prefers `gemma3:4b` by
name if it's installed alongside other models.

### Option 2: llama.cpp

llama.cpp ships two different tools, and this trips people up: `llama-cli`
(or the older `main`) is an interactive terminal chat program with **no
network API at all** -- Trailbound has no way to detect or talk to it, no
matter how it's running. `llama-server` is the one that exposes an HTTP
API, and that's the one Trailbound looks for:

```bash
./llama-server -m /path/to/model.gguf --port 8080
```

(On Windows it's `llama-server.exe`; if you built from source it'll be
under `build/bin/`.) Trailbound checks `http://localhost:8080` for it.

### Either way

Once a server is running, start (or restart) Trailbound and you'll see
`Local AI detected` at the top, along with which backend and model it
found. Two things change:

- The opening, landmarks, and ending get freshly generated narration
  instead of the built-in story text.
- At every story moment (an encounter, a breakdown, a landmark, a hard
  crossing...) you can type literally anything -- *"I try to talk our way
  past them"*, *"give the last of our water to the sick one"*, *"push the
  wagon myself"* -- and the model narrates what happens and adjusts your
  resources and party accordingly. Press Enter instead of typing anything
  to skip straight to the quick-choice menu if you'd rather just pick an
  option.

If no local model is found, you'll see a note that it's using built-in
story text and quick-choice menus instead -- gameplay is identical either
way, just without free-text input. Nothing is sent anywhere outside your
machine, and there's no API key involved. Routine day-to-day flavor text
generation and free-text interpretation both fail safely: if the model
times out or returns something unusable, the game falls back to a neutral
default rather than stalling. Whatever the model proposes for your
resources is also clamped to the same safe ranges the scripted events use,
so no amount of creative prompting can break the game's economy (e.g.
typing "I find a billion gold" will not, in fact, give you a billion
gold).

**Ollama/llama.cpp loads models lazily** -- the model doesn't actually sit
in memory until something asks it to generate, and a cold load of a
multi-GB model can take a while. Trailbound handles this by sending a
tiny throwaway request on startup to force the model to load right away
(you'll see "Waking up the local model..." for a moment) rather than
having that delay land in the middle of your first real action. If you'd
rather skip the wait, running `ollama run <model>` or sending it one
message yourself before launching Trailbound has the same warming effect.

**If nothing is being detected at all, or free-text actions always come
back as a generic "it plays out without much fanfare" response,** run the
game with debug logging on to see exactly why:

```bash
TRAILBOUND_DEBUG=1 python3 main.py       # macOS/Linux (use python3 if plain python isn't aliased)
set TRAILBOUND_DEBUG=1 && python main.py # Windows cmd
$env:TRAILBOUND_DEBUG=1; python main.py  # Windows PowerShell
```

This prints the real error (connection refused, timeout, HTTP error, or
the model's raw unparseable output) to the terminal instead of failing
silently -- e.g. "connection refused" on both ports usually means no
server is actually running (check you started `llama-server`, not
`llama-cli`), while a slow response that eventually times out points to
the model just being too large/slow for `TIMEOUT_ACTION` (60s by default,
`TIMEOUT_WARMUP` is a more generous 120s for that first cold-start
request; edit the constants at the top of `engine/ai.py` if you need
more).

## Playing

Each day you choose to continue, adjust **pace** (grueling/steady/cautious
-- faster is riskier, slower is safer but takes longer) or **rations**
(bare/meager/filling -- more food per day means better health but faster
depletion of your stores), check the log, or save and quit. Landmarks and
river/canyon/reef-style crossings offer their own choices along the way --
or, with local AI running, your own typed actions. Progress autosaves
after each day, so you can quit anytime and pick the same journey back up
next time you launch the game.

## Project layout

```
main.py              entry point / menus / day loop / mode routing
setup_ai.py           optional: installs Ollama (if needed) and pulls the
                       default model (gemma3:4b); `python setup_ai.py`
engine/state.py       Character & GameState dataclasses (structured genres)
engine/genres.py      all genre content (names, flavor text, endings) -- add a genre here, no engine changes needed
engine/events.py      the simulation: daily advance + all event/landmark/crossing logic
engine/endings.py     ending-tier scoring + AI-or-fallback closing narration
engine/freeplay.py     Freeplay mode: solo state, setup flow, turn loop, ending
engine/ai.py          local AI backend detection (Ollama + llama.cpp server) + generation, always with a safe fallback
engine/ui.py          all terminal rendering (rich-based), plus Freeplay's green/clear-screen/single-keypress UI
engine/namegen.py     procedural landmark/destination/party name generation
engine/save.py        JSON autosave/resume (structured genres only, see Freeplay note above)
test_smoke.py         optional: drives the engine directly across hundreds of
                       seeded runs (all genres) to confirm nothing crashes and
                       every run reaches a valid ending; `python test_smoke.py`
test_freetext.py      optional: exercises the free-text action pathway
                       (clamping, malformed AI responses, invalid targets)
                       without needing a live model server; `python test_freetext.py`
test_ai_backends.py   optional: spins up mock Ollama/llama.cpp HTTP servers to
                       test real detection + generation code paths (note: binds
                       to ports 11434/8080, so stop any real server first);
                       `python test_ai_backends.py`
test_freeplay_state.py        optional: Freeplay inventory/health mutation and clamping logic
test_freeplay_ai.py           optional: interpret_freeplay_action sanitization against a mock server
test_freeplay_integration.py  optional: a full scripted Freeplay session end to end
test_freeplay_summary.py      optional: the rolling-summary continuity mechanism,
                                including a live session that crosses the trigger threshold
```

Adding a sixth *structured* genre is just adding one more `Genre(...)`
entry to `engine/genres.py` -- the simulation, UI, and AI narration all
pick it up automatically. Freeplay is a separate, simpler code path
(`engine/freeplay.py`) since it doesn't share the money/food/vehicle
economy the structured genres use.
