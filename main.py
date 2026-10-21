import os
import sys
import tempfile
from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task

# Windows terminals need this for emoji, and for ANSI colors in older consoles.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.system("")

USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ
COLORS = {"high": "31", "medium": "33", "low": "32", "warn": "33;1", "ok": "32;1", "bold": "1"}
EMOJI_BY_WORD = [
    (("walk",), "🦮"),
    (("breakfast", "dinner", "feed", "meal"), "🍽️"),
    (("med", "pill", "flea"), "💊"),
    (("groom", "bath", "brush"), "✂️"),
    (("vet", "checkup"), "🏥"),
    (("play", "toy"), "🎾"),
]


def color(text, name):
    """Wrap text in an ANSI color code when writing to a real terminal."""
    if not USE_COLOR:
        return text
    return f"\033[{COLORS[name]}m{text}\033[0m"


def task_emoji(description):
    """Pick an emoji from keywords in the task description."""
    lowered = description.lower()
    for words, emoji in EMOJI_BY_WORD:
        if any(w in lowered for w in words):
            return emoji
    return "🐾"


def format_task(t):
    """One readable line for a task."""
    status = "✅" if t.completed else "⬜"
    priority = color(f"{t.priority:<6}", t.priority)
    return (f"  {status} {t.time}  {task_emoji(t.description)} {t.description:<16} "
            f"{t.pet_name:<6} {t.duration_minutes:>3} min  {priority} {t.frequency}")


def show(title, tasks):
    print(f"\n{color(title, 'bold')}")
    print("-" * len(title))
    if not tasks:
        print("  (nothing)")
    for t in tasks:
        print(format_task(t))


def main():
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added out of order on purpose.
    mochi.add_task(Task("Evening walk", "18:30", duration_minutes=30, priority="medium", frequency="daily"))
    mochi.add_task(Task("Morning walk", "07:30", duration_minutes=30, priority="high", frequency="daily"))
    luna.add_task(Task("Breakfast", "08:00", duration_minutes=10, priority="high", frequency="daily"))
    luna.add_task(Task("Flea medication", "12:00", duration_minutes=5, priority="high", frequency="weekly"))
    mochi.add_task(Task("Grooming", "08:00", duration_minutes=45, priority="low"))  # clashes with Breakfast

    scheduler = Scheduler(owner)

    print(f"PawPal+ demo for {owner.name}: {len(owner.pets)} pets, "
          f"{len(owner.get_all_tasks())} tasks")

    show("Today's Schedule (sorted by time)", scheduler.todays_schedule())
    show("Sorted by priority, then time", scheduler.sort_by_priority())
    show("Filter: Luna's tasks", scheduler.filter_tasks(pet_name="Luna"))

    print(f"\n{color('Conflict check', 'bold')}")
    print("--------------")
    conflicts = scheduler.detect_conflicts()
    for warning in conflicts:
        print(color(f"  ⚠️  {warning}", "warn"))
    if not conflicts:
        print(color("  ✅ No conflicts.", "ok"))

    print(f"\n{color('Next available slot', 'bold')}")
    print("-------------------")
    today = date.today()
    for minutes in (20, 60, 120):
        slot = scheduler.next_available_slot(minutes, today)
        print(f"  {minutes:>3} min task fits at: {slot or 'no free slot today'}")

    morning_walk = scheduler.sort_by_time()[0]
    next_task = scheduler.mark_task_complete(morning_walk)
    print(f"\nCompleted '{morning_walk.description}' -> next one created for {next_task.due_date}")
    show("Filter: completed tasks", scheduler.filter_tasks(completed=True))
    show("Filter: Mochi's pending tasks", Scheduler(owner).filter_tasks(pet_name="Mochi", completed=False))

    # Save and reload to show the data survives between runs.
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "data.json")
        owner.save_to_json(path)
        restored = Owner.load_from_json(path)
    print(f"\n{color('Persistence', 'bold')}")
    print("-----------")
    print(f"  Saved and reloaded: {len(restored.pets)} pets, "
          f"{len(restored.get_all_tasks())} tasks, identical data: {restored == owner}")


if __name__ == "__main__":
    main()
