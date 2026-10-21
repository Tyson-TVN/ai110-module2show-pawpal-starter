# AI Interactions Log

---

## Agent Workflow (SF7)

I used Claude Code in agent mode inside VS Code to add the stretch features after the core project was submitted.

**What task did you give the agent?**

Add the stretch features: a "next available slot" algorithm, saving and loading pets and tasks as JSON, nicer terminal output, priority scheduling examples in the README, and a model comparison. I also asked it to check how the repo renders on GitHub.

**What did the agent do?**

Files modified:

- `pawpal_system.py`: added `Scheduler.next_available_slot()`, and `to_dict()` / `from_dict()` on `Task`, `Pet` and `Owner`, plus `Owner.save_to_json()` and `Owner.load_from_json()`.
- `main.py`: rewrote the output with emoji status icons, task-type emoji and ANSI colors, and added next-slot and save/reload demos.
- `app.py`: loads `data.json` on start, saves after every change, and has a "Find a free slot" section.
- `tests/test_pawpal.py`: added 9 tests (27 in total) for the slot finder and for JSON round-trips.
- `.gitignore`: added `data.json` so personal data is not committed.
- `README.md`, `reflection.md` and this file: documentation.

Other steps: it ran two sub-agents on the same prompt for the model comparison below, ran the tests and the demo, drove the Streamlit app with Streamlit's test runner to check that data survives a restart, and opened the GitHub repo in the built-in browser to check the README and the UML diagram render.

**What did you have to verify or fix manually?**

- The agent's first test for the "gap between tasks" case was wrong. A 90-minute task does fit exactly into the 07:30 to 09:00 gap, so the code was right and the test expectation was fixed.
- The disk on my computer filled up halfway through. The agent stopped when writes started failing, checked that the source files were not damaged, and waited while I freed space.
- With almost no memory left, the app check crashed with an OpenBLAS allocation error. Running it again with `OPENBLAS_NUM_THREADS=1` worked.
- Earlier, during the core project, I reviewed my own code with separate AI chats. That review led to validating the `HH:MM` time format in `Task`.

---

## Prompt Comparison (SF11)

Same prompt, two models, run as separate sub-agents. Neither was allowed to edit files; each had to return only the method.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | Claude Haiku (sub-agent) | Claude Sonnet (sub-agent) |
| **Prompt** | "Design a new Scheduler method `next_available_slot(self, duration_minutes, on_date, day_start='07:00', day_end='21:00')` that returns the earliest HH:MM start on that date where a task of that length fits without overlapping any pending task, using each task's time and duration. Return None if nothing fits. Reply with only the code and a 2-sentence note on edge cases." | Identical prompt |
| **Response summary** | Builds a set of candidate start times (the window start plus the end of every busy block), then tries them in order and returns the first one that does not overlap any block. | Sorts the busy blocks, then makes one pass, moving a "candidate" start past each block that is in the way, and stops at the first big enough gap. |
| **What was useful** | Easy to reason about ("try each possible start, check for overlap"). Parses times with `strptime`, so a malformed time raises a clear error. | Shorter loop, no repeated overlap checks. Overlapping and nested tasks are handled naturally by taking the larger end time. Ignores a negative duration instead of letting it break the math. |
| **Problems noticed** | Re-checks every busy block for every candidate, so the work grows quickly with the number of tasks. Does not guard against a negative task duration. | Parses times by splitting on `:`, so a bad string would give a confusing error (in this project `Task` already validates times, so it can't happen). |
| **Decision** | Not used. | Used. |

I ran both versions against the same 7 slot tests (empty day, busy start, gap between tasks, back-to-back and nested tasks, completed and other-day tasks, a full day, and a bad duration). Both passed all 7, so correctness did not decide it.

**Which approach did you use in your final implementation and why?**

Option B (Sonnet's version). Both were correct on every test, so I chose the one that does a single pass over the day, since that is simpler to read and keeps the cost small as the number of tasks grows.
