# Planner & Tasks

## Planned Elements

Scheduled assignments, activities, lessons, and to-dos from the Smartschool planner.

The website calendar calls `GET /planner/api/v1/planned-elements/user/{id}` with **`from` and `to` only**. That unfiltered response is the timetable. Sidebar widgets add `types=` and/or `includes=`.

```python
from datetime import date
from smartschool import Smartschool, PathCredentials, PlannedElements, PinnedPlannedElements

session = Smartschool(PathCredentials())

# Default: today + 34 days, no types filter (same as the calendar grid)
for element in PlannedElements(session):
    print(f"{element.name} ({element.plannedElementType})")
    print(f"  From: {element.period.dateTimeFrom}")
    print(f"  To:   {element.period.dateTimeTo}")
    print(f"  Color: {element.color}")

    if element.courses:
        print(f"  Courses: {', '.join(c.name for c in element.courses)}")

    if element.organisers:
        for user in element.organisers.users:
            print(f"  Organiser: {user.name.startingWithFirstName}")
```

### Custom Date Range

```python
elements = PlannedElements(
    session,
    from_date=date(2026, 3, 1),
    till_date=date(2026, 3, 31),
)

for element in elements:
    print(element.name)
```

### Types and includes

`types` and `includes` are optional. Omit `types` for the full calendar. Pass a comma-separated string or a sequence of strings for a sidebar subset.

```python
sidebar = PlannedElements(
    session,
    types="planned-assignments,planned-to-dos",
    includes="icon,courses,locations,upload-folders,labels",
)
```

### Element Types

The `plannedElementType` field indicates the type. Values seen on the wire include:

- `planned-lessons` — timetable lessons
- `planned-school-activities` — school-wide activities
- `planned-lesson-cluster-moments` / `planned-lesson-cluster-assignments`
- `planned-placeholders` — placeholder events
- `planned-assignments` — assignments with courses, participants, and locations
- `planned-to-dos` — personal to-do items (may not have courses/participants)
- `planned-generics`, `planned-lesson-free-days`, `planned-meetings`

### Pinned elements

```python
for element in PinnedPlannedElements(session, includes="icon,courses,locations,upload-folders,labels"):
    print(element.name)
```

## Future Tasks

Deprecated: `POST /Agenda/Futuretasks/getFuturetasks` is the old Schoolagenda sidebar.
Prefer `PlannedElements` with a `types` filter.

Upcoming assignments and deadlines grouped by day and course.

```python
from smartschool import FutureTasks

for day in FutureTasks(session):
    print(f"\n{day.pretty_date} ({day.date})")
    for course in day.courses:
        print(f"  {course.course_title}:")
        for task in course.items.tasks:
            print(f"    - {task.label}: {task.description}")
            if task.warning:
                print(f"      [WARNING]")
```

## Assignment Types

List the available assignment types configured for the platform.

```python
from smartschool import ApplicableAssignmentTypes

for atype in ApplicableAssignmentTypes(session):
    print(f"{atype.name} ({atype.abbreviation}) - weight: {atype.weight}")
```
