import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "app"))

from app import app, cleanup_rooms, create_room, new_room_state, rooms, socketio  # noqa: E402


@pytest.fixture(autouse=True)
def reset_rooms():
    rooms.clear()
    yield
    rooms.clear()


def test_root_redirects_to_a_new_unique_room():
    first = app.test_client().get("/")
    second = app.test_client().get("/")

    assert first.status_code == 302
    assert second.status_code == 302
    assert re.fullmatch(r"/room/[0-9a-f]{16}", first.location)
    assert re.fullmatch(r"/room/[0-9a-f]{16}", second.location)
    assert first.location != second.location


def test_room_page_contains_its_room_id():
    room_id = create_room()
    response = app.test_client().get(f"/room/{room_id}")

    assert response.status_code == 200
    assert room_id.encode() in response.data


def test_timer_events_are_isolated_between_rooms():
    room_a_id = create_room()
    room_b_id = create_room()
    room_a = socketio.test_client(app, query_string=f"room_id={room_a_id}")
    room_b = socketio.test_client(app, query_string=f"room_id={room_b_id}")

    room_a.get_received()
    room_b.get_received()

    room_a.emit("start_timer", {"minutes": 1, "seconds": 0})

    assert any(event["name"] == "timer_started" for event in room_a.get_received())
    assert not any(event["name"] == "timer_started" for event in room_b.get_received())

    room_a.disconnect()
    room_b.disconnect()


def test_new_client_in_same_room_receives_existing_timer_state():
    room_id = create_room()
    first_client = socketio.test_client(app, query_string=f"room_id={room_id}")
    first_client.get_received()
    first_client.emit("start_timer", {"minutes": 2, "seconds": 30})
    first_client.get_received()

    second_client = socketio.test_client(app, query_string=f"room_id={room_id}")
    updates = [event for event in second_client.get_received() if event["name"] == "timer_update"]

    assert updates
    assert updates[-1]["args"][0]["is_running"] is True
    assert updates[-1]["args"][0]["remaining_time"] == pytest.approx(150)

    first_client.disconnect()
    second_client.disconnect()


def test_idle_room_is_removed_by_cleanup():
    room_id = create_room()
    rooms[room_id]["last_activity"] = datetime.now() - timedelta(hours=2)

    cleanup_rooms()

    assert room_id not in rooms


def test_active_or_connected_room_is_not_removed_by_cleanup():
    active_room_id = create_room()
    connected_room_id = create_room()
    old = datetime.now() - timedelta(hours=2)
    rooms[active_room_id]["last_activity"] = old
    rooms[active_room_id]["is_running"] = True
    rooms[connected_room_id]["last_activity"] = old
    rooms[connected_room_id]["connected_clients"] = 1

    cleanup_rooms()

    assert active_room_id in rooms
    assert connected_room_id in rooms


def test_deleted_room_url_returns_not_found():
    room_id = create_room()
    rooms[room_id]["last_activity"] = datetime.now() - timedelta(hours=2)
    cleanup_rooms()

    response = app.test_client().get(f"/room/{room_id}")

    assert response.status_code == 404


def test_timer_duration_is_limited_to_24_hours():
    room_id = create_room()
    client = socketio.test_client(app, query_string=f"room_id={room_id}")
    client.get_received()

    client.emit("start_timer", {"minutes": 1440, "seconds": 1})
    events = client.get_received()

    assert any(event["name"] == "timer_error" for event in events)
    assert rooms[room_id]["is_running"] is False
    client.disconnect()


def test_invalid_timer_duration_is_rejected_without_exception():
    room_id = create_room()
    client = socketio.test_client(app, query_string=f"room_id={room_id}")
    client.get_received()

    client.emit("start_timer", {"minutes": "not-a-number", "seconds": 0})
    events = client.get_received()

    assert any(event["name"] == "timer_error" for event in events)
    assert rooms[room_id]["is_running"] is False
    client.disconnect()


def test_timer_event_does_not_recreate_deleted_room():
    room_id = create_room()
    client = socketio.test_client(app, query_string=f"room_id={room_id}")
    client.get_received()
    del rooms[room_id]

    client.emit("stop_timer")

    assert room_id not in rooms
    client.disconnect()


def test_malformed_room_id_is_not_served():
    rooms["not-a-generated-room-id"] = new_room_state()

    response = app.test_client().get("/room/not-a-generated-room-id")

    assert response.status_code == 404
