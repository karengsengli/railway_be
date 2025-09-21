# ThakhinMala Train Transport Booking System - Claude Context

## Project Overview
This is a comprehensive train booking system for Bangkok (BTS, MRT) and Osaka (JR West, Nankai) with advanced features including QR code generation, complex fare pricing, and ticket validation.

## Tech Stack
- **Backend**: FastAPI, Python 3.8+
- **Database**: PostgreSQL (Neon hosted)
- **ORM**: SQLAlchemy with async support
- **Authentication**: JWT tokens
- **QR Codes**: qrcode library with PIL
- **Excel**: pandas + openpyxl
- **Frontend**: React + Tailwind CSS (planned)

## Key Features
- Multi-region support (Bangkok & Osaka)
- Complex fare pricing with passenger type discounts
- QR code ticket generation and validation
- Excel import/export for fare rules
- 4-hour ticket validity
- Mobile QR scanner portal
- RESTful API with async support

## Project Structure
```
fastapi-project/
├── src/                        # Main application code
│   ├── auth/                   # Authentication module
│   ├── stations/               # Station management
│   ├── routes/                 # Route management
│   ├── fare_rules/             # Complex fare pricing system
│   ├── tickets/                # Booking and ticket validation
│   ├── journeys/               # Journey planning
│   ├── config.py               # Global configuration
│   ├── database.py             # Database connection
│   ├── models.py               # Global models
│   └── main.py                 # FastAPI application
├── admin-panel/                # Admin interface
├── user-website/               # User frontend
├── requirements/               # Python dependencies
├── schema.sql                  # Database schema
├── seed_data.sql               # Sample data
├── qr_scanner_portal.html      # QR code scanner
└── .env                        # Environment variables
```

## Database
- **Host**: Neon PostgreSQL
- **Connection**: Already configured in .env
- **Key Tables**: regions, train_companies, train_lines, stations, fare_rules, tickets, ticket_segments

## Common Commands
```bash
# Start the server
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Install dependencies
pip install -r requirements/requirements.txt

# Database operations
python create_tables.py
python seed_database.py
python database_reset_and_seed.py

# Data import scripts
python import_transit_data.py
python insert_bts_stations.py
python generate_route_segments.py
```

## API Endpoints
- **Swagger UI**: http://localhost:8000/docs
- **Base URL**: http://localhost:8000/api/

### Key Endpoints:
- Authentication: `/api/auth/register`, `/api/auth/login`
- Stations: `/api/stations/`, `/api/stations/search`
- Fare Rules: `/api/fare-rules/calculate-fare/`
- Tickets: `/api/tickets/book`, `/api/tickets/validate`

### Enhanced Route Management Endpoints:
- **Line Station Management**:
  - `POST /api/route-segments/lines/{line_id}/stations/` - Add station to line with order
  - `GET /api/route-segments/lines/{line_id}/stations/` - Get ordered stations for line
  - `PUT /api/route-segments/station-orders/{order_id}/move-up/` - Move station up
  - `PUT /api/route-segments/station-orders/{order_id}/move-down/` - Move station down
  - `PUT /api/route-segments/station-orders/{order_id}/position/{new_position}` - Set specific position

- **Route Connections**:
  - `POST /api/route-segments/lines/{line_id}/connections/` - Create route connection
  - `GET /api/route-segments/lines/{line_id}/connections/` - Get line connections
  - `POST /api/route-segments/lines/{line_id}/connections/auto-generate/` - Auto-generate connections

- **Interchange Management**:
  - `POST /api/route-segments/interchanges/` - Create interchange point
  - `GET /api/route-segments/interchanges/` - List interchange points
  - `POST /api/route-segments/interchanges/{id}/transfers/` - Create transfer route
  - `GET /api/route-segments/interchanges/{id}/transfers/` - Get transfer routes

- **Pathfinding (Your Custom Algorithm)**:
  - `GET /api/route-segments/pathfinding/graph/` - Get graph for your algorithm
  - `GET /api/route-segments/pathfinding/routes/` - Find routes between stations
  - `POST /api/route-segments/pathfinding/find-journey/` - Use your exact find_journey algorithm
  - `GET /api/route-segments/pathfinding/validate-connectivity/` - Validate graph connectivity

