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
