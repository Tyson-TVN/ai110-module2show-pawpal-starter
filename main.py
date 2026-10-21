from pawpal_system import Owner, Pet, Task, Scheduler


def show(title, tasks):
    print(f"\n{title}")
    print("-" * len(title))
    if not tasks:
        print("  (nothing)")
    for t in tasks:
        status = "x" if t.completed else " "
        print(f"  [{status}] {t.time}  {t.description:<18} {t.pet_name:<8} "
              f"{t.duration_minutes:>3} min  {t.priority:<6} {t.frequency}")


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

    print("\nConflict check")
    print("--------------")
    for warning in scheduler.detect_conflicts() or ["No conflicts."]:
        print(f"  WARNING: {warning}")

    morning_walk = scheduler.sort_by_time()[0]
    next_task = scheduler.mark_task_complete(morning_walk)
    print(f"\nCompleted '{morning_walk.description}' -> next one created for {next_task.due_date}")
    show("Filter: completed tasks", scheduler.filter_tasks(completed=True))
    show("Filter: Mochi's pending tasks", scheduler.filter_tasks(pet_name="Mochi", completed=False))


if __name__ == "__main__":
    main()
