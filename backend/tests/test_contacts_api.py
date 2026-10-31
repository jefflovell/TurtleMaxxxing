"""Contacts through the HTTP API: the list, privacy, and the people on a task.

All names and details are fictional (example.com, 555-01xx).
"""


def labels(client):
    return {l["name"]: l["id"] for l in client.get("/api/labels").json()}


def make_contact(client, name="Mr. Anderson", **fields):
    res = client.post("/api/contacts", json={"name": name, **fields})
    assert res.status_code == 201, res.text
    return res.json()


def make_task(client, title, **fields):
    res = client.post("/api/tasks", json={"title": title, **fields})
    assert res.status_code == 201, res.text
    return res.json()


def test_contacts_crud_and_sorting(client):
    anderson = make_contact(client, organization="Smith Agency", role="Client contact",
                            email="anderson@example.com", phone="555-0100", location="Smith Agency, 2nd floor")
    assert anderson["organization"] == "Smith Agency" and anderson["is_private"] is False
    make_contact(client, "Pat Rivera", organization="Leak Busters Plumbing")
    make_contact(client, "Aunt Jo")  # no organization: listed last
    names = [c["name"] for c in client.get("/api/contacts").json()]
    assert names == ["Pat Rivera", "Mr. Anderson", "Aunt Jo"]

    res = client.patch(f"/api/contacts/{anderson['id']}", json={"phone": "", "role": "  Director "})
    assert res.json()["phone"] == "" and res.json()["role"] == "Director"
    assert client.delete(f"/api/contacts/{anderson['id']}").status_code == 204
    assert client.get(f"/api/contacts/{anderson['id']}").status_code == 404


def test_contact_search_matches_name_organization_and_place(client):
    make_contact(client, organization="Smith Agency", location="Downtown office")
    make_contact(client, "Pat Rivera", organization="Leak Busters Plumbing", role="Plumber")
    find = lambda q: [c["name"] for c in client.get("/api/contacts", params={"q": q}).json()]
    assert find("smith") == ["Mr. Anderson"]
    assert find("plumb") == ["Pat Rivera"]
    assert find("downtown") == ["Mr. Anderson"]


def test_contact_validation(client):
    assert client.post("/api/contacts", json={"name": ""}).status_code == 422
    assert client.post("/api/contacts", json={"name": "X", "email": "not an email"}).status_code == 422
    assert client.post("/api/contacts", json={"name": "X", "label_ids": [999]}).status_code == 422
    assert client.patch("/api/contacts/999", json={"name": "X"}).status_code == 404


def test_contacts_follow_the_same_private_rule_as_tasks(client):
    ids = labels(client)
    flagged = make_contact(client, "Flagged", private=True)
    tagged = make_contact(client, "Tagged", label_ids=[ids["work"], ids["private"]])
    plain = make_contact(client, "Plain", label_ids=[ids["work"]])
    assert flagged["is_private"] and tagged["is_private"] and not plain["is_private"]

    # Turning auto-Private on for a label applies to contacts that already have it.
    client.patch(f"/api/labels/{ids['work']}", json={"auto_private": True})
    assert client.get(f"/api/contacts/{plain['id']}").json()["is_private"] is True


def test_tasks_list_their_people_with_each_persons_privacy(client):
    ids = labels(client)
    anderson = make_contact(client, organization="Smith Agency", location="Smith Agency, 2nd floor")
    jordan = make_contact(client, "Jordan Lee", organization="Smith Agency", label_ids=[ids["private"]])
    task = make_task(client, "Client meeting", contact_ids=[anderson["id"], jordan["id"]])

    people = {p["name"]: p for p in task["contacts"]}
    assert people["Mr. Anderson"]["organization"] == "Smith Agency"
    assert people["Mr. Anderson"]["location"] == "Smith Agency, 2nd floor"
    # The task itself isn't Private, but a Private person on it is marked, so the AI gate (M3) can withhold them.
    assert task["is_private"] is False
    assert people["Mr. Anderson"]["is_private"] is False and people["Jordan Lee"]["is_private"] is True

    detail = client.get(f"/api/contacts/{anderson['id']}").json()
    assert [t["title"] for t in detail["tasks"]] == ["Client meeting"]
    assert detail["open_task_count"] == 1


def test_changing_and_removing_people_on_a_task(client):
    anderson = make_contact(client)
    rivera = make_contact(client, "Pat Rivera")
    task = make_task(client, "Call about the leak", contact_ids=[anderson["id"]])
    res = client.patch(f"/api/tasks/{task['id']}", json={"contact_ids": [rivera["id"]]})
    assert [p["name"] for p in res.json()["contacts"]] == ["Pat Rivera"]
    assert client.patch(f"/api/tasks/{task['id']}", json={"contact_ids": [999]}).status_code == 422

    # Deleting a contact takes them off the task; the task stays.
    client.delete(f"/api/contacts/{rivera['id']}")
    assert client.get(f"/api/tasks/{task['id']}").json()["contacts"] == []


def test_task_search_finds_tasks_by_their_people(client):
    anderson = make_contact(client, organization="Smith Agency")
    make_task(client, "Prep slides", contact_ids=[anderson["id"]])
    make_task(client, "Water the plants")
    find = lambda q: [t["title"] for t in client.get("/api/tasks", params={"q": q}).json()]
    assert find("anderson") == ["Prep slides"]
    assert find("smith agency") == ["Prep slides"]
