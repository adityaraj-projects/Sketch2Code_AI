from app.collaboration.connection_manager import CollaborationManager


class FakeConnection:
    def __init__(self, name: str):
        self.name = name
        self.received: list[dict] = []

    async def send_json(self, data: dict) -> None:
        self.received.append(data)


async def test_join_adds_to_room_and_broadcasts_presence():
    manager = CollaborationManager()
    alice = FakeConnection("alice")

    await manager.join("proj1", alice, "u1", "Alice", "#7C5CFF")

    assert manager.room_size("proj1") == 1
    assert alice.received[-1]["type"] == "presence"
    assert alice.received[-1]["participants"][0]["user_name"] == "Alice"


async def test_second_participant_sees_both_in_presence_list():
    manager = CollaborationManager()
    alice = FakeConnection("alice")
    bob = FakeConnection("bob")

    await manager.join("proj1", alice, "u1", "Alice", "#7C5CFF")
    await manager.join("proj1", bob, "u2", "Bob", "#2EE6A6")

    names_in_bobs_view = {p["user_name"] for p in bob.received[-1]["participants"]}
    assert names_in_bobs_view == {"Alice", "Bob"}
    names_in_alices_view = {p["user_name"] for p in alice.received[-1]["participants"]}
    assert names_in_alices_view == {"Alice", "Bob"}


async def test_broadcast_from_excludes_the_sender():
    manager = CollaborationManager()
    alice = FakeConnection("alice")
    bob = FakeConnection("bob")
    await manager.join("proj1", alice, "u1", "Alice", "#7C5CFF")
    await manager.join("proj1", bob, "u2", "Bob", "#2EE6A6")

    await manager.broadcast_from("proj1", alice, {"type": "cursor", "x": 10, "y": 20})

    bob_messages = [m for m in bob.received if m["type"] == "cursor"]
    alice_messages = [m for m in alice.received if m["type"] == "cursor"]
    assert len(bob_messages) == 1
    assert len(alice_messages) == 0


async def test_rooms_are_isolated_between_projects():
    manager = CollaborationManager()
    alice = FakeConnection("alice")
    carol = FakeConnection("carol")
    await manager.join("proj1", alice, "u1", "Alice", "#7C5CFF")
    await manager.join("proj2", carol, "u3", "Carol", "#FF9F43")

    await manager.broadcast_from("proj1", alice, {"type": "canvas_op", "op": {}})

    assert not any(m["type"] == "canvas_op" for m in carol.received)


async def test_leave_removes_participant_and_notifies_remaining():
    manager = CollaborationManager()
    alice = FakeConnection("alice")
    bob = FakeConnection("bob")
    await manager.join("proj1", alice, "u1", "Alice", "#7C5CFF")
    await manager.join("proj1", bob, "u2", "Bob", "#2EE6A6")

    await manager.leave("proj1", alice)

    assert manager.room_size("proj1") == 1
    remaining_names = {p["user_name"] for p in bob.received[-1]["participants"]}
    assert remaining_names == {"Bob"}


async def test_last_participant_leaving_cleans_up_the_room():
    manager = CollaborationManager()
    alice = FakeConnection("alice")
    await manager.join("proj1", alice, "u1", "Alice", "#7C5CFF")

    await manager.leave("proj1", alice)

    assert manager.room_size("proj1") == 0
    assert "proj1" not in manager._rooms