## Recent Work & Files
Based on file timestamps, recent work includes:
- `generate_route_segments.py` (Sep 19) - Route segment generation
- `insert_bts_stations.py` (Sep 19) - BTS station data import
- `cleanup_unused_tables.py` (Sep 19) - Database cleanup
- `create_route_segment_tables.py` (Sep 19) - Route segment table creation

### Latest Implementation (Current Session):
**Enhanced Route Management System** - Complete CRUD system for managing train line routes with:

#### Backend Implementation ✅
- **Station Ordering System**: Sortable up/down functionality for stations within train lines
- **Route Connections**: Direct connections between adjacent stations with distance/duration
- **Interchange Points**: Management of intersection points between different train lines
- **Transfer Routes**: Walking connections between lines at interchange stations
- **Custom Pathfinding**: Graph generation compatible with user's custom pathfinding algorithm

#### Admin Panel UI Implementation ✅
- **RouteManagementSystem**: Main component with tabbed interface (http://localhost:3001/route-management)
- **StationOrderingManager**: Add stations to lines, drag-and-drop reordering with ↑/↓ buttons
- **RouteConnectionsManager**: Create connections between stations (distance/duration), auto-generate feature
- **InterchangePointsManager**: Create interchange points and transfer routes between lines
- **PathfindingTestManager**: Test your custom find_journey algorithm, graph analysis, connectivity validation

#### Key Features Delivered:
- ✅ **Station Management**: Add stations to lines with ordering positions (1, 2, 3...)
- ✅ **Sortable Interface**: Move stations up/down with buttons, automatic reordering
- ✅ **Route Connections**: Define Khu Khot → Yaek Kor Pon Aor (1km, 4min) connections
- ✅ **Interchange System**: Create Siam-Sukhumvit → Siam-Silom walking transfers (5min)
- ✅ **Auto-Generation**: Automatically create connections between consecutive stations
- ✅ **Pathfinding Testing**: Test routes with your exact algorithm format
- ✅ **Graph Validation**: Check connectivity, identify missing transfers, isolated nodes

## Current State
- Database schema established with complex fare pricing system
- Core API endpoints implemented
- QR code generation and validation working
- Sample data for Bangkok BTS/MRT and Osaka JR/Nankai lines
- Excel import/export functionality for fare management
- **FIXED**: Backend server running successfully on port 8000 (using `python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000` from project root)
- **FIXED**: Admin panel running successfully on port 3003 with route management system working
- **RESOLVED**: "lines.map is not a function" error fixed by properly handling API response structure (`data.lines` instead of `data`)
- **FIXED**: Route-segments endpoints now working via `route_segments_simple.py` router
- **WORKING**: Station ordering functionality in admin panel now functional

## Implementation Status & Todo List

### ✅ COMPLETED FEATURES
1. **Core Infrastructure**
   - FastAPI backend with async SQLAlchemy
   - PostgreSQL database (Neon hosted)
   - JWT authentication system
   - CORS configuration for cross-origin requests

2. **Data Management**
   - Region, company, line, and station CRUD operations
   - Complex fare pricing system with passenger type discounts
   - Excel import/export for fare rules
   - QR code ticket generation and validation

3. **Route Management Foundation**
   - Basic route-segments API endpoints
   - Station ordering functionality (minimal implementation)
   - Admin panel UI with tabbed interface
   - Line and station management interface

### 🚧 IN PROGRESS
1. **Route Management Enhancement**
   - Database integration for route-segments endpoints
   - Real-time station reordering with persistence
   - Route connection management between adjacent stations

### 📋 PENDING IMPLEMENTATION

#### Phase 1: Core Route Management (HIGH PRIORITY)
1. **Database Schema Validation**
   - Verify all route_segments tables exist in Neon DB
   - Run database migration scripts if needed
   - Test table relationships and constraints

2. **Enhanced Station Management**
   - Replace mock endpoints with real database queries
   - Implement station position reordering (move up/down)
   - Add station deletion and modification
   - Validate unique station positions per line

3. **Route Connections**
   - Direct connections between adjacent stations
   - Distance and duration calculation
   - Auto-generation of connections between consecutive stations
   - Bidirectional route support

#### Phase 2: Advanced Features (MEDIUM PRIORITY)
4. **Interchange Management**
   - Transfer points between different lines
   - Walking connections and transfer times
   - Transfer cost calculation
   - Platform and accessibility information

5. **Pathfinding Integration**
   - Graph generation from route data
   - Custom pathfinding algorithm implementation
   - Multi-line journey planning
   - Alternative route suggestions

6. **Data Quality & Validation**
   - Input validation for all route data
   - Consistency checks between stations and routes
   - Error handling and user feedback
   - Data integrity constraints

#### Phase 3: User Experience (LOW PRIORITY)
7. **Admin Panel Enhancements**
   - Drag-and-drop station reordering
   - Visual route mapping
   - Bulk operations for route management
   - Real-time preview of changes

8. **Import/Export Features**
   - CSV/Excel import for route data
   - Route data export functionality
   - Template generation for bulk imports
   - Migration tools for existing data

#### Phase 4: Testing & Optimization
9. **Testing Suite**
   - Unit tests for all route management functions
   - Integration tests for API endpoints
   - E2E tests for admin panel functionality
   - Performance testing for large datasets

10. **Performance Optimization**
    - Database query optimization
    - Caching for frequently accessed routes
    - Pagination for large station lists
    - API response optimization

### 🔧 TECHNICAL DEBT & FIXES NEEDED
1. **Route-Segments Endpoints**: Currently using minimal mock implementation in `route_segments_simple.py`
2. **Database Integration**: Need to replace mock responses with actual database queries
3. **Error Handling**: Add comprehensive error handling and validation
4. **API Documentation**: Update OpenAPI specs for new endpoints
5. **Code Organization**: Consolidate route management logic into proper modules

## 🚀 QUICK START FOR NEXT SESSION

### Current Working Setup
- **Backend**: `python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000` (from project root)
- **Admin Panel**: Running on port 3003 - http://localhost:3003/route-management
- **Route Segments API**: Working via `src/route_segments_simple.py` router

### Immediate Next Steps (Priority Order)
1. **Replace Mock Endpoints**: Update `route_segments_simple.py` with real database queries
2. **Test Database Schema**: Verify `line_station_orders` and related tables exist
3. **Add Station Reordering**: Implement move up/down functionality with database persistence
4. **Add Validation**: Input validation and error handling for all route operations

### Key Files to Focus On
- `src/route_segments_simple.py` - Current minimal implementation needing database integration
- `src/route_segments/models.py` - Database models for route management
- `admin-panel/src/components/StationOrderingManager.tsx` - Frontend station ordering component
- `admin-panel/src/components/RouteManagementSystem.tsx` - Main route management interface

### Database Tables Needed
- `line_station_orders` - Station ordering within lines
- `route_connections` - Direct connections between stations
- `interchange_points` - Transfer points between lines
- `interchange_transfers` - Transfer routes at interchange points

### Testing Checklist
- [ ] Can add stations to a line
- [ ] Can reorder stations (move up/down)
- [ ] Can view route management data
- [ ] Admin panel loads without errors
- [ ] API endpoints return proper JSON responses

## Development Notes
- Uses async SQLAlchemy for database operations
- JWT authentication implemented
- Complex fare calculation based on route, passenger type, and time
- 4-hour ticket validity system
- QR code contains encrypted ticket information

## Environment
- **Working Directory**: C:\Users\mala\Desktop\Thakhin Mala\ThakhinMala\fastapi-project
- **Python**: Virtual environment in venv/
- **Database**: Neon PostgreSQL (connection in .env)

## Testing
- Test files in tests/ directory
- QR scanner portal for manual testing
- API testing via Swagger UI

---
*This context file helps Claude understand the project state and avoid repeated explanations. Update this file as the project evolves.*