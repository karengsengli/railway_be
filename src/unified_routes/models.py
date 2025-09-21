from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, DateTime, Text, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base
import enum

class TransportTypeEnum(enum.Enum):
    train = "train"
    walk = "walk"

class RouteStatusEnum(enum.Enum):
    active = "active"
    inactive = "inactive"
    maintenance = "maintenance"

class UnifiedRoute(Base):
    __tablename__ = "unified_routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    line_id = Column(Integer, ForeignKey("train_lines.id"), nullable=False)
    status = Column(Enum(RouteStatusEnum), default=RouteStatusEnum.active)
    total_distance = Column(DECIMAL(10, 2), nullable=False, default=0)
    total_duration = Column(Integer, nullable=False, default=0)  # in minutes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    line = relationship("TrainLine")
    segments = relationship("RouteSegment", back_populates="route", cascade="all, delete-orphan")

class RouteSegment(Base):
    __tablename__ = "route_segments"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("unified_routes.id"), nullable=False)
    from_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    to_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    transport_type = Column(Enum(TransportTypeEnum), default=TransportTypeEnum.train)
    distance_km = Column(DECIMAL(10, 2), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False)  # Order of this segment in the route
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    route = relationship("UnifiedRoute", back_populates="segments")
    from_station = relationship("Station", foreign_keys=[from_station_id])
    to_station = relationship("Station", foreign_keys=[to_station_id])