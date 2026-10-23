import json

from app.toolbox import ToolBox


def test_cancel_changes_only_this_session():
    a, b = ToolBox(), ToolBox()
    rid = json.loads(a.call("get_user_details", {"user_id": "yusuf_li_4428"}))["result"]["reservations"][0]
    a.call("cancel_reservation", {"reservation_id": rid})
    assert a.cancelled() == [rid]
    assert b.cancelled() == []
    assert json.loads(b.call("get_reservation_details", {"reservation_id": rid}))["result"].get("status") is None


def test_errors_are_returned_not_raised():
    out = json.loads(ToolBox().call("get_reservation_details", {"reservation_id": "NOPE00"}))
    assert "not found" in out["error"]


def test_call_log_records_turn():
    tb = ToolBox(turn=lambda: 3)
    tb.call("get_flight_status", {"flight_number": "HAT170", "date": "2024-05-22"})
    assert tb.log[0]["turn"] == 3 and tb.log[0]["ok"]
