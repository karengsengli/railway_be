# Train Transport Booking System

A comprehensive train booking system for Bangkok (BTS, MRT) and Osaka (JR West, Nankai) with advanced features including QR code generation, complex fare pricing, and ticket validation.

## Features

- **Multi-Region Support**: Bangkok and Osaka train systems
- **Complex Fare Pricing**: Route-based pricing with passenger type discounts
- **QR Code Tickets**: Generate and validate QR codes for tickets
- **Excel Integration**: Import/export fare rules via Excel files
- **4-Hour Validity**: Tickets are valid for 4 hours after booking
- **Mobile Scanner**: Web-based QR code scanner for ticket validation
- **RESTful API**: Complete FastAPI backend with async support

## Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: PostgreSQL (Neon hosted)
- **ORM**: SQLAlchemy with async support
- **Authentication**: JWT tokens
- **QR Codes**: qrcode library with PIL
- **Excel**: pandas + openpyxl
- **Frontend**: React + Tailwind CSS (planned)

## Project Structure

```
fastapi-project/
├── src/
│   ├── auth/                # Authentication module
│   ├── stations/            # Station management
│   ├── routes/              # Route management
│   ├── fare_rules/          # Complex fare pricing system
│   ├── tickets/             # Booking and ticket validation
│   ├── journeys/            # Journey planning
│   ├── config.py            # Global configuration
│   ├── database.py          # Database connection
│   ├── models.py            # Global models
│   └── main.py              # FastAPI application
├── requirements/
│   └── requirements.txt     # Python dependencies
├── schema.sql               # Database schema
├── seed_data.sql            # Sample data
├── qr_scanner_portal.html   # QR code scanner web portal
└── .env                     # Environment variables
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd fastapi-project
pip install -r requirements/requirements.txt
```

### 2. Database Setup

The project is configured to use Neon PostgreSQL. The connection is already set up in `.env`.

```bash
# Initialize database with schema
psql $DATABASE_URL -f schema.sql

# Load seed data
psql $DATABASE_URL -f seed_data.sql
```

### 3. Environment Variables

Update `.env` file with your settings:

```env
DATABASE_URL=postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 4. Run the Application

```bash
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Key API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Stations
- `GET /api/stations/` - List all stations
- `GET /api/stations/search?q={query}` - Search stations
- `GET /api/stations/line/{line_id}` - Get stations by line

### Fare Rules
- `GET /api/fare-rules/fare-matrix/{line_id}` - Get fare matrix for a line
- `POST /api/fare-rules/calculate-fare/` - Calculate fare for specific route
- `GET /api/fare-rules/fare-matrix/{line_id}/export` - Export fare matrix to Excel
- `POST /api/fare-rules/fare-matrix/{line_id}/import` - Import fare matrix from Excel

### Tickets
- `POST /api/tickets/book` - Book a new ticket
- `POST /api/tickets/validate` - Validate a ticket by QR code
- `POST /api/tickets/use/{ticket_id}` - Use/consume a ticket
- `GET /api/tickets/my-tickets` - Get user's tickets

## QR Code Scanner

Open `qr_scanner_portal.html` in a web browser to access the ticket validation portal. Features:
- Camera-based QR code scanning
- Manual ticket ID entry
- Real-time ticket validation
- Ticket usage tracking

## Database Schema

### Key Tables

1. **regions** - Geographic regions (Bangkok, Osaka)
2. **train_companies** - Train operators (BTS, MRT, JR West, Nankai)
3. **train_lines** - Train lines with colors and codes
4. **stations** - Individual stations with coordinates
5. **fare_rules** - Complex pricing matrix by route and passenger type
6. **tickets** - Booking records with QR codes
7. **ticket_segments** - Individual journey segments

### Pricing System

The fare system supports:
- **Route-based pricing**: Different prices for different station pairs
- **Passenger types**: Adult, Child, Senior, Member with different discounts
- **Peak hour multipliers**: Higher prices during rush hours
- **Validity periods**: Time-based fare rule validity

## Sample Data

The system includes sample data for:

### Bangkok
- **BTS Sukhumvit Line**: Mo Chit to Bearing (23 stations)
- **BTS Silom Line**: National Stadium to Bang Wa (13 stations)
- **MRT Blue Line**: Basic stations
- **MRT Purple Line**: Basic stations

### Osaka
- **JR Osaka Loop Line**: Major stations
- **Nankai Main Line**: Namba to Kansai Airport

## Booking Flow

1. User selects origin and destination stations
2. System calculates fare based on passenger types and time
3. QR code ticket generated (valid for 4 hours)
4. User presents QR code at station
5. Staff scans QR code to validate and use ticket

## Excel Integration

Fare rules can be managed via Excel:

1. **Export**: Download current fare matrix as Excel file
2. **Edit**: Modify prices in Excel
3. **Import**: Upload updated Excel file to bulk update fares

Excel format:
```
From Station | To Station | Adult Price | Child Price | Senior Price | Member Price
Mo Chit      | Asok       | 44.00       | 22.00       | 30.00        | 39.60
Mo Chit      | Siam       | 34.00       | 17.00       | 23.00        | 30.60
```

## Deployment

### Docker (Optional)

```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements/requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env .

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **Security**: Change SECRET_KEY in production
2. **Database**: Use connection pooling for high load
3. **Caching**: Add Redis for fare calculation caching
4. **Monitoring**: Add logging and health checks
5. **SSL**: Use HTTPS in production

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## License

MIT License - See LICENSE file for details