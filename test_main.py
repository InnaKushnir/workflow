import pytest
from fastapi.testclient import TestClient


from main import app, get_db
from db.models import Base, Workflow
from test_db import override_get_db, TestingSessionLocal

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():

    Base.metadata.create_all(bind=TestingSessionLocal().get_bind())
    yield

    Base.metadata.drop_all(bind=TestingSessionLocal().get_bind())


def test_create_get_all_workflow():
    workflow = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    response = client.post("/workflows/", json=workflow)

    assert response.status_code == 200
    created_workflow_id = response.json()["id"]

    response = client.get("/workflows/")

    assert response.status_code == 200

    assert isinstance(response.json(), list)

    workflows = response.json()
    assert any(workflow["id"] == created_workflow_id for workflow in workflows)


def test_get_workflow():

    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    create_response = client.post("/workflows/", json=workflow_data)

    assert create_response.status_code == 200
    created_workflow = create_response.json()
    workflow_id = created_workflow["id"]

    response = client.get(f"/workflows/{workflow_id}/")

    assert response.status_code == 200

    retrieved_workflow = response.json()
    assert retrieved_workflow["id"] == created_workflow["id"]
    assert retrieved_workflow["name"] == created_workflow["name"]

def test_create_and_get_nodes():
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    create_workflow_response = client.post("/workflows/", json=workflow_data)
    assert create_workflow_response.status_code == 200
    workflow_id = create_workflow_response.json()["id"]

    node_data = {
        "type": "Start",
        "status": "pending",
        "message": "Start node"
    }
    create_node_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node_data)
    assert create_node_response.status_code == 200
    assert create_node_response.json()["message"] == node_data["message"]

    get_nodes_response = client.get("/nodes/")
    assert get_nodes_response.status_code == 200
    nodes = get_nodes_response.json()

    created_node_id = create_node_response.json()["id"]
    created_node_present = any(node["id"] == created_node_id for node in nodes)
    assert created_node_present, f"Created node with ID {created_node_id} not found in the list of nodes"

def test_create_edge():
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    create_workflow_response = client.post("/workflows/", json=workflow_data)
    assert create_workflow_response.status_code == 200
    workflow_id = create_workflow_response.json()["id"]

    node1_data = {
        "type": "Start",
        "status": "pending",
        "message": "Start node"
    }
    node2_data = {
        "type": "End",
        "status": "pending",
        "message": "End node"
    }
    node1_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node1_data)
    assert node1_response.status_code == 200
    node1_id = node1_response.json()["id"]

    node2_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node2_data)
    assert node2_response.status_code == 200
    node2_id = node2_response.json()["id"]

    edge_data = {
        "start_node_id": node1_id,
        "end_node_id": node2_id,
        "status": "Yes"
    }
    create_edge_response = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data)
    assert create_edge_response.status_code == 200
    created_edge_id = create_edge_response.json()["id"]
    assert create_edge_response.json()["status"] == edge_data["status"]

    edge_data_same_start_node = {
        "start_node_id": node1_id,
        "end_node_id": node2_id,
        "status": "Yes"
    }
    response_same_start_node = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data_same_start_node)
    assert response_same_start_node.status_code == 400
    assert "Start Node can only have one outgoing edge." in response_same_start_node.json()["detail"]

    node3_data = {
        "type": "Message",
        "status": "pending",
        "message": "Message node"
    }
    node3_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node3_data)
    assert node3_response.status_code == 200
    node3_id = node3_response.json()["id"]

def test_create_edge_start_node():

    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    create_workflow_response = client.post("/workflows/", json=workflow_data)
    assert create_workflow_response.status_code == 200
    workflow_id = create_workflow_response.json()["id"]

    node_data = {
        "type": "Start",
        "status": "pending",
        "message": "Start node"
    }
    create_node_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node_data)
    assert create_node_response.status_code == 200
    start_node_id = create_node_response.json()["id"]

    node2_data = {
        "type": "End",
        "status": "pending",
        "message": "End node"
    }
    create_node2_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node2_data)
    assert create_node2_response.status_code == 200
    end_node_id = create_node2_response.json()["id"]

    edge_data = {
        "start_node_id": start_node_id,
        "end_node_id": end_node_id,
        "status": "Yes"
    }
    create_edge_response = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data)
    assert create_edge_response.status_code == 200

    edge_data_invalid = {
        "start_node_id": start_node_id,
        "end_node_id": end_node_id,
        "status": "No"
    }
    response_invalid = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data_invalid)
    assert response_invalid.status_code == 400
    assert "Start Node can only have one outgoing edge" in response_invalid.json()["detail"]

def test_create_edge_message_node():
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    create_workflow_response = client.post("/workflows/", json=workflow_data)
    assert create_workflow_response.status_code == 200
    workflow_id = create_workflow_response.json()["id"]

    node_data = {
        "type": "Message",
        "status": "pending",
        "message": "Message node"
    }
    create_node_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node_data)
    assert create_node_response.status_code == 200
    message_node_id = create_node_response.json()["id"]

    node2_data = {
        "type": "End",
        "status": "pending",
        "message": "End node"
    }
    create_node2_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node2_data)
    assert create_node2_response.status_code == 200
    end_node_id = create_node2_response.json()["id"]

    edge_data = {
        "start_node_id": message_node_id,
        "end_node_id": end_node_id,
        "status": "Yes"
    }
    create_edge_response = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data)
    assert create_edge_response.status_code == 200

    node3_data = {
        "type": "Start",
        "status": "pending",
        "message": "Start node"
    }
    create_node3_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node3_data)
    assert create_node3_response.status_code == 200
    start_node_id = create_node3_response.json()["id"]

    edge_data_invalid_start = {
        "start_node_id": start_node_id,
        "end_node_id": end_node_id,
        "status": "Yes"
    }
    response_invalid_start = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data_invalid_start)
    assert response_invalid_start.status_code == 200

def test_get_node():
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    create_workflow_response = client.post("/workflows/", json=workflow_data)
    assert create_workflow_response.status_code == 200
    workflow_id = create_workflow_response.json()["id"]

    node_data = {
        "type": "Start",
        "status": "pending",
        "message": "Start node"
    }
    create_node_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node_data)

    assert create_node_response.status_code == 200, f"Unexpected status code: {create_node_response.status_code}, response: {create_node_response.json()}"
    response_json = create_node_response.json()
    print(f"Create node response: {response_json}")

    node_id = response_json["id"]
    get_node_response = client.get(f"/nodes/{node_id}/")
    node_json = get_node_response.json()
    print(f"Get node response: {node_json}")

    assert node_json["id"] == node_id, f"Expected node ID: {node_id}, but got: {node_json['id']}"
    assert node_json["type"] == node_data[
        "type"], f"Expected node type: {node_data['type']}, but got: {node_json['type']}"
    assert node_json["status"] == node_data[
        "status"], f"Expected node status: {node_data['status']}, but got: {node_json['status']}"
    assert node_json["message"] == node_data[
        "message"], f"Expected node message: {node_data['message']}, but got: {node_json['message']}"
    assert node_json[
               "workflow_id"] == workflow_id, f"Expected workflow ID: {workflow_id}, but got: {node_json['workflow_id']}"


def test_get_all_edges():
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    create_workflow_response = client.post("/workflows/", json=workflow_data)
    assert create_workflow_response.status_code == 200
    workflow_id = create_workflow_response.json()["id"]

    node1_data = {
        "type": "Start",
        "status": "pending",
        "message": "Start node"
    }
    node2_data = {
        "type": "End",
        "status": "pending",
        "message": "End node"
    }
    node1_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node1_data)
    assert node1_response.status_code == 200
    node1_id = node1_response.json()["id"]

    node2_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node2_data)
    assert node2_response.status_code == 200
    node2_id = node2_response.json()["id"]

    edge_data = {
        "start_node_id": node1_id,
        "end_node_id": node2_id,
        "status": "Yes"
    }
    create_edge_response = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data)
    assert create_edge_response.status_code == 200
    created_edge_id = create_edge_response.json()["id"]

    response = client.get("/edges/")
    assert response.status_code == 200
    edges = response.json()

    created_edge_present = any(edge["id"] == created_edge_id for edge in edges)
    assert created_edge_present, f"Created edge with ID {created_edge_id} not found in the list of edges"

def test_update_edge():
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    create_workflow_response = client.post("/workflows/", json=workflow_data)
    assert create_workflow_response.status_code == 200
    workflow_id = create_workflow_response.json()["id"]

    node1_data = {
        "type": "Start",
        "status": "pending",
        "message": "Start node"
    }
    node2_data = {
        "type": "End",
        "status": "pending",
        "message": "End node"
    }
    node1_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node1_data)
    assert node1_response.status_code == 200
    node1_id = node1_response.json()["id"]

    node2_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node2_data)
    assert node2_response.status_code == 200
    node2_id = node2_response.json()["id"]

    edge_data = {
        "start_node_id": node1_id,
        "end_node_id": node2_id,
        "status": "Yes"
    }
    create_edge_response = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data)
    assert create_edge_response.status_code == 200
    edge_id = create_edge_response.json()["id"]

    updated_edge_data = {
        "start_node_id": node1_id,
        "end_node_id": node2_id,
        "status": "No"
    }
    update_edge_response = client.put(f"/edges/{edge_id}/", json=updated_edge_data)
    assert update_edge_response.status_code == 200

    updated_edge = update_edge_response.json()
    assert updated_edge["id"] == edge_id, f"Expected edge ID: {edge_id}, but got: {updated_edge['id']}"
    assert updated_edge["start_node_id"] == node1_id, f"Expected start_node_id: {node1_id}, but got: {updated_edge['start_node_id']}"
    assert updated_edge["end_node_id"] == node2_id, f"Expected end_node_id: {node2_id}, but got: {updated_edge['end_node_id']}"
    assert updated_edge["status"] == updated_edge_data["status"], f"Expected status: {updated_edge_data['status']}, but got: {updated_edge['status']}"

    invalid_edge_id = edge_id + 999
    invalid_update_response = client.put(f"/edges/{invalid_edge_id}/", json=updated_edge_data)
    assert invalid_update_response.status_code == 404
    assert invalid_update_response.json()["detail"] == "Edge not found"

def test_get_edge_by_id():
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    create_workflow_response = client.post("/workflows/", json=workflow_data)
    assert create_workflow_response.status_code == 200
    workflow_id = create_workflow_response.json()["id"]

    node1_data = {
        "type": "Start",
        "status": "pending",
        "message": "Start node"
    }
    node2_data = {
        "type": "End",
        "status": "pending",
        "message": "End node"
    }
    node1_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node1_data)
    assert node1_response.status_code == 200
    node1_id = node1_response.json()["id"]

    node2_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node2_data)
    assert node2_response.status_code == 200
    node2_id = node2_response.json()["id"]

    edge_data = {
        "start_node_id": node1_id,
        "end_node_id": node2_id,
        "status": "Yes"
    }
    create_edge_response = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data)
    assert create_edge_response.status_code == 200
    created_edge_id = create_edge_response.json()["id"]

    response = client.get(f"/edges/{created_edge_id}/")
    assert response.status_code == 200


def test_run_workflow_with_complex_scenario():
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    create_workflow_response = client.post("/workflows/", json=workflow_data)
    assert create_workflow_response.status_code == 200
    workflow_id = create_workflow_response.json()["id"]

    node1_data = {"type": "Start", "status": "pending", "message": "Start node"}
    node2_data = {"type": "Message", "status": "pending", "message": "Message node 1"}
    node3_data = {"type": "Condition", "status": "pending", "message": "Condition node",
                  "condition_expression": "message == 'hello'"}
    node4_data = {"type": "Message", "status": "pending", "message": "Message node 2"}
    node5_data = {"type": "Message", "status": "pending", "message": "Message node 3"}
    node6_data = {"type": "End", "status": "pending", "message": "End node"}

    nodes_data = [node1_data, node2_data, node3_data, node4_data, node5_data, node6_data]
    node_ids = []

    for node_data in nodes_data:
        node_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node_data)
        assert node_response.status_code == 200
        node_id = node_response.json()["id"]
        node_ids.append(node_id)

    edges_data = [
        {"start_node_id": node_ids[0], "end_node_id": node_ids[1], "status": "Yes"},
        {"start_node_id": node_ids[1], "end_node_id": node_ids[2], "status": "Yes"},
        {"start_node_id": node_ids[2], "end_node_id": node_ids[3], "status": "Yes"},
        {"start_node_id": node_ids[2], "end_node_id": node_ids[4], "status": "No"},
        {"start_node_id": node_ids[3], "end_node_id": node_ids[5], "status": "Yes"}
    ]

    for edge_data in edges_data:
        create_edge_response = client.post(f"/workflows/{workflow_id}/edges/", json=edge_data)
        if create_edge_response.status_code != 200:
            print(create_edge_response.json())
        assert create_edge_response.status_code == 200

    run_workflow_response = client.post(f"/workflows/{workflow_id}/run/")
    assert run_workflow_response.status_code == 200

    result = run_workflow_response.json()
    assert "path" in result
    assert isinstance(result["path"], list)
    assert len(result["path"]) > 0

    for node in result["path"]:
        assert "id" in node
        assert "type" in node
        assert "status" in node
        assert "message" in node
