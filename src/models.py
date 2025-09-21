from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean, Text, ForeignKey, BIGINT, JSON, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BIGINT, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user_roles = relationship("UserHasRole", back_populates="user")
    tickets = relationship("Ticket", back_populates="user")
    journeys = relationship("Journey", back_populates="user")

class Role(Base):
    __tablename__ = "roles"

    id = Column(BIGINT, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user_roles = relationship("UserHasRole", back_populates="role")

class UserHasRole(Base):
    __tablename__ = "user_has_roles"

    id = Column(BIGINT, primary_key=True, index=True)
    user_id = Column(BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(BIGINT, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

    __table_args__ = (UniqueConstraint('user_id', 'role_id'),)

class Region(Base):
    __tablename__ = "regions"

    id = Column(BIGINT, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    timezone = Column(String(50), default="UTC")
    currency = Column(String(10), default="USD")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    train_companies = relationship("TrainCompany", back_populates="region")

class TrainCompany(Base):
    __tablename__ = "train_companies"

    id = Column(BIGINT, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    status = Column(String(50), default="active")
    region_id = Column(BIGINT, ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False)
    website = Column(String(255))
    contact_info = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    region = relationship("Region", back_populates="train_companies")
    train_lines = relationship("TrainLine", back_populates="company")

class TrainLine(Base):
    __tablename__ = "train_lines"

    id = Column(BIGINT, primary_key=True, index=True)
    company_id = Column(BIGINT, ForeignKey("train_companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    color = Column(String(20))
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    company = relationship("TrainCompany", back_populates="train_lines")
    stations = relationship("Station", back_populates="line")
    routes = relationship("Route", back_populates="line")
    fare_rules = relationship("FareRule", back_populates="line")
    ticket_segments = relationship("TicketSegment", back_populates="line")
    train_route = relationship("TrainRoute", back_populates="line", uselist=False)  # One-to-one

class Station(Base):
    __tablename__ = "stations"

    id = Column(BIGINT, primary_key=True, index=True)
    line_id = Column(BIGINT, ForeignKey("train_lines.id"))
    name = Column(String(255), nullable=False)
    code = Column(String(10))
    lat = Column(DECIMAL(10, 6))
    long = Column(DECIMAL(10, 6), name="long")  # Database column name is "long"
    is_interchange = Column(Boolean, default=False)
    platform_count = Column(Integer)
    status = Column(String(50), default="active")
    zone_number = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    line = relationship("TrainLine", back_populates="stations")
    routes_from = relationship("Route", foreign_keys="Route.from_station_id", back_populates="from_station")
    routes_to = relationship("Route", foreign_keys="Route.to_station_id", back_populates="to_station")

class Route(Base):
    __tablename__ = "routes"

    id = Column(BIGINT, primary_key=True, index=True)
    line_id = Column(BIGINT, ForeignKey("train_lines.id"), nullable=False)
    from_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)
    to_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)
    transport_type = Column(String(50), nullable=False, default="train")
    distance_km = Column(DECIMAL(8, 2))
    duration_minutes = Column(Integer)
    station_count = Column(Integer)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    line = relationship("TrainLine", back_populates="routes")
    from_station = relationship("Station", foreign_keys=[from_station_id])
    to_station = relationship("Station", foreign_keys=[to_station_id])
    journey_segments = relationship("JourneySegment", back_populates="route")

    __table_args__ = (UniqueConstraint('line_id', 'from_station_id', 'to_station_id'),)

class PassengerType(Base):
    __tablename__ = "passenger_types"

    id = Column(BIGINT, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    discount_percentage = Column(DECIMAL(5, 2), default=0.00)
    age_min = Column(Integer)
    age_max = Column(Integer)
    requires_proof = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    fare_rules = relationship("FareRule", back_populates="passenger_type")
    ticket_segments = relationship("TicketSegment", back_populates="passenger_type")

class FareRule(Base):
    __tablename__ = "fare_rules"

    id = Column(BIGINT, primary_key=True, index=True)
    line_id = Column(BIGINT, ForeignKey("train_lines.id"), nullable=False)
    from_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)
    to_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)
    passenger_type_id = Column(BIGINT, ForeignKey("passenger_types.id"), nullable=False)
    base_price = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(10), default="THB")
    valid_from = Column(Date, default=func.current_date())
    valid_to = Column(Date)
    peak_hour_multiplier = Column(DECIMAL(4, 2), default=1.00)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    line = relationship("TrainLine", back_populates="fare_rules")
    from_station = relationship("Station", foreign_keys=[from_station_id])
    to_station = relationship("Station", foreign_keys=[to_station_id])
    passenger_type = relationship("PassengerType", back_populates="fare_rules")

    __table_args__ = (UniqueConstraint('line_id', 'from_station_id', 'to_station_id', 'passenger_type_id', 'valid_from'),)

class Journey(Base):
    __tablename__ = "journeys"

    id = Column(BIGINT, primary_key=True, index=True)
    user_id = Column(BIGINT, ForeignKey("users.id"))
    from_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)
    to_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)
    total_cost = Column(DECIMAL(10, 2))
    passenger_count = Column(JSON)
    status = Column(String(50), default="planned")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="journeys")
    from_station = relationship("Station", foreign_keys=[from_station_id])
    to_station = relationship("Station", foreign_keys=[to_station_id])
    journey_segments = relationship("JourneySegment", back_populates="journey", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="journey")

