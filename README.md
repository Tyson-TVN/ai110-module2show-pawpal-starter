# PawPal+

PawPal+ is a pet care planner. An owner can register several pets, schedule feedings, walks, medications and appointments for each of them, and see one combined schedule that is sorted, checked for clashes, and kept up to date as recurring tasks are completed.

The logic lives in `pawpal_system.py` and is used by three things: a terminal demo (`main.py`), a pytest suite (`tests/test_pawpal.py`) and a Streamlit app (`app.py`).

## How the system works

| Class | Responsibility |
|-------|----------------|
| `Task` | One activity: description, time (`HH:MM`), due date, duration, priority, frequency (`once`/`daily`/`weekly`), completion status. `mark_complete()` marks it done. |
| `Pet` | A pet's name, species and its list of tasks. `add_task()` attaches a task and tags it with the pet's name. |
| `Owner` | Holds all of the owner's pets. `get_all_tasks()` returns every pet's tasks in one list. |
| `Scheduler` | Works on an `Owner`. It always reads tasks through `owner.get_all_tasks()`, so every feature works across all pets. |

An `Owner` has many `Pet`s, a `Pet` has many `Task`s, and the `Scheduler` reads from the `Owner`. The diagram is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) (the first sketch is in [`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd)).

## Features

- Add multiple pets and any number of tasks per pet
- Tasks sorted by date and time across all pets
- Tasks sorted by priority (high first), then time
- Filtering by pet and by completed/pending status
- Conflict warnings when two pending tasks share the same date and time, even for different pets
- Daily and weekly tasks create their next occurrence automatically when completed
- Streamlit UI with warnings, tables and a "mark complete" button

## Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` | Sorts with `sorted()` and a lambda key. `HH:MM` strings sort correctly as text because they are zero-padded. |
| Filtering | `Scheduler.filter_tasks(pet_name, completed)` | Either filter, or both together. Pet name is not case sensitive. |
| Conflict handling | `Scheduler.detect_conflicts()` | Returns a list of warning strings instead of raising. Only pending tasks are checked, and only exact same date + time counts. |
| Recurring tasks | `Scheduler.mark_task_complete(task)` | Daily adds 1 day (`timedelta(days=1)`), weekly adds 7 days. Completing an already completed task does nothing, so it can't create duplicates. |
| Today's plan | `Scheduler.todays_schedule()` | Tasks due today in time order. |

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
  [ ] 07:30  Morning walk       Mochi     30 min  high   daily
  [ ] 08:00  Grooming           Mochi     45 min  low    once
  [ ] 08:00  Breakfast          Luna      10 min  high   daily
  [ ] 12:00  Flea medication    Luna       5 min  high   weekly
  [ ] 18:30  Evening walk       Mochi     30 min  medium daily

Sorted by priority, then time
-----------------------------
  [ ] 07:30  Morning walk       Mochi     30 min  high   daily
  [ ] 08:00  Breakfast          Luna      10 min  high   daily
  [ ] 12:00  Flea medication    Luna       5 min  high   weekly
  [ ] 18:30  Evening walk       Mochi     30 min  medium daily
  [ ] 08:00  Grooming           Mochi     45 min  low    once

Filter: Luna's tasks
--------------------
  [ ] 08:00  Breakfast          Luna      10 min  high   daily
  [ ] 12:00  Flea medication    Luna       5 min  high   weekly

Conflict check
--------------
  WARNING: Conflict on 2026-10-21 at 08:00: Grooming (Mochi), Breakfast (Luna)

Completed 'Morning walk' -> next one created for 2026-10-22

Filter: completed tasks
-----------------------
  [x] 07:30  Morning walk       Mochi     30 min  high   daily

Filter: Mochi's pending tasks
-----------------------------
  [ ] 18:30  Evening walk       Mochi     30 min  medium daily
  [ ] 08:00  Grooming           Mochi     45 min  low    once
  [ ] 07:30  Morning walk       Mochi     30 min  high   daily
```

The dates in the output are whatever day you run the script.

## Demo Walkthrough

1. **Add a pet.** Type a name, pick a species and press *Add pet*. Repeat for each pet. A pet is a `Pet` object stored on the `Owner` kept in `st.session_state`, so it stays while you use the app.
2. **Schedule a task.** Choose the pet, describe the task, pick a date, time, duration, priority and whether it repeats, then press *Add task*.
3. **Read the schedule.** The *Schedule* section shows a table for Today, All tasks, or By priority. The *Pet* and *Status* selectors filter it.
4. **See conflicts.** If two pending tasks share a date and time, a yellow warning names both tasks and pets. With no clashes you see a green "No scheduling conflicts" message.
5. **Complete a task.** Pick a task under *Mark a task complete* and press the button. A daily or weekly task immediately gets a new copy on its next due date.

Scheduler behaviors you can see: sorting by time and priority, filtering by pet and status, conflict warnings across pets, and recurrence.

## Testing PawPal+

```bash
python -m pytest
```

The 14 tests cover:

- Task completion and adding a task to a pet
- Sorting by time across pets and sorting by priority
- Filtering by pet name and by status
- Daily and weekly recurrence, no recurrence for one-time tasks, and no duplicate when a task is completed twice
- Conflict detection across pets, no false conflicts, and completed tasks being ignored
- Edge cases: a pet or owner with no tasks, and an invalid priority

```
============================= test session starts =============================
platform win32 -- Python 3.12.3, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Dev\ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 14 items

tests\test_pawpal.py ..............                                      [100%]

============================= 14 passed in 1.13s ==============================
```

**Confidence level: ★★★★☆ (4/5).** The scheduling logic is covered by passing tests and the UI flow was exercised end to end. The missing star is for overlapping durations, time zones and bad `HH:MM` input, which are not handled or tested.

## Project files

- `pawpal_system.py`: `Task`, `Pet`, `Owner`, `Scheduler`
- `main.py`: terminal demo
- `app.py`: Streamlit UI
- `tests/test_pawpal.py`: pytest suite
- `diagrams/`: Mermaid UML (`uml_draft.mmd`, `uml_final.mmd`, `uml.mmd`)
- `reflection.md`: design and process reflection
