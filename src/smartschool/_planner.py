from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from ._objects import ApplicableAssignmentType, PlannedElement
from ._session import SessionMixin

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from datetime import date

__all__ = ["ApplicableAssignmentTypes", "PinnedPlannedElements", "PlannedElements"]

# Types observed on the unfiltered calendar GET (and sidebar filters).
# The model is `PlannedElement.planned_element_type`; this is documentation, not a validator.
PLANNER_ELEMENT_TYPES = (
    "planned-assignments",
    "planned-generics",
    "planned-lesson-cluster-assignments",
    "planned-lesson-cluster-moments",
    "planned-lesson-free-days",
    "planned-lessons",
    "planned-meetings",
    "planned-placeholders",
    "planned-school-activities",
    "planned-to-dos",
)


def _csv_query_value(value: str | Sequence[str] | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    joined = ",".join(part.strip() for part in value if str(part).strip())
    return joined or None


def _planner_query(*, from_date: date, till_date: date, types: str | Sequence[str] | None, includes: str | Sequence[str] | None) -> dict[str, str]:
    data = {"from": from_date.isoformat(), "to": till_date.isoformat()}
    types_csv = _csv_query_value(types)
    if types_csv:
        data["types"] = types_csv
    includes_csv = _csv_query_value(includes)
    if includes_csv:
        data["includes"] = includes_csv
    return data


@dataclass
class ApplicableAssignmentTypes(SessionMixin, Iterable[ApplicableAssignmentType]):
    def __iter__(self) -> Iterator[ApplicableAssignmentType]:
        for type_ in self.session.json("/lesson-content/api/v1/assignments/applicable-assignment-types"):
            yield ApplicableAssignmentType(**type_)


@dataclass
class PlannedElements(SessionMixin, Iterable[PlannedElement]):
    """
    Calendar GET ``/planner/api/v1/planned-elements/user/{id}``.

    Default matches the website timetable: ``from`` and ``to`` only (no ``types`` filter),
    so lessons, school activities, placeholders, assignments, and to-dos all come back.
    Pass ``types`` for sidebar subsets and ``includes`` for the expansion list the SPA uses.
    """

    from_date: date = field(default_factory=lambda: datetime.now(tz=ZoneInfo("Europe/Brussels")).replace(hour=0, minute=0, second=0, microsecond=0))
    till_date: date | None = None
    types: str | Sequence[str] | None = None
    includes: str | Sequence[str] | None = None

    def __post_init__(self):
        if self.till_date is None:
            self.till_date = self.from_date + timedelta(days=34, seconds=-1)

    def __iter__(self) -> Iterator[PlannedElement]:
        assert self.till_date is not None  # set in __post_init__
        payload = self.session.json(
            f"/planner/api/v1/planned-elements/user/{self.session.authenticated_user['id']}",
            data=_planner_query(from_date=self.from_date, till_date=self.till_date, types=self.types, includes=self.includes),
        )
        for element in payload:
            yield PlannedElement(**element)


@dataclass
class PinnedPlannedElements(SessionMixin, Iterable[PlannedElement]):
    """GET ``/planner/api/v1/planned-elements/pinned``."""

    includes: str | Sequence[str] | None = None

    def __iter__(self) -> Iterator[PlannedElement]:
        includes_csv = _csv_query_value(self.includes)
        kwargs = {"data": {"includes": includes_csv}} if includes_csv else {}
        payload = self.session.json("/planner/api/v1/planned-elements/pinned", **kwargs)
        for element in payload:
            yield PlannedElement(**element)