class JourneySegment(Base):
    __tablename__ = "journey_segments"

    id = Column(BIGINT, primary_key=True, index=True)
    journey_id = Column(BIGINT, ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    route_id = Column(BIGINT, ForeignKey("routes.id"), nullable=False)
    segment_order = Column(Integer, nullable=False)
    from_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)
    to_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)
    cost = Column(DECIMAL(10, 2))
    instructions = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    journey = relationship("Journey", back_populates="journey_segments")
    route = relationship("Route", back_populates="journey_segments")
    from_station = relationship("Station", foreign_keys=[from_station_id])
    to_station = relationship("Station", foreign_keys=[to_station_id])

class PaymentType(Base):
    __tablename__ = "payment_types"

    id = Column(BIGINT, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)
    status = Column(String(50), default="active")
    processing_fee = Column(DECIMAL(10, 2), default=0.00)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    tickets = relationship("Ticket", back_populates="payment_type")

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(BIGINT, primary_key=True, index=True)
    ticket_unique_string = Column(String(100), unique=True, nullable=False, index=True)
    qr_code = Column(Text)
    user_id = Column(BIGINT, ForeignKey("users.id"), nullable=False)
    journey_id = Column(BIGINT, ForeignKey("journeys.id"))
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    paid_currency = Column(String(10), default="THB")
    paid_amount = Column(DECIMAL(10, 2))
    passenger_details = Column(JSON)
    status = Column(String(50), default="pending")
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    issued_at = Column(DateTime, default=func.now())
    used_at = Column(DateTime)
    payment_type_id = Column(BIGINT, ForeignKey("payment_types.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="tickets")
    journey = relationship("Journey", back_populates="tickets")
    payment_type = relationship("PaymentType", back_populates="tickets")
    ticket_segments = relationship("TicketSegment", back_populates="ticket", cascade="all, delete-orphan")

class TicketSegment(Base):
    __tablename__ = "ticket_segments"

    id = Column(BIGINT, primary_key=True, index=True)
    ticket_id = Column(BIGINT, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    from_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)
    to_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)
    line_id = Column(BIGINT, ForeignKey("train_lines.id"), nullable=False)
    passenger_type_id = Column(BIGINT, ForeignKey("passenger_types.id"), nullable=False)
    fare_amount = Column(DECIMAL(10, 2), nullable=False)
    segment_order = Column(Integer, nullable=False)
    status = Column(String(50), default="valid")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    ticket = relationship("Ticket", back_populates="ticket_segments")
    from_station = relationship("Station", foreign_keys=[from_station_id])
    to_station = relationship("Station", foreign_keys=[to_station_id])
    line = relationship("TrainLine", back_populates="ticket_segments")
    passenger_type = relationship("PassengerType", back_populates="ticket_segments")

# Train Route Management Models
class TrainRoute(Base):
    """
    One route per train line - represents the complete route for a line
    e.g., "Sukhumvit Line Route" or "Silom Line Route"
    """
    __tablename__ = "train_routes"

    id = Column(BIGINT, primary_key=True, index=True)
    line_id = Column(BIGINT, ForeignKey("train_lines.id"), unique=True, nullable=False)  # One-to-one with train line
    name = Column(String(255), nullable=False)  # e.g., "Sukhumvit Line Route"
    description = Column(Text)
    total_distance_km = Column(DECIMAL(8, 2))
    total_duration_minutes = Column(Integer)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    line = relationship("TrainLine", back_populates="train_route")
    route_segments = relationship("RouteSegment", back_populates="train_route", order_by="RouteSegment.segment_order")

class RouteSegment(Base):
    """
    Individual station-to-station connections within a route
    e.g., "Khu Khot -> Yaek Kor Pon Aor"
    """
    __tablename__ = "route_segments"

    id = Column(BIGINT, primary_key=True, index=True)
    train_route_id = Column(BIGINT, ForeignKey("train_routes.id"), nullable=False)
    from_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)
    to_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)
    segment_order = Column(Integer, nullable=False)  # For sorting (1, 2, 3, ...)
    distance_km = Column(DECIMAL(8, 2), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    transport_type = Column(String(50), default="train")  # train, bus, walk, etc.
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    train_route = relationship("TrainRoute", back_populates="route_segments")
    from_station = relationship("Station", foreign_keys=[from_station_id])
    to_station = relationship("Station", foreign_keys=[to_station_id])

    # Ensure unique ordering within each route
    __table_args__ = (
        UniqueConstraint('train_route_id', 'segment_order'),
        UniqueConstraint('train_route_id', 'from_station_id', 'to_station_id'),
    )

# Intersection Models for Train Line Transfers
class IntersectionPoint(Base):
    """
    Physical intersection points where multiple train lines meet
    e.g., "Siam Station" connects BTS Sukhumvit and BTS Silom lines
    """
    __tablename__ = "intersection_points"

    id = Column(BIGINT, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Siam Interchange"
    description = Column(Text)  # Optional description of the intersection
    lat = Column(DECIMAL(10, 6))  # Latitude
    long = Column(DECIMAL(10, 6))  # Longitude
    station_codes = Column(JSON)  # List of station codes that meet here
    accessibility_features = Column(JSON)  # Elevator, escalator, wheelchair access
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    intersection_segments = relationship("IntersectionSegment", back_populates="intersection_point")

class IntersectionSegment(Base):
    """
    Transfer segments between different train lines at intersection points
    e.g., "Walk from BTS Siam (Sukhumvit) to BTS Siam (Silom)" - 0.2km, 5min walk
    """
    __tablename__ = "intersection_segments"

    id = Column(BIGINT, primary_key=True, index=True)
    intersection_point_id = Column(BIGINT, ForeignKey("intersection_points.id"), nullable=False)
    from_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)  # Station on first line
    to_station_id = Column(BIGINT, ForeignKey("stations.id"), nullable=False)    # Station on second line
    from_line_id = Column(BIGINT, ForeignKey("train_lines.id"), nullable=False)  # First train line
    to_line_id = Column(BIGINT, ForeignKey("train_lines.id"), nullable=False)    # Second train line
    distance_km = Column(DECIMAL(8, 2), nullable=False)  # Transfer distance (e.g., 0.2 km)
    duration_minutes = Column(Integer, nullable=False)   # Transfer time (e.g., 5 minutes)
    transport_type = Column(String(50), default="walk")  # walk, elevator, escalator, shuttle
    transfer_cost = Column(DECIMAL(10, 2), default=0.00)  # Additional cost for transfer (usually 0)
    direction_instructions = Column(Text)  # "Exit at platform 2, follow signs to Silom Line"
    accessibility_notes = Column(Text)     # "Elevator available", "Wheelchair accessible"
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    intersection_point = relationship("IntersectionPoint", back_populates="intersection_segments")
    from_station = relationship("Station", foreign_keys=[from_station_id])
    to_station = relationship("Station", foreign_keys=[to_station_id])
    from_line = relationship("TrainLine", foreign_keys=[from_line_id])
    to_line = relationship("TrainLine", foreign_keys=[to_line_id])

    # Ensure unique transfers between stations at intersection points
    __table_args__ = (
        UniqueConstraint('intersection_point_id', 'from_station_id', 'to_station_id'),
    )