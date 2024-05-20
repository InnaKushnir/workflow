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


