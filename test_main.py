import pytest
from fastapi.testclient import TestClient

from db.models import Base
from main import app, get_db
from test_db import override_get_db, TestingSessionLocal

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    Base.metadata.create_all(bind=TestingSessionLocal().get_bind())
    yield

    Base.metadata.drop_all(bind=TestingSessionLocal().get_bind())


def create_workflow(client, name="Test Workflow", description="A test workflow"):
    workflow_data = {"name": name, "description": description}
    response = client.post("/workflows/", json=workflow_data)
    assert response.status_code == 200
    return response.json()


def create_node(client, workflow_id, node_type="Start", status="pending", message="Start node",
                condition_expression=None):
    node_data = {"type": node_type, "status": status, "message": message}
    if condition_expression:
        node_data["condition_expression"] = condition_expression
    response = client.post(f"/workflows/{workflow_id}/nodes/", json=node_data)
    assert response.status_code == 200
    return response.json()


def create_edge(client, workflow_id, start_node_id, end_node_id, status="Yes"):
    edge_data = {"start_node_id": start_node_id, "end_node_id": end_node_id, "status": status}
    response = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data)
    assert response.status_code == 200
    return response.json()


def test_create_get_all_workflow():
    workflow = create_workflow(client)
    created_workflow_id = workflow["id"]

    response = client.get("/workflows/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    workflows = response.json()
    assert any(w["id"] == created_workflow_id for w in workflows)


def test_get_workflow():
    created_workflow = create_workflow(client)
    workflow_id = created_workflow["id"]

    response = client.get(f"/workflows/{workflow_id}/")
    assert response.status_code == 200

    retrieved_workflow = response.json()
    assert retrieved_workflow["id"] == created_workflow["id"]
    assert retrieved_workflow["name"] == created_workflow["name"]


def test_create_and_get_nodes():
    workflow = create_workflow(client)
    workflow_id = workflow["id"]

    node = create_node(client, workflow_id)
    node_id = node["id"]

    response = client.get("/nodes/")
    assert response.status_code == 200

    nodes = response.json()
    assert any(n["id"] == node_id for n in nodes)


def test_create_edge():
    workflow = create_workflow(client)
    workflow_id = workflow["id"]

    node1 = create_node(client, workflow_id)
    node2 = create_node(client, workflow_id, node_type="End")

    edge = create_edge(client, workflow_id, node1["id"], node2["id"])
    edge_id = edge["id"]

    edge_data_same_start_node = {
        "start_node_id": node1["id"],
        "end_node_id": node2["id"],
        "status": "Yes"
    }
    response_same_start_node = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data_same_start_node)
    assert response_same_start_node.status_code == 400
    assert "Start Node can only have one outgoing edge." in response_same_start_node.json()["detail"]

    node3 = create_node(client, workflow_id, node_type="Message")


def test_create_edge_start_node():
    workflow = create_workflow(client)
    workflow_id = workflow["id"]

    start_node = create_node(client, workflow_id)
    end_node = create_node(client, workflow_id, node_type="End")

    edge = create_edge(client, workflow_id, start_node["id"], end_node["id"])

    edge_data_invalid = {
        "start_node_id": start_node["id"],
        "end_node_id": end_node["id"],
        "status": "No"
    }
    response_invalid = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data_invalid)
    assert response_invalid.status_code == 400
    assert "Start Node can only have one outgoing edge" in response_invalid.json()["detail"]


def test_create_edge_message_node():
    workflow = create_workflow(client)
    workflow_id = workflow["id"]

    message_node = create_node(client, workflow_id, node_type="Message")
    end_node = create_node(client, workflow_id, node_type="End")

    edge = create_edge(client, workflow_id, message_node["id"], end_node["id"])

    start_node = create_node(client, workflow_id, node_type="Start")

    edge_data_invalid_start = {
        "start_node_id": start_node["id"],
        "end_node_id": end_node["id"],
        "status": "Yes"
    }
    response_invalid_start = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data_invalid_start)
    assert response_invalid_start.status_code == 200


