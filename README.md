#### Workflow-service

REST ful API for Workflow service.
This project is a FastAPI-based API for managing workflows using graph concepts. The system allows the creation of four types of nodes and includes API development with FastAPI and Pydantic for handling web requests, integration with the networkX library for graph management, and the implementation of an algorithm to determine the path from the start node to the end node.


#### Features


- **Create, Update, Delete Workflows**: Endpoints to manage workflows.
- **Node Management**: Endpoints to add new nodes (Start, Message, Condition, End) to a workflow.
- **Node Configuration**: Ability to change parameters for nodes or delete nodes.
- **Run Workflow**: Endpoint to initialize and run a selected workflow, returning the detailed path from the Start node to the End node, or an error if no valid path exists with a description of the reason.

## API Endpoints

### Create, Update, Delete Workflows

Endpoints for managing workflows, allowing users to create, update, and delete workflows.

### Node Management

- **Add Node**: Endpoint to add new nodes to the workflow. The supported node types are Start, Message, Condition, and End.
- Use such condition_expression "message.startswith('test')", "message == 'Hello World'" or other.

### Node Configuration

- **Update Node**: Endpoint to modify the parameters of existing nodes.
- **Delete Node**: Endpoint to remove nodes from the workflow.

### Run Workflow

- **Initialize and Run Workflow**: Endpoint to start a specific workflow and find the shortest path from the Start node to the End node using the networkX library. If no valid path is found, the endpoint will return an error message with a description of the issue.

#### Installation
##### Python3 must be already installed.
```
git clone https://github.com/InnaKushnir/workflow
cd workflow
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
```


#### Run the following necessary commands
```
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

* Starting the project is done with the command.
```
uvicorn main:app --reload
```

