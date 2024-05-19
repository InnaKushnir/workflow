from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates
from datetime import datetime

Base = declarative_base()


class NodeType(str, Enum):
    start = 'Start'
    message = 'Message'
    condition = 'Condition'
    end = 'End'


class NodeStatus(str, Enum):
    pending = 'pending'
    sent = 'sent'
    opened = 'opened'


class EdgeStatus(str, Enum):
    yes = 'Yes'
    no = 'No'


class Workflow(Base):
    __tablename__ = "workflow"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    nodes = relationship("Node", back_populates="workflow")
    edges = relationship("Edge", back_populates="workflow")


class Node(Base):
    __tablename__ = "node"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey('workflow.id'))
    type = Column(SQLAEnum(NodeType))
    status = Column(SQLAEnum(NodeStatus), nullable=True)
    message = Column(String, nullable=True)

    workflow = relationship("Workflow", back_populates="nodes")
    outgoing_edges = relationship("Edge", foreign_keys="[Edge.start_node_id]", back_populates="start_node")
    incoming_edges = relationship("Edge", foreign_keys="[Edge.end_node_id]", back_populates="end_node")

    # @validates('type')
    # def validate_type(self, key, type):
    #     if type == NodeType.message and not self.message:
    #         raise ValueError("Message Node must have a message.")
    #     return type


class Edge(Base):
    __tablename__ = "edge"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey('workflow.id'))
    start_node_id = Column(Integer, ForeignKey('node.id'))
    end_node_id = Column(Integer, ForeignKey('node.id'))
    status = Column(String, nullable=True)

    workflow = relationship("Workflow", back_populates="edges")
    start_node = relationship("Node", foreign_keys=[start_node_id], back_populates="outgoing_edges")
    end_node = relationship("Node", foreign_keys=[end_node_id], back_populates="incoming_edges")

    # @staticmethod
    # def validate_start_node(start_node):
    #     if start_node.type == NodeType.start:
    #         if len(start_node.outgoing_edges) >= 1:
    #             raise ValueError("Start Node can only have one outgoing edge.")
    #         if len(start_node.incoming_edges) > 0:
    #             raise ValueError("Start Node cannot have incoming edges.")
    #     elif start_node.type == NodeType.message:
    #         if len(start_node.outgoing_edges) >= 1:
    #             raise ValueError("Message Node can only have one outgoing edge.")
    #     elif start_node.type == NodeType.condition:
    #         if len(start_node.outgoing_edges) >= 2:
    #             raise ValueError("Condition Node can only have two outgoing edges (Yes and No).")
    #     elif start_node.type == NodeType.end:
    #         if len(start_node.outgoing_edges) > 0:
    #             raise ValueError("End Node cannot have outgoing edges.")
    #
    # @staticmethod
    # def validate_end_node(end_node):
    #     if end_node.type == NodeType.start:
    #         raise ValueError("Start Node cannot be an end node.")
    #     elif end_node.type == NodeType.end:
    #         if len(end_node.outgoing_edges) > 0:
    #             raise ValueError("End Node cannot have outgoing edges.")