def test_get_node():
    workflow = create_workflow(client)
    workflow_id = workflow["id"]

    node = create_node(client, workflow_id)
    node_id = node["id"]

    response = client.get(f"/nodes/{node_id}/")
    assert response.status_code == 200

    node_json = response.json()
    assert node_json["id"] == node_id
    assert node_json["type"] == node["type"]
    assert node_json["status"] == node["status"]
    assert node_json["message"] == node["message"]
    assert node_json["workflow_id"] == workflow_id


def test_get_all_edges():
    workflow = create_workflow(client)
    workflow_id = workflow["id"]

    node1 = create_node(client, workflow_id)
    node2 = create_node(client, workflow_id, node_type="End")

    edge = create_edge(client, workflow_id, node1["id"], node2["id"])
    edge_id = edge["id"]

    response = client.get("/edges/")
    assert response.status_code == 200

    edges = response.json()
    assert any(e["id"] == edge_id for e in edges)


def test_update_edge():
    workflow = create_workflow(client)
    workflow_id = workflow["id"]

    node1 = create_node(client, workflow_id)
    node2 = create_node(client, workflow_id, node_type="End")

    edge = create_edge(client, workflow_id, node1["id"], node2["id"])
    edge_id = edge["id"]

    updated_edge_data = {
        "start_node_id": node1["id"],
        "end_node_id": node2["id"],
        "status": "No"
    }
    update_edge_response = client.put(f"/edges/{edge_id}/", json=updated_edge_data)
    assert update_edge_response.status_code == 200

    updated_edge = update_edge_response.json()
    assert updated_edge["id"] == edge_id
    assert updated_edge["start_node_id"] == node1["id"]
    assert updated_edge["end_node_id"] == node2["id"]
    assert updated_edge["status"] == updated_edge_data["status"]

    invalid_edge_id = edge_id + 999
    invalid_update_response = client.put(f"/edges/{invalid_edge_id}/", json=updated_edge_data)
    assert invalid_update_response.status_code == 404
    assert invalid_update_response.json()["detail"] == "Edge not found"


def test_get_edge_by_id():
    workflow = create_workflow(client)
    workflow_id = workflow["id"]

    node1 = create_node(client, workflow_id)
    node2 = create_node(client, workflow_id, node_type="End")

    edge = create_edge(client, workflow_id, node1["id"], node2["id"])
    edge_id = edge["id"]

    response = client.get(f"/edges/{edge_id}/")
    assert response.status_code == 200


def test_run_workflow_with_complex_scenario():
    workflow = create_workflow(client)
    workflow_id = workflow["id"]

    nodes = [
        create_node(client, workflow_id, node_type="Start"),
        create_node(client, workflow_id, node_type="Message", message="Message node 1"),
        create_node(client, workflow_id, node_type="Condition", message="Condition node",
                    condition_expression="message == 'hello'"),
        create_node(client, workflow_id, node_type="Message", message="Message node 2"),
        create_node(client, workflow_id, node_type="Message", message="Message node 3"),
        create_node(client, workflow_id, node_type="End"),
    ]
    node_ids = [node["id"] for node in nodes]

    edges = [
        {"start_node_id": node_ids[0], "end_node_id": node_ids[1], "status": None},
        {"start_node_id": node_ids[1], "end_node_id": node_ids[2], "status": None},
        {"start_node_id": node_ids[2], "end_node_id": node_ids[3], "status": "Yes"},
        {"start_node_id": node_ids[2], "end_node_id": node_ids[4], "status": "No"},
        {"start_node_id": node_ids[3], "end_node_id": node_ids[5], "status": "Yes"},
        {"start_node_id": node_ids[4], "end_node_id": node_ids[5], "status": "Yes"},
    ]

    for edge_data in edges:
        create_edge(client, workflow_id, edge_data["start_node_id"], edge_data["end_node_id"], edge_data["status"])
    expected_path = [
        {"id": node_ids[0], "type": "Start", "status": None, "message": None},
        {"id": node_ids[1], "type": "Message", "status": None, "message": "Message node 1"},
        {"id": node_ids[2], "type": "Condition", "status": None, "message": "Condition node"},
        {"id": node_ids[4], "type": "Message", "status": None, "message": "Message node 2"},
        {"id": node_ids[5], "type": "End", "status": None, "message": None},
    ]

    response = client.post(f"/workflows/{workflow_id}/run/")
    response_json = response.json()
    assert response.status_code == 200
    assert "path" in response_json
