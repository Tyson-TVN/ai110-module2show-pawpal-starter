# PawPal+

PawPal+ is a pet care planner. An owner can register several pets, schedule feedings, walks, medications and appointments for each of them, and see one combined schedule that is sorted, checked for clashes, and kept up to date as recurring tasks are completed. Data is saved to a file, so it is still there the next time the app opens.

The logic lives in `pawpal_system.py` and is used by three things: a terminal demo (`main.py`), a pytest suite (`tests/test_pawpal.py`) and a Streamlit app (`app.py`).

## How the system works

| Class | Responsibility |
|-------|----------------|
| `Task` | One activity: description, time (`HH:MM`), due date, duration, priority, frequency (`once`/`daily`/`weekly`), completion status. `mark_complete()` marks it done. |
| `Pet` | A pet's name, species and its list of tasks. `add_task()` attaches a task and tags it with the pet's name. |
| `Owner` | Holds all of the owner's pets. `get_all_tasks()` returns every pet's tasks in one list. Also saves and loads everything as JSON. |
| `Scheduler` | Works on an `Owner`. It always reads tasks through `owner.get_all_tasks()`, so every feature works across all pets. |

An `Owner` has many `Pet`s, a `Pet` has many `Task`s, and the `Scheduler` reads from the `Owner`. The diagram is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) (the first sketch is in [`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd)).

## Features

- Add multiple pets and any number of tasks per pet
- Tasks sorted by date and time across all pets
- Tasks sorted by priority (high first), then time
- Filtering by pet and by completed/pending status
- Conflict warnings when two pending tasks share the same date and time, even for different pets
- Daily and weekly tasks create their next occurrence automatically when completed
- "Next available slot" finder that uses task durations to find free time
- Pets and tasks saved to `data.json` and reloaded on the next run
- Color and emoji formatted terminal output
- Streamlit UI with warnings, tables, a "mark complete" button and a free-slot finder

## Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` | Sorts with `sorted()` and a lambda key. `HH:MM` strings sort correctly as text because `Task` only accepts zero-padded times. |
| Filtering | `Scheduler.filter_tasks(pet_name, completed)` | Either filter, or both together. Pet name is not case sensitive. |
| Conflict handling | `Scheduler.detect_conflicts()` | Returns a list of warning strings instead of raising. Only pending tasks are checked, and only exact same date + time counts. |
| Recurring tasks | `Scheduler.mark_task_complete(task)` | Daily adds 1 day (`timedelta(days=1)`), weekly adds 7 days. Completing an already completed task does nothing, so it can't create duplicates. |
| Today's plan | `Scheduler.todays_schedule()` | Tasks due today in time order. |
| Free time | `Scheduler.next_available_slot(minutes, date)` | Earliest start between 07:00 and 21:00 where the task fits without overlapping a pending task. See below. |

## Stretch features

### Next available slot (advanced algorithm)

`Scheduler.next_available_slot(duration_minutes, on_date, day_start="07:00", day_end="21:00")` turns each pending task that day into a busy block (start time plus duration), sorts the blocks, and walks through them once, moving a candidate start past any block in the way. It returns the first start where the new task fits, or `None` if the day is full. Back-to-back tasks are allowed (a task that ends at 08:00 does not block one starting at 08:00), and overlapping or nested tasks are handled. Completed tasks and tasks on other days are ignored.

Example from the demo (tasks at 07:30 for 30 min, 08:00 for 45 min and 10 min, and so on):

```
Next available slot
-------------------
   20 min task fits at: 07:00
   60 min task fits at: 08:45
  120 min task fits at: 08:45
```

This is also a simple form of time-blocking: it uses durations to avoid overlaps, which `detect_conflicts()` deliberately does not do (see `reflection.md`, section 2b). In the Streamlit app it is the "Find a free slot" section.

### Priority scheduling

`Scheduler.sort_by_priority()` orders tasks high, medium, low and then by date and time. In the demo output below, "Grooming" (low) moves to the bottom even though it is at 08:00, and the 18:30 "Evening walk" (medium) comes after the high priority tasks. In the Streamlit app choose **By priority** in the *Show* selector.

```
Sorted by priority, then time
-----------------------------
  ⬜ 07:30  🦮 Morning walk     Mochi   30 min  high   daily
  ⬜ 08:00  🍽️ Breakfast        Luna    10 min  high   daily
  ⬜ 12:00  💊 Flea medication  Luna     5 min  high   weekly
  ⬜ 18:30  🦮 Evening walk     Mochi   30 min  medium daily
  ⬜ 08:00  ✂️ Grooming         Mochi   45 min  low    once
```

### Data persistence

Pets and tasks are saved as JSON and loaded again on the next run.

1. `Task`, `Pet` and `Owner` each have `to_dict()` and `from_dict()`. Dates are stored as ISO strings (`2026-10-21`).
2. `Owner.save_to_json(path)` writes the whole owner, with pets and tasks nested inside, to a file.
3. `Owner.load_from_json(path)` reads it back and rebuilds the objects.
4. `app.py` tries to load `data.json` when the app starts (if it is missing or unreadable it starts with an empty owner), and saves after adding a pet, adding a task, completing a task and changing the owner name.
5. `main.py` saves to a temporary file and reloads it to show the data comes back identical.

Files changed: `pawpal_system.py` (the methods above), `app.py` (load and save calls), `main.py` (demo), `tests/test_pawpal.py` (round-trip test), `.gitignore` (so `data.json` is not committed).

### Output formatting

Added to `main.py`, with no extra libraries:

- `color(text, name)` wraps text in ANSI color codes: red for high priority, yellow for medium and warnings, green for low priority and OK messages. Colors only turn on in a real terminal and are off when output is piped to a file or when the `NO_COLOR` variable is set.
- `task_emoji(description)` picks an icon from keywords in the task name (🦮 walks, 🍽️ meals, 💊 medicine, ✂️ grooming, 🏥 vet, 🎾 play, 🐾 anything else).
- `format_task(task)` builds each line, with ✅ or ⬜ for the completion status.
- Conflict warnings print with a ⚠️ icon in yellow.

The sample output below was captured to a file, so it shows the emoji but not the colors.

### AI process documents

`ai_interactions.md` has the agent workflow notes and a Haiku versus Sonnet comparison for the slot finder.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Running it

```bash
python main.py            # terminal demo
streamlit run app.py      # web app
python -m pytest          # tests
```

## Sample Output

Output of `python main.py`:

```
PawPal+ demo for Jordan: 2 pets, 5 tasks

Today's Schedule (sorted by time)
---------------------------------
  ⬜ 07:30  🦮 Morning walk     Mochi   30 min  high   daily
  ⬜ 08:00  ✂️ Grooming         Mochi   45 min  low    once
  ⬜ 08:00  🍽️ Breakfast        Luna    10 min  high   daily
  ⬜ 12:00  💊 Flea medication  Luna     5 min  high   weekly
  ⬜ 18:30  🦮 Evening walk     Mochi   30 min  medium daily

Sorted by priority, then time
-----------------------------
  ⬜ 07:30  🦮 Morning walk     Mochi   30 min  high   daily
  ⬜ 08:00  🍽️ Breakfast        Luna    10 min  high   daily
  ⬜ 12:00  💊 Flea medication  Luna     5 min  high   weekly
  ⬜ 18:30  🦮 Evening walk     Mochi   30 min  medium daily
  ⬜ 08:00  ✂️ Grooming         Mochi   45 min  low    once

Filter: Luna's tasks
--------------------
  ⬜ 08:00  🍽️ Breakfast        Luna    10 min  high   daily
  ⬜ 12:00  💊 Flea medication  Luna     5 min  high   weekly

Conflict check
--------------
  ⚠️  Conflict on 2026-10-21 at 08:00: Grooming (Mochi), Breakfast (Luna)

Next available slot
-------------------
   20 min task fits at: 07:00
   60 min task fits at: 08:45
  120 min task fits at: 08:45

Completed 'Morning walk' -> next one created for 2026-10-22

Filter: completed tasks
-----------------------
  ✅ 07:30  🦮 Morning walk     Mochi   30 min  high   daily

Filter: Mochi's pending tasks
-----------------------------
  ⬜ 18:30  🦮 Evening walk     Mochi   30 min  medium daily
  ⬜ 08:00  ✂️ Grooming         Mochi   45 min  low    once
  ⬜ 07:30  🦮 Morning walk     Mochi   30 min  high   daily

Persistence
-----------
  Saved and reloaded: 2 pets, 6 tasks, identical data: True
```

The dates in the output are whatever day you run the script.

## Demo Walkthrough

1. **Add a pet.** Type a name, pick a species and press *Add pet*. Repeat for each pet. A pet is a `Pet` object stored on the `Owner` kept in `st.session_state`, and it is also saved to `data.json`.
2. **Schedule a task.** Choose the pet, describe the task, pick a date, time, duration, priority and whether it repeats, then press *Add task*.
3. **Read the schedule.** The *Schedule* section shows a table for Today, All tasks, or By priority. The *Pet* and *Status* selectors filter it.
4. **See conflicts.** If two pending tasks share a date and time, a yellow warning names both tasks and pets. With no clashes you see a green "No scheduling conflicts" message.
5. **Complete a task.** Pick a task under *Mark a task complete* and press the button. A daily or weekly task immediately gets a new copy on its next due date.
6. **Find free time.** In *Find a free slot*, enter a task length and a day, and the app tells you the earliest time it fits.
7. **Close and reopen.** Your pets and tasks are still there.

Scheduler behaviors you can see: sorting by time and priority, filtering by pet and status, conflict warnings across pets, recurrence, and free-slot search.

## Testing PawPal+

```bash
python -m pytest
```

The 27 tests cover:

- Task completion and adding a task to a pet
- Sorting by time across pets and sorting by priority
- Filtering by pet name and by status
- Daily and weekly recurrence, no recurrence for one-time tasks, and no duplicate when a task is completed twice
- Conflict detection across pets, no false conflicts, and completed tasks being ignored
- Next available slot: empty day, skipping a busy task, using a gap (including an exact fit), back-to-back and nested tasks, ignoring completed and other-day tasks, a full day, and a bad duration
- Saving and loading JSON (a full round trip, and a missing file)
- Edge cases: a pet or owner with no tasks, an invalid priority, and malformed times (`9:00`, `25:99`, empty)

```
============================= test session starts =============================
platform win32 -- Python 3.12.3, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Dev\ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 27 items

tests\test_pawpal.py ...........................                         [100%]

============================= 27 passed in 0.11s ==============================
```

**Confidence level: ★★★★☆ (4/5).** The scheduling logic is covered by passing tests and the UI flow was exercised end to end, including a restart that reloads saved data. The missing star is for time zones, tasks that cross midnight, and the fact that conflict detection still only matches exact start times.

## Project files

- `pawpal_system.py`: `Task`, `Pet`, `Owner`, `Scheduler`
- `main.py`: terminal demo
- `app.py`: Streamlit UI
- `tests/test_pawpal.py`: pytest suite
- `diagrams/`: Mermaid UML (`uml_draft.mmd`, `uml_final.mmd`, `uml.mmd`)
- `reflection.md`: design and process reflection
- `ai_interactions.md`: agent workflow and model comparison
