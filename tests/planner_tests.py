import json
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import time_machine

from smartschool import ApplicableAssignmentTypes, PinnedPlannedElements, PlannedElement, PlannedElements, Smartschool


def _query(requests_mock) -> dict[str, list[str]]:
    return parse_qs(urlparse(requests_mock.last_request.url).query)


@time_machine.travel("2025-05-06")
def test_periods_happy_flow(session: Smartschool):
    sut = list(PlannedElements(session))

    assert len(sut) == 25

    assert sut[0].courses[0].name == "Godsdienst"
    assert sut[0].planned_element_type == "planned-placeholders"
    assert not sut[0].unconfirmed


@time_machine.travel("2025-05-06")
def test_planned_elements_till_date(session: Smartschool):
    sut = list(PlannedElements(session, till_date=date(2025, 5, 7)))

    assert len(sut) == 1

    assert sut[0].courses[0].name == "Dummy"
    assert sut[0].planned_element_type == "planned-placeholders"
    assert sut[0].unconfirmed


@time_machine.travel("2025-05-06")
def test_planned_elements_omits_types_by_default(session: Smartschool, requests_mock):
    list(PlannedElements(session))
    qs = _query(requests_mock)
    assert "types" not in qs
    assert "includes" not in qs
    assert qs["from"] == ["2025-05-06T00:00:00+02:00"]


@time_machine.travel("2025-05-06")
def test_planned_elements_sends_types_and_includes(session: Smartschool, requests_mock):
    list(
        PlannedElements(
            session,
            types=["planned-lessons", "planned-assignments"],
            includes="icon,courses,locations,upload-folders,labels",
        )
    )
    qs = _query(requests_mock)
    assert qs["types"] == ["planned-lessons,planned-assignments"]
    assert qs["includes"] == ["icon,courses,locations,upload-folders,labels"]


def test_pinned_planned_elements_default(session: Smartschool, requests_mock):
    assert list(PinnedPlannedElements(session)) == []
    assert "/planner/api/v1/planned-elements/pinned" in requests_mock.last_request.url
    assert requests_mock.last_request.query in ("", None) or "includes" not in parse_qs(requests_mock.last_request.query)


def test_pinned_planned_elements_sends_includes(session: Smartschool, requests_mock):
    list(PinnedPlannedElements(session, includes=["icon", "courses"]))
    qs = _query(requests_mock)
    assert qs["includes"] == ["icon,courses"]


def test_applicable_assignment_types(session: Smartschool):
    sut = list(ApplicableAssignmentTypes(session))

    assert len(sut) == 7

    obj = sut[0]
    assert obj.abbreviation == "-"
    assert obj.id == "12657aa0-3b29-4977-925b-e2a0f133f2ba"
    assert obj.is_visible is True
    assert obj.name == "-"
    assert obj.platform_id == 49
    assert obj.weight == pytest.approx(1.0)


def test_planned_element_tolerates_missing_restore_from_trash():
    """Live calendar GETs omit canUserRestoreFromTrash on some lesson payloads."""
    fixture = Path(__file__).parent / "requests/get/planner/api/v1/planned-elements/user/49_10880_2/1b58e50a13c1.json"
    payload = json.loads(fixture.read_text(encoding="utf8"))[0]
    del payload["capabilities"]["canUserRestoreFromTrash"]

    element = PlannedElement(**payload)

    assert element.capabilities.can_user_restore_from_trash is False
