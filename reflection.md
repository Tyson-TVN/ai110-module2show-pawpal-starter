# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The three things a user needs to do are add a pet, schedule a task for that pet, and see the day's tasks in order. I split the system into four classes:

- `Task` holds one activity: what it is, when (`HH:MM`), the due date, how long it takes, its priority, how often it repeats, and whether it is done. It can mark itself complete.
- `Pet` holds a name, a species and its list of tasks, and knows how to add or remove one.
- `Owner` holds the list of pets and has `get_all_tasks()`, which returns every pet's tasks together.
- `Scheduler` is the brain. It takes an `Owner` and does the sorting, filtering, conflict checking and recurring-task logic. It never keeps its own copy of the data; it always asks the owner.

I used dataclasses for `Task`, `Pet` and `Owner` because they are mostly data. `Scheduler` is a normal class because it is mostly behavior.

**b. Design changes**

- I added a `pet_name` field to `Task`, and `Pet.add_task()` fills it in. Without it the scheduler could not filter by pet, could not say which pet a conflict belongs to, and could not find the right pet to attach the next occurrence of a recurring task to.
- `mark_task_complete()` returns early if a task is already completed. The first version would have created a second copy of a daily task if the button was pressed twice, so I added that guard and a test for it.
- Conflict detection ignores completed tasks, since a finished task at 08:00 should not block a new one.
- [[FILL IN: one change you made because of the feedback from AI chat #1, or write "I did not change the design after the review" if that is true.]]

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler looks at the time of day and the due date first, because a pet owner mostly needs to know "what is next". Priority is a second way to sort, for when the day is too full to do everything. Duration is stored and shown but not used to block out time. I put time first because it is the thing that decides whether something gets done; priority only matters once there is a choice to make.

**b. Tradeoffs**

`detect_conflicts()` only flags tasks that start at exactly the same date and time. It does not notice that a 45 minute grooming session starting at 08:00 overlaps a feeding at 08:30. I kept it this way because exact matching is simple to read, simple to test, and catches the most obvious double-booking. Real overlap checking would need start and end times and a more complicated comparison. For a household with a few pets it is reasonable, and the warning is advice rather than a block, so a missed overlap does not break anything.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code in VS Code as the main tool. I had it help plan the order of work, draft the UML, write the class skeleton, implement the classes and algorithms, write the demo script and the tests, build the Streamlit page, and draft the README. I used separate chats for separate jobs: one to review the skeleton, one to plan edge-case tests, and one to look at simplifying an algorithm. The prompts that worked best were specific ones that named the file and the question, such as asking for the three most important problems in the skeleton rather than "review my code".

[[FILL IN: one sentence on how keeping those chats separate helped, in your own words.]]

**b. Judgment and verification**

[[FILL IN: describe one real suggestion from the AI chats that you rejected or changed, what it was, and why. This must be something that actually happened.]]

I did not take the code on trust. I ran `python main.py` and checked the output by eye against what I expected, ran `python -m pytest` until all tests passed, and ran the Streamlit app, adding pets and tasks, creating a same-time conflict and completing a daily task to see the next day's task appear.

---

## 4. Testing and Verification

**a. What you tested**

I wrote 14 tests. They cover task completion, adding tasks to a pet, sorting by time across two pets, sorting by priority, filtering by pet and by status, daily and weekly recurrence, one-time tasks not recurring, completing a task twice, conflicts across pets, no false conflicts, completed tasks being ignored in conflict checks, empty pets and owners, and an invalid priority. These matter because sorting, recurrence and conflicts are the parts that make the app useful, and they are easy to get subtly wrong.

**b. Confidence**

I am fairly confident (4 out of 5). The core behaviors are tested and pass, and I ran the UI flow end to end. What I would test next: overlapping durations, tasks that cross midnight, badly formatted times, a pet name that appears twice, and weekly tasks completed late.

---

## 5. Reflection

**a. What went well**

Building the logic and the terminal demo before the web page. When I got to the UI almost nothing needed fixing because the classes already worked.

**b. What you would improve**

I would make conflict detection duration-aware and let the owner edit or delete tasks in the UI. I would also save pets and tasks to a file so they survive closing the app.

**c. Key takeaway**

The AI could write code quickly, but the decisions that mattered were mine: what the classes are responsible for, what counts as a conflict, and what to leave out. Having a clear design and tests first made it easy to tell whether what the AI produced was right.
