-- ================================
-- Drop existing tables if they exist
-- ================================
DROP TABLE IF EXISTS ticket_routes CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS payment_types CASCADE;
DROP TABLE IF EXISTS journey_segments CASCADE;
DROP TABLE IF EXISTS journeys CASCADE;
DROP TABLE IF EXISTS fare_rules CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS stations CASCADE;
DROP TABLE IF EXISTS train_lines CASCADE;
DROP TABLE IF EXISTS train_companies CASCADE;
DROP TABLE IF EXISTS regions CASCADE;
DROP TABLE IF EXISTS user_has_roles CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ================================
-- Users & Roles
-- ================================
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_has_roles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, role_id)
);

-- ================================
-- Regions / Systems / Stations
-- ================================
CREATE TABLE regions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE train_companies (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    region_id BIGINT NOT NULL REFERENCES regions(id),
    website VARCHAR(255),
    contact_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE train_lines (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES train_companies(id),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(10) NOT NULL,
    color VARCHAR(20),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, code)
);

CREATE TABLE stations (
    id BIGSERIAL PRIMARY KEY,
    line_id BIGINT REFERENCES train_lines(id),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(20),
    lat DECIMAL(10,6),
    lng DECIMAL(10,6),
    station_order INTEGER,
    status VARCHAR(50) DEFAULT 'active',
    facilities JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- Routes & Complex Fare System
-- ================================
CREATE TABLE routes (
    id BIGSERIAL PRIMARY KEY,
    line_id BIGINT NOT NULL REFERENCES train_lines(id),
    from_station_id BIGINT NOT NULL REFERENCES stations(id),
    to_station_id BIGINT NOT NULL REFERENCES stations(id),
    transport_type VARCHAR(50) NOT NULL DEFAULT 'train',
    distance_km DECIMAL(8,2),
    duration_minutes INT,
    station_count INT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(line_id, from_station_id, to_station_id)
);

-- Passenger types with discount rules
CREATE TABLE passenger_types (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    discount_percentage DECIMAL(5,2) DEFAULT 0.00,
    age_min INTEGER,
    age_max INTEGER,
    requires_proof BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Complex fare rules - supports route-based pricing matrix
CREATE TABLE fare_rules (
    id BIGSERIAL PRIMARY KEY,
    line_id BIGINT NOT NULL REFERENCES train_lines(id),
    from_station_id BIGINT NOT NULL REFERENCES stations(id),
    to_station_id BIGINT NOT NULL REFERENCES stations(id),
    passenger_type_id BIGINT NOT NULL REFERENCES passenger_types(id),
    base_price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'THB',
    valid_from DATE DEFAULT CURRENT_DATE,
    valid_to DATE,
    peak_hour_multiplier DECIMAL(4,2) DEFAULT 1.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(line_id, from_station_id, to_station_id, passenger_type_id, valid_from)
);

-- ================================
-- Journey Planning
-- ================================
CREATE TABLE journeys (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    from_station_id BIGINT NOT NULL REFERENCES stations(id),
    to_station_id BIGINT NOT NULL REFERENCES stations(id),
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    total_cost DECIMAL(10,2),
    passenger_count JSONB,
    status VARCHAR(50) DEFAULT 'planned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE journey_segments (
    id BIGSERIAL PRIMARY KEY,
    journey_id BIGINT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    route_id BIGINT NOT NULL REFERENCES routes(id),
    segment_order INT NOT NULL,
    from_station_id BIGINT NOT NULL REFERENCES stations(id),
    to_station_id BIGINT NOT NULL REFERENCES stations(id),
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    cost DECIMAL(10,2),
    instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- Tickets & Payments
-- ================================
CREATE TABLE payment_types (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    code VARCHAR(50) NOT NULL UNIQUE,
    status VARCHAR(50) DEFAULT 'active',
    processing_fee DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tickets (
    id BIGSERIAL PRIMARY KEY,
    ticket_unique_string VARCHAR(100) UNIQUE NOT NULL,
    qr_code TEXT,
    user_id BIGINT NOT NULL REFERENCES users(id),
    journey_id BIGINT REFERENCES journeys(id),
    total_amount DECIMAL(10,2) NOT NULL,
    paid_currency VARCHAR(10) DEFAULT 'THB',
    paid_amount DECIMAL(10,2),
    passenger_details JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    valid_from TIMESTAMP NOT NULL,
    valid_until TIMESTAMP NOT NULL,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP,
    payment_type_id BIGINT REFERENCES payment_types(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ticket_segments (
    id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    from_station_id BIGINT NOT NULL REFERENCES stations(id),
    to_station_id BIGINT NOT NULL REFERENCES stations(id),
    line_id BIGINT NOT NULL REFERENCES train_lines(id),
    passenger_type_id BIGINT NOT NULL REFERENCES passenger_types(id),
    fare_amount DECIMAL(10,2) NOT NULL,
    segment_order INT NOT NULL,
    status VARCHAR(50) DEFAULT 'valid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- Indexes for Performance
-- ================================
CREATE INDEX idx_stations_line_order ON stations(line_id, station_order);
CREATE INDEX idx_routes_from_to ON routes(from_station_id, to_station_id);
CREATE INDEX idx_fare_rules_lookup ON fare_rules(line_id, from_station_id, to_station_id, passenger_type_id);
CREATE INDEX idx_tickets_user_status ON tickets(user_id, status);
CREATE INDEX idx_tickets_qr_code ON tickets(ticket_unique_string);
CREATE INDEX idx_tickets_valid_period ON tickets(valid_from, valid_until);

-- ================================
-- Sample Data Insert
-- ================================

-- Insert regions
INSERT INTO regions (name, country, timezone, currency) VALUES
('Bangkok', 'Thailand', 'Asia/Bangkok', 'THB'),
('Osaka', 'Japan', 'Asia/Tokyo', 'JPY');

-- Insert passenger types
INSERT INTO passenger_types (name, description, discount_percentage, age_min, age_max, requires_proof) VALUES
('adult', 'Adult passenger', 0.00, 18, 64, FALSE),
('child', 'Child passenger', 50.00, 3, 17, TRUE),
('senior', 'Senior citizen', 30.00, 65, NULL, TRUE),
('member', 'Member with discount', 10.00, NULL, NULL, TRUE);

-- Insert payment types
INSERT INTO payment_types (name, code, status, processing_fee) VALUES
('Cash', 'CASH', 'active', 0.00),
('Credit Card', 'CREDIT', 'active', 2.50),
('Mobile Payment', 'MOBILE', 'active', 1.00),
('Transit Card', 'TRANSIT', 'active', 0.00);

-- Insert roles
INSERT INTO roles (name, description) VALUES
('admin', 'System administrator with full access'),
('operator', 'Train system operator'),
('customer', 'Regular customer'),
('staff', 'Station staff member');