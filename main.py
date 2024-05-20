import networkx as nx
from fastapi import FastAPI, Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from typing_extensions import Union
import matplotlib.pyplot as plt

from db import models
from typing import List
import schemas
from db.models import NodeType
from dependencies import get_db
from schemas import WorkflowCreate
from services import WorkflowService

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/workflows/", response_model=List[schemas.Workflow])
def get_all_workflow(workflow_service: WorkflowService = Depends()):
    return workflow_service.get_all_workflow()


@app.get("/workflows/{workflow_id}/", response_model=schemas.Workflow)
def get_workflow(workflow_id: Union[int, None] = None, workflow_service: WorkflowService = Depends()):
    db_workflow = workflow_service.get_workflow(workflow_id=workflow_id)

    if db_workflow is None:
        raise HTTPException(status_code=404, detail="Author not found")

    return db_workflow


@app.post("/workflows/", response_model=schemas.Workflow)
def create_workflow(workflow: schemas.WorkflowCreate, workflow_service: WorkflowService = Depends()):

    return workflow_service.create_workflow(workflow=workflow)


@app.post("/workflows/{workflow_id}/nodes/", response_model=schemas.Node)
def create_node(workflow_id: int, node: schemas.NodeCreate, node_service: WorkflowService = Depends()):
    return node_service.create_node(workflow_id, node)


@app.get("/nodes/", response_model=List[schemas.Node])
def get_all_nodes(nodes_service: WorkflowService = Depends()):
    return nodes_service.get_all_nodes()


@app.put("/nodes/{node_id}/", response_model=schemas.Node)
def update_node(node_id: int, node: schemas.NodeCreate, node_service: WorkflowService = Depends()):
    return node_service.update_node(node_id, node)


@app.delete("/nodes/{node_id}/", response_model=schemas.Node)
def delete_node(node_id: int, node_service: WorkflowService = Depends()):
    return node_service.delete_node(node_id)


@app.post("/workflows/{workflow_id}/edges/", response_model=schemas.Edge)
def create_edge(workflow_id: int, edge: schemas.EdgeCreate, edge_service: WorkflowService = Depends()):
    return edge_service.create_edge(workflow_id, edge)


@app.get("/edges/", response_model=List[schemas.Edge])
def get_all_edges(edge_service: WorkflowService = Depends()):
    return edge_service.get_all_edges()

@app.put("/edges/{edge_id}/", response_model=schemas.Edge)
def update_edge(edge_id: int, edge: schemas.EdgeCreate, edge_service: WorkflowService = Depends()):
    return edge_service.update_edge(edge_id, edge)


@app.delete("/edges/{edge_id}/", response_model=schemas.Edge)
def delete_edge(edge_id: int, edge_service: WorkflowService = Depends()):
    return edge_service.delete_edge(edge_id)


@app.post("/workflows/{workflow_id}/run/")
def run_workflow(workflow_id: int, workflow_service: WorkflowService = Depends()):
    workflow = workflow_service.get_workflow(workflow_id)
    G = nx.DiGraph()

    for node in workflow.nodes:
        G.add_node(node.id, type=node.type, status=node.status, message=node.message)

    for edge in workflow.edges:
        G.add_edge(edge.start_node_id, edge.end_node_id, status=edge.status)

    start_nodes = [node.id for node in workflow.nodes if node.type == NodeType.start]
    end_nodes = [node.id for node in workflow.nodes if node.type == NodeType.end]
    print(start_nodes, end_nodes)
    print(111)
    if not start_nodes:
        return {"error": "No start node found"}
    if not end_nodes:
        return {"error": "No end node found"}
    # plt.figure(figsize=(10, 6))
    # nx.draw(G, with_labels=True)
    # plt.show()

    try:
        path = None
        for start_node in start_nodes:
            print(start_node)
            for end_node in end_nodes:
                print(end_node)
                path = nx.shortest_path(G, source=start_node, target=end_node)
                print(222, path)
                if path:
                    break
            if path:
                break
        if not path:
            return {"error": "No path found from start to end node"}

        detailed_path = []
        for node_id in path:
            node = workflow_service.db.query(models.Node).filter(models.Node.id == node_id).first()
            detailed_path.append({
                "id": node.id,
                "type": node.type,
                "status": node.status,
                "message": node.message
            })

        return {"path": detailed_path}
    except nx.NetworkXNoPath:
        return {"error": "No path found from start to end node"}


