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
    response_json = create_node_response.json()
    print(f"Create node response: {response_json}")

    node_id = response_json["id"]
    get_node_response = client.get(f"/nodes/1/")
    assert get_node_response.status_code == 200, f"Unexpected status code: {get_node_response.status_code}, response: {get_node_response.json()}"
    node_json = get_node_response.json()
    print(f"Get node response: {node_json}")



def test_create_edge():
    workflow = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    create_response = client.post("/workflows/", json=workflow)
    workflow_id = create_response.json()["id"]

    node1 = {
        "type": "Start",
        "status": "pending",
        "message": "Start node"
    }
    node2 = {
        "type": "End",
        "status": "pending",
        "message": "End node"
    }
    node1_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node1)
    node2_response = client.post(f"/workflows/{workflow_id}/nodes/", json=node2)

    edge = {
        "start_node_id": node1_response.json()["id"],
        "end_node_id": node2_response.json()["id"],
        "status": "Yes"
    }
    response = client.post(f"/workflows/{workflow_id}/edges/", json=edge)
    assert response.status_code == 200
    assert response.json()["status"] == edge["status"]

def test_get_all_edges():
    response = client.get("/edges/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)