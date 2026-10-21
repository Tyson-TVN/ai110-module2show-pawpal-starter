from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


@pytest.fixture
def setup():
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna, Scheduler(owner)


def test_mark_complete_changes_status():
    task = Task("Walk", "07:30")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task("Walk", "07:30"))
    assert len(pet.tasks) == 1
    assert pet.tasks[0].pet_name == "Mochi"


def test_sort_by_time_is_chronological_across_pets(setup):
    owner, mochi, luna, scheduler = setup
    mochi.add_task(Task("Evening walk", "18:30"))
    luna.add_task(Task("Breakfast", "08:00"))
    mochi.add_task(Task("Morning walk", "07:30"))

    times = [t.time for t in scheduler.sort_by_time()]
    assert times == ["07:30", "08:00", "18:30"]


def test_sort_by_priority_puts_high_first(setup):
    owner, mochi, luna, scheduler = setup
    mochi.add_task(Task("Grooming", "07:00", priority="low"))
    luna.add_task(Task("Medication", "09:00", priority="high"))

    assert scheduler.sort_by_priority()[0].description == "Medication"


def test_filter_by_pet_and_status(setup):
    owner, mochi, luna, scheduler = setup
    done = Task("Breakfast", "08:00")
    luna.add_task(done)
    luna.add_task(Task("Play", "17:00"))
    mochi.add_task(Task("Walk", "07:30"))
    done.mark_complete()

    assert len(scheduler.filter_tasks(pet_name="Luna")) == 2
    assert scheduler.filter_tasks(completed=True) == [done]
    assert len(scheduler.filter_tasks(pet_name="luna", completed=False)) == 1


def test_daily_task_creates_next_day_task(setup):
    owner, mochi, luna, scheduler = setup
    task = Task("Walk", "07:30", frequency="daily")
    mochi.add_task(task)

    next_task = scheduler.mark_task_complete(task)

    assert task.completed is True
    assert next_task.due_date == task.due_date + timedelta(days=1)
    assert next_task.completed is False
    assert next_task in mochi.tasks
    assert len(mochi.tasks) == 2


def test_weekly_task_creates_task_seven_days_later(setup):
    owner, mochi, luna, scheduler = setup
    task = Task("Flea medication", "12:00", frequency="weekly")
    luna.add_task(task)

    next_task = scheduler.mark_task_complete(task)

    assert next_task.due_date == date.today() + timedelta(days=7)


def test_one_time_task_does_not_recur(setup):
    owner, mochi, luna, scheduler = setup
    task = Task("Vet visit", "10:00")
    mochi.add_task(task)

    assert scheduler.mark_task_complete(task) is None
    assert len(mochi.tasks) == 1


def test_completing_twice_does_not_duplicate_recurring_task(setup):
    owner, mochi, luna, scheduler = setup
    task = Task("Walk", "07:30", frequency="daily")
    mochi.add_task(task)

    scheduler.mark_task_complete(task)
    scheduler.mark_task_complete(task)

    assert len(mochi.tasks) == 2


def test_conflict_detected_for_same_time_on_different_pets(setup):
    owner, mochi, luna, scheduler = setup
    mochi.add_task(Task("Grooming", "08:00"))
    luna.add_task(Task("Breakfast", "08:00"))

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0]
    assert "Mochi" in warnings[0] and "Luna" in warnings[0]


def test_no_conflict_for_different_times(setup):
    owner, mochi, luna, scheduler = setup
    mochi.add_task(Task("Walk", "07:30"))
    luna.add_task(Task("Breakfast", "08:00"))

    assert scheduler.detect_conflicts() == []


def test_completed_task_is_not_reported_as_conflict(setup):
    owner, mochi, luna, scheduler = setup
    first = Task("Grooming", "08:00")
    mochi.add_task(first)
    luna.add_task(Task("Breakfast", "08:00"))
    first.mark_complete()

    assert scheduler.detect_conflicts() == []


def test_pet_with_no_tasks_and_empty_owner(setup):
    owner, mochi, luna, scheduler = setup

    assert mochi.get_tasks() == []
    assert scheduler.sort_by_time() == []
    assert scheduler.detect_conflicts() == []
    assert scheduler.todays_schedule() == []


@pytest.mark.parametrize("bad_time", ["9:00", "25:99", "", "noon"])
def test_malformed_time_is_rejected(bad_time):
    with pytest.raises(ValueError):
        Task("Walk", bad_time)


def test_invalid_priority_is_rejected():
    with pytest.raises(ValueError):
        Task("Walk", "07:30", priority="urgent")


# --- next available slot ---------------------------------------------------

def slot_setup(*tasks):
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    for t in tasks:
        pet.add_task(t)
    return Scheduler(owner)


def test_next_slot_empty_day_is_start_of_window():
    scheduler = slot_setup()
    assert scheduler.next_available_slot(30, date.today()) == "07:00"


def test_next_slot_skips_past_busy_task():
    scheduler = slot_setup(Task("Walk", "07:00", duration_minutes=45))
    assert scheduler.next_available_slot(30, date.today()) == "07:45"


def test_next_slot_uses_gap_between_tasks():
    scheduler = slot_setup(Task("Walk", "07:00", duration_minutes=30),
                           Task("Vet", "09:00", duration_minutes=60))
    assert scheduler.next_available_slot(60, date.today()) == "07:30"
    assert scheduler.next_available_slot(90, date.today()) == "07:30"  # exact fit
    assert scheduler.next_available_slot(100, date.today()) == "10:00"


def test_next_slot_handles_back_to_back_and_nested_tasks():
    scheduler = slot_setup(Task("A", "07:00", duration_minutes=60),
                           Task("B", "07:10", duration_minutes=10),
                           Task("C", "08:00", duration_minutes=30))
    assert scheduler.next_available_slot(15, date.today()) == "08:30"


def test_next_slot_ignores_completed_and_other_days():
    done = Task("Walk", "07:00", duration_minutes=60)
    tomorrow = Task("Walk", "07:00", duration_minutes=60,
                    due_date=date.today() + timedelta(days=1))
    scheduler = slot_setup(done, tomorrow)
    done.mark_complete()
    assert scheduler.next_available_slot(30, date.today()) == "07:00"


def test_next_slot_returns_none_when_day_is_full():
    scheduler = slot_setup(Task("All day", "07:00", duration_minutes=840))
    assert scheduler.next_available_slot(15, date.today()) is None


def test_next_slot_rejects_non_positive_duration():
    with pytest.raises(ValueError):
        slot_setup().next_available_slot(0, date.today())


# --- persistence -----------------------------------------------------------

def test_save_and_load_round_trip(tmp_path):
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog")
    owner.add_pet(mochi)
    mochi.add_task(Task("Walk", "07:30", duration_minutes=30, priority="high",
                        frequency="daily"))
    done = Task("Bath", "10:00", due_date=date(2026, 1, 5))
    mochi.add_task(done)
    done.mark_complete()

    path = tmp_path / "data.json"
    owner.save_to_json(str(path))
    loaded = Owner.load_from_json(str(path))

    assert loaded == owner
    assert loaded.pets[0].tasks[0].pet_name == "Mochi"
    assert loaded.pets[0].tasks[1].completed is True
    assert loaded.pets[0].tasks[1].due_date == date(2026, 1, 5)


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        Owner.load_from_json(str(tmp_path / "nope.json"))
