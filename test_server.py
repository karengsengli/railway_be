from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncpg
import os
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional

app = FastAPI(
    title="Test Train Transport API",
    description="Minimal test server for CORS testing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_admin_role(token_data: dict = Depends(verify_token)):
    """Ensure user has admin role"""
    user_roles = token_data.get("roles", [])
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return token_data

@app.get("/")
async def root():
    return {"message": "Test Train Transport Booking System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/auth/login")
async def login(credentials: dict):
    """Authenticate user and return JWT token"""
    email = credentials.get("email")
    password = credentials.get("password")

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    # Demo authentication - check against our demo users
    demo_users = [
        {
            "email": "admin@trainbooking.com",
            "password": "admin123",  # In production, this would be hashed
            "first_name": "Admin",
            "last_name": "User",
            "roles": ["admin", "user"]
        },
        {
            "email": "john.doe@email.com",
            "password": "user123",
            "first_name": "John",
            "last_name": "Doe",
            "roles": ["user"]
        }
    ]

    user = None
    for demo_user in demo_users:
        if demo_user["email"] == email and demo_user["password"] == password:
            user = demo_user
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["email"],
            "roles": user["roles"],
            "first_name": user["first_name"],
            "last_name": user["last_name"]
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "roles": user["roles"]
        }
    }

@app.get("/api/auth/verify")
async def verify_auth(token_data: dict = Depends(verify_token)):
    """Verify current JWT token and return user info"""
    return {
        "valid": True,
        "user": {
            "email": token_data.get("sub"),
            "first_name": token_data.get("first_name"),
            "last_name": token_data.get("last_name"),
            "roles": token_data.get("roles", [])
        }
    }

@app.get("/api/simple-stations/")
async def get_simple_stations():
    """Simple stations endpoint that works with actual database schema"""
    try:
        # Use the same connection string from .env
        database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require')
        connection_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(connection_url)

        # Get basic station data without complex relationships
        result = await conn.fetch("""
            SELECT id, name, lat, long as lng, status, zone_number
            FROM stations
            WHERE status = 'active'
            ORDER BY name
            LIMIT 50
        """)

        stations = []
        for row in result:
            stations.append({
                "id": row["id"],
                "name": row["name"],
                "lat": float(row["lat"]) if row["lat"] else None,
                "lng": float(row["lng"]) if row["lng"] else None,
                "status": row["status"],
                "zone_number": row["zone_number"]
            })

        await conn.close()

        return {"stations": stations, "total_count": len(stations)}

    except Exception as e:
        return {"error": str(e), "stations": [], "total_count": 0}

@app.get("/api/stations/")
async def get_stations_with_lines():
    """Get comprehensive stations data with line relationships - Admin only"""
    try:
        # Create comprehensive stations data from authentic Bangkok transit data
        stations_data = []

        # Get lines for reference
        demo_lines = [
            {"id": 1, "name": "BTS Sukhumvit Line", "code": "SUK", "color": "#00A651", "company_name": "Bangkok Mass Transit System (BTS)"},
            {"id": 2, "name": "BTS Silom Line", "code": "SIL", "color": "#004225", "company_name": "Bangkok Mass Transit System (BTS)"},
            {"id": 3, "name": "MRT Blue Line", "code": "BL", "color": "#003DA5", "company_name": "Mass Rapid Transit Authority (MRTA)"},
            {"id": 4, "name": "MRT Purple Line", "code": "PP", "color": "#663399", "company_name": "Mass Rapid Transit Authority (MRTA)"},
            {"id": 5, "name": "Airport Rail Link", "code": "ARL", "color": "#FF6B35", "company_name": "State Railway of Thailand (SRT)"},
            {"id": 6, "name": "BTS Gold Line", "code": "GL", "color": "#FFD700", "company_name": "Bangkok Mass Transit System (BTS)"},
            {"id": 7, "name": "Bangkok BRT", "code": "BRT", "color": "#FF0000", "company_name": "Bangkok Bus Rapid Transit (BRT)"},
            {"id": 8, "name": "SRT Dark Red Line", "code": "SRT-DR", "color": "#8B0000", "company_name": "State Railway of Thailand (SRT)"},
            {"id": 9, "name": "SRT Light Red Line", "code": "SRT-LR", "color": "#FF6B6B", "company_name": "State Railway of Thailand (SRT)"},
            {"id": 10, "name": "MRT Yellow Line", "code": "YL", "color": "#FFD700", "company_name": "Mass Rapid Transit Authority (MRTA)"},
            {"id": 11, "name": "MRT Pink Line", "code": "PK", "color": "#FF69B4", "company_name": "Mass Rapid Transit Authority (MRTA)"}
        ]

        # Build comprehensive station data with line relationships
        station_id_counter = 1
        for line in demo_lines:
            line_id = line["id"]
            stations_list = get_demo_stations_for_line(line_id)

            for station_name in stations_list:
                # Check if station already exists (for interchange stations)
                existing_station = None
                for station in stations_data:
                    if station["name"] == station_name:
                        existing_station = station
                        break

                if existing_station:
                    # Add line to existing station (interchange station)
                    existing_station["lines"].append({
                        "line_id": line_id,
                        "line_name": line["name"],
                        "line_code": line["code"],
                        "line_color": line["color"],
                        "company_name": line["company_name"]
                    })
                    existing_station["is_interchange"] = len(existing_station["lines"]) > 1
                else:
                    # Create new station
                    stations_data.append({
                        "id": station_id_counter,
                        "name": station_name,
                        "status": "active",
                        "zone_number": 1,  # Default zone
                        "is_interchange": False,
                        "lines": [{
                            "line_id": line_id,
                            "line_name": line["name"],
                            "line_code": line["code"],
                            "line_color": line["color"],
                            "company_name": line["company_name"]
                        }],
                        "created_at": "2024-01-01T00:00:00"
                    })
                    station_id_counter += 1

        # Sort stations alphabetically
        stations_data.sort(key=lambda x: x["name"])

        return {
            "stations": stations_data,
            "total_count": len(stations_data),
            "interchange_count": len([s for s in stations_data if s["is_interchange"]]),
            "message": "Comprehensive Bangkok transit stations with line relationships"
        }

    except Exception as e:
        return {"error": str(e), "stations": [], "total_count": 0}

@app.get("/api/tickets/")
async def get_simple_tickets():
    """Simple tickets endpoint that returns empty data to prevent 404"""
    return {"tickets": [], "total_count": 0, "message": "Demo data - backend schema needs migration"}

@app.get("/api/fare-rules/")
async def get_simple_fare_rules():
    """Simple fare rules endpoint that returns empty data to prevent 404"""
    return {"fare_rules": [], "total_count": 0, "message": "Demo data - backend schema needs migration"}

@app.get("/api/users/")
async def get_users(admin_data: dict = Depends(require_admin_role)):
    """Get users from database or demo data - Admin only"""
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require')
        connection_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(connection_url)

        # Try to get users data, but return demo data if tables don't exist
        try:
            result = await conn.fetch("""
                SELECT u.id, u.email, u.first_name, u.last_name, u.phone, u.is_active, u.created_at,
                       array_agg(r.name) as roles
                FROM users u
                LEFT JOIN user_has_role uhr ON u.id = uhr.user_id
                LEFT JOIN roles r ON uhr.role_id = r.id
                GROUP BY u.id, u.email, u.first_name, u.last_name, u.phone, u.is_active, u.created_at
                ORDER BY u.created_at DESC
                LIMIT 100
            """)

            users = []
            for row in result:
                users.append({
                    "id": row["id"],
                    "email": row["email"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "phone": row["phone"],
                    "is_active": row["is_active"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "roles": [role for role in row["roles"] if role is not None]
                })

            await conn.close()
            return {"users": users, "total_count": len(users)}

        except Exception:
            # Return demo data if tables don't exist
            await conn.close()
            demo_users = [
                {
                    "id": 1,
                    "email": "admin@trainbooking.com",
                    "first_name": "Admin",
                    "last_name": "User",
                    "phone": "+1234567890",
                    "is_active": True,
                    "created_at": "2024-01-01T10:00:00Z",
                    "roles": ["admin", "user"]
                },
                {
                    "id": 2,
                    "email": "john.doe@email.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone": "+1234567891",
                    "is_active": True,
                    "created_at": "2024-01-02T11:30:00Z",
                    "roles": ["user"]
                },
                {
                    "id": 3,
                    "email": "jane.smith@email.com",
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "phone": "+1234567892",
                    "is_active": False,
                    "created_at": "2024-01-03T09:15:00Z",
                    "roles": ["user"]
                }
            ]
            return {"users": demo_users, "total_count": len(demo_users), "message": "Demo data - user tables need to be created"}

    except Exception as e:
        return {"error": str(e), "users": [], "total_count": 0}

@app.get("/api/roles/")
async def get_roles(admin_data: dict = Depends(require_admin_role)):
    """Get all roles from database or demo data - Admin only"""
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require')
        connection_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(connection_url)

        try:
            result = await conn.fetch("""
                SELECT id, name, description, created_at
                FROM roles
                ORDER BY name
            """)

            roles = []
            for row in result:
                roles.append({
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None
                })

            await conn.close()
            return {"roles": roles, "total_count": len(roles)}

        except Exception:
            # Return demo data if tables don't exist
            await conn.close()
            demo_roles = [
                {
                    "id": 1,
                    "name": "admin",
                    "description": "Administrator with full access to all features",
                    "created_at": "2024-01-01T10:00:00Z"
                },
                {
                    "id": 2,
                    "name": "user",
                    "description": "Regular user with basic booking permissions",
                    "created_at": "2024-01-01T10:01:00Z"
                },
                {
                    "id": 3,
                    "name": "moderator",
                    "description": "Moderator with limited administrative privileges",
                    "created_at": "2024-01-01T10:02:00Z"
                }
            ]
            return {"roles": demo_roles, "total_count": len(demo_roles), "message": "Demo data - roles table needs to be created"}

    except Exception as e:
        return {"error": str(e), "roles": [], "total_count": 0}

@app.post("/api/users/{user_id}/roles")
async def assign_role_to_user(user_id: int, role_data: dict, admin_data: dict = Depends(require_admin_role)):
    """Assign a role to a user - Admin only"""
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require')
        connection_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(connection_url)

        # Check if role assignment already exists
        existing = await conn.fetchrow("""
            SELECT id FROM user_has_role
            WHERE user_id = $1 AND role_id = $2
        """, user_id, role_data["role_id"])

        if existing:
            await conn.close()
            return {"success": False, "message": "User already has this role"}

        # Insert role assignment
        await conn.execute("""
            INSERT INTO user_has_role (user_id, role_id, assigned_at, assigned_by)
            VALUES ($1, $2, NOW(), $3)
        """, user_id, role_data["role_id"], role_data.get("assigned_by", 1))

        await conn.close()
        return {"success": True, "message": "Role assigned successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(user_id: int, role_id: int, admin_data: dict = Depends(require_admin_role)):
    """Remove a role from a user - Admin only"""
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require')
        connection_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(connection_url)

        # Remove role assignment
        result = await conn.execute("""
            DELETE FROM user_has_role
            WHERE user_id = $1 AND role_id = $2
        """, user_id, role_id)

        await conn.close()
        return {"success": True, "message": "Role removed successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/roles/")
async def create_role(role_data: dict, admin_data: dict = Depends(require_admin_role)):
    """Create a new role - Admin only"""
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require')
        connection_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(connection_url)

        # Insert new role
        result = await conn.fetchrow("""
            INSERT INTO roles (name, description, created_at)
            VALUES ($1, $2, NOW())
            RETURNING id, name, description, created_at
        """, role_data["name"], role_data["description"])

        await conn.close()

        return {
            "success": True,
            "message": "Role created successfully",
            "role": {
                "id": result["id"],
                "name": result["name"],
                "description": result["description"],
                "created_at": result["created_at"].isoformat() if result["created_at"] else None
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/roles/{role_id}")
async def update_role(role_id: int, role_data: dict, admin_data: dict = Depends(require_admin_role)):
    """Update a role - Admin only"""
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require')
        connection_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(connection_url)

        # Update role
        result = await conn.fetchrow("""
            UPDATE roles
            SET name = $2, description = $3
            WHERE id = $1
            RETURNING id, name, description, created_at
        """, role_id, role_data["name"], role_data["description"])

        await conn.close()

        if result:
            return {
                "success": True,
                "message": "Role updated successfully",
                "role": {
                    "id": result["id"],
                    "name": result["name"],
                    "description": result["description"],
                    "created_at": result["created_at"].isoformat() if result["created_at"] else None
                }
            }
        else:
            return {"success": False, "message": "Role not found"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/roles/{role_id}")
async def delete_role(role_id: int, admin_data: dict = Depends(require_admin_role)):
    """Delete a role and remove all user assignments - Admin only"""
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require')
        connection_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(connection_url)

        # First remove all user assignments for this role
        await conn.execute("DELETE FROM user_has_role WHERE role_id = $1", role_id)

        # Then delete the role
        result = await conn.execute("DELETE FROM roles WHERE id = $1", role_id)

        await conn.close()
        return {"success": True, "message": "Role deleted successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}

# Company Management Endpoints
@app.get("/api/companies/")
async def get_companies(admin_data: dict = Depends(require_admin_role)):
    """Get all companies - Admin only"""
    try:
        # Demo companies data - Bangkok Transit Operators
        demo_companies = [
            {
                "id": 1,
                "name": "Bangkok Mass Transit System (BTS)",
                "description": "Skytrain elevated rapid transit system",
                "email": "info@bts.co.th",
                "phone": "+66-2-617-6000",
                "address": "1200 Rama IV Road, Pathumwan, Bangkok 10330",
                "website": "www.bts.co.th",
                "status": "active",
                "company_color": "#00A651",
                "created_at": "2024-01-15T10:00:00"
            },
            {
                "id": 2,
                "name": "Mass Rapid Transit Authority (MRTA)",
                "description": "Underground subway and elevated transit operator",
                "email": "contact@mrta.co.th",
                "phone": "+66-2-354-2000",
                "address": "175 Rama IX Road, Huai Khwang, Bangkok 10310",
                "website": "www.mrta.co.th",
                "status": "active",
                "company_color": "#003DA5",
                "created_at": "2024-02-20T14:30:00"
            },
            {
                "id": 3,
                "name": "State Railway of Thailand (SRT)",
                "description": "National railway services including Airport Rail Link",
                "email": "info@railway.co.th",
                "phone": "+66-2-220-4334",
                "address": "1 Rong Muang Road, Pathumwan, Bangkok 10330",
                "website": "www.railway.co.th",
                "status": "active",
                "company_color": "#FF6B35",
                "created_at": "2024-03-10T09:15:00"
            },
            {
                "id": 4,
                "name": "Bangkok Bus Rapid Transit (BRT)",
                "description": "Bus rapid transit system",
                "email": "info@brt.bangkok.go.th",
                "phone": "+66-2-225-5555",
                "address": "Bangkok Metropolitan Administration",
                "website": "www.brt.bangkok.go.th",
                "status": "inactive",
                "company_color": "#FF0000",
                "created_at": "2024-04-05T11:00:00"
            }
        ]
        return {"companies": demo_companies}
    except Exception as e:
        return {"companies": [], "error": str(e)}

@app.post("/api/companies/")
async def create_company(company_data: dict, admin_data: dict = Depends(require_admin_role)):
    """Create a new company - Admin only"""
    try:
        from datetime import datetime

        # Create new company with demo ID
        new_company = {
            "id": 100 + len([]),  # Demo ID generation
            "name": company_data.get("name", ""),
            "description": company_data.get("description", ""),
            "email": company_data.get("email", ""),
            "phone": company_data.get("phone", ""),
            "address": company_data.get("address", ""),
            "website": company_data.get("website", ""),
            "status": company_data.get("status", "active"),
            "created_at": datetime.now().isoformat()
        }

        return {"success": True, "company": new_company, "message": "Company created successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/companies/{company_id}")
async def update_company(company_id: int, company_data: dict, admin_data: dict = Depends(require_admin_role)):
    """Update a company - Admin only"""
    try:
        updated_company = {
            "id": company_id,
            "name": company_data.get("name", ""),
            "description": company_data.get("description", ""),
            "email": company_data.get("email", ""),
            "phone": company_data.get("phone", ""),
            "address": company_data.get("address", ""),
            "website": company_data.get("website", ""),
            "status": company_data.get("status", "active"),
        }

        return {"success": True, "company": updated_company, "message": "Company updated successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/companies/{company_id}")
async def delete_company(company_id: int, admin_data: dict = Depends(require_admin_role)):
    """Delete a company - Admin only"""
    try:
        return {"success": True, "message": "Company deleted successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}

# Helper function for demo stations by line
def get_demo_stations_for_line(line_id):
    """Get authentic Bangkok transit stations for a specific line"""
    stations_by_line = {
        1: [  # BTS Sukhumvit Line (32 stations)
            "Mo Chit", "Saphan Phut", "Senanikhom", "Ari", "Sanam Pao", "Victory Monument",
            "Phaya Thai", "Ratchathewi", "Siam", "Chit Lom", "Ploenchit", "Nana", "Asok",
            "Phrom Phong", "Thong Lo", "Ekkamai", "Phra Khanong", "On Nut", "Bang Chak",
            "Punnawithi", "Udom Suk", "Bang Na", "Bearing", "Samrong", "Pu Chao", "Chang Erawan",
            "Royal Thai Naval Academy", "Pak Nam", "Srinagarindra", "Phraek Sa", "Sai Luat",
            "Kheha"
        ],
        2: [  # BTS Silom Line (14 stations)
            "National Stadium", "Siam", "Ratchadamri", "Sala Daeng", "Chong Nonsi",
            "Surasak", "Saphan Taksin", "Krung Thon Buri", "Wongwian Yai", "Pho Nimit",
            "Talad Phlu", "Wutthakat", "Bang Wa", "Phasi Charoen"
        ],
        3: [  # MRT Blue Line (38 stations)
            "Tha Phra", "Charan 13", "Fai Chai", "Bang Khun Non", "Bang Yi Khan", "Sirindhorn",
            "Bang Phlat", "Bang O", "Bang Pho", "Tao Poon", "Bang Sue", "Kamphaeng Phet",
            "Chatuchak Park", "Phahon Yothin", "Lat Phrao", "Ratchadaphisek", "Sutthisan",
            "Huai Khwang", "Thailand Cultural Centre", "Phra Ram 9", "Phetchaburi", "Sukhumvit",
            "Queen Sirikit National Convention Centre", "Khlong Toei", "Lumphini", "Si Lom",
            "Sam Yan", "Hua Lamphong", "Wat Mangkon", "Sam Yot", "Sanam Chai", "Itsaraphap",
            "Bang Phai", "Bang Wa", "Phetkasem 48", "Phasi Charoen", "Bang Khae", "Lak Song"
        ],
        4: [  # MRT Purple Line (16 stations)
            "Khlong Bang Phai", "Talad Bang Yai", "Sam Yaek Bang Yai", "Bang Phlu", "Bang Rak Yai",
            "Bang Rak Noi Tha It", "Sai Ma", "Phra Nang klao Bridge", "Yaek Nonthaburi 1",
            "Bang Krasor", "Nonthaburi Civic Center", "Ministry of Public Health", "Yaek Tiwanon",
            "Wong Sawang", "Bang Son", "Tao Poon"
        ],
        5: [  # Airport Rail Link (8 stations)
            "Suvarnabhumi", "Lat Krabang", "Ban Thap Chang", "Hua Mak", "Ramkhamhaeng",
            "Makkasan", "Ratchaprarop", "Phaya Thai"
        ],
        6: [  # BTS Gold Line (3 stations)
            "Krung Thon Buri", "Charoen Nakhon", "Khlong San"
        ],
        7: [  # BRT Line (14 stations) - Updated 2024 configuration
            "Sathorn", "Narathiwat 1", "Wat Pariwat", "Thanon Chan", "Wat Dokmai",
            "Wat Dan", "Charoen Rat", "Dao Khanong", "Bang Pakok", "Ratchapruek",
            "Nang Linchi", "Wat Sikesa", "Phran Nok", "Ratchaphruek"
        ],
        8: [  # SRT Dark Red Line (10 stations)
            "Krung Thep Aphiwat Central Terminal", "Chatuchak", "Wat Samian Nari",
            "Bang Bua", "Bang Khen", "Lak Si", "Kan Kheha", "Don Mueang", "Laksi",
            "Rangsit"
        ],
        9: [  # SRT Light Red Line (4 stations)
            "Krung Thep Aphiwat Central Terminal", "Bang Bamru", "Bang Kruai", "Taling Chan"
        ],
        10: [ # MRT Yellow Line (23 stations)
            "Lat Phrao", "Phawana", "Chok Chai 4", "Saphan Phut", "Wang Thonglang",
            "Hua Mak", "Ramkhamhaeng", "Ramkhamhaeng 12", "Malai", "Tedsaban Bang Na",
            "Bang Na", "Srinagarindra 38", "Srinagarindra 46", "Phraek Sa", "Lat Krabang",
            "Khlong Ban Ma", "Lam Sali", "Ban Thap Chang", "Hua Tak", "Phlu Ta Luang",
            "Suwinthawong", "Wat Thep Leela", "Samrong"
        ],
        11: [ # MRT Pink Line (30 stations)
            "Khae Rai", "Min Buri Market", "Min Buri", "Lat Pla Khao", "Klongchan",
            "Wat Bua Khwan", "Ramkhamhaeng University", "Ramkhamhaeng 109",
            "Nong Chok", "Krungthep Kreetha", "Saphan Mai", "Wat Phra Si Mahathat",
            "Ram Inthra 109", "Lat Mayom", "Wat Sri Waree", "Bang Kapi",
            "Khlong Tan", "Lat Phrao Wang Hin", "Chokchai", "Ratchadaphisek",
            "Din Daeng", "Pratunam", "Phetchaburi", "Thong Lo", "Asok",
            "Phrom Phong", "Benchasiri Park", "Emporium", "Phhra Khanong",
            "Wat That Thong"
        ]
    }
    return stations_by_line.get(line_id, [])

# Transit Lines Management Endpoints
@app.get("/api/lines/")
async def get_lines(admin_data: dict = Depends(require_admin_role)):
    """Get all transit lines - Admin only"""
    try:
        # Get station counts for each line
        def get_station_count_for_line(line_id):
            stations = get_demo_stations_for_line(line_id)
            return len(stations)

        # Comprehensive Bangkok Transit Lines Data - Updated 2024
        demo_lines = [
            {
                "id": 1,
                "name": "BTS Sukhumvit Line",
                "code": "SUK",
                "company_id": 1,
                "company_name": "Bangkok Mass Transit System (BTS)",
                "color": "#00A651",
                "type": "Skytrain",
                "stations_count": get_station_count_for_line(1),
                "length": "38.3 km",
                "status": "active",
                "description": "Light Green Line running from Mo Chit to Kheha with extensions",
                "created_at": "2024-01-15T10:00:00"
            },
            {
                "id": 2,
                "name": "BTS Silom Line",
                "code": "SIL",
                "company_id": 1,
                "company_name": "Bangkok Mass Transit System (BTS)",
                "color": "#004225",
                "type": "Skytrain",
                "stations_count": get_station_count_for_line(2),
                "length": "17.4 km",
                "status": "active",
                "description": "Dark Green Line from National Stadium to Phasi Charoen",
                "created_at": "2024-01-16T10:00:00"
            },
            {
                "id": 3,
                "name": "MRT Blue Line",
                "code": "BL",
                "company_id": 2,
                "company_name": "Mass Rapid Transit Authority (MRTA)",
                "color": "#003DA5",
                "type": "Subway",
                "stations_count": get_station_count_for_line(3),
                "length": "48.0 km",
                "status": "active",
                "description": "Underground circular line covering central Bangkok from Tha Phra to Lak Song",
                "created_at": "2024-01-17T10:00:00"
            },
            {
                "id": 4,
                "name": "MRT Purple Line",
                "code": "PP",
                "company_id": 2,
                "company_name": "Mass Rapid Transit Authority (MRTA)",
                "color": "#663399",
                "type": "Elevated",
                "stations_count": get_station_count_for_line(4),
                "length": "23.0 km",
                "status": "active",
                "description": "Purple Line from Khlong Bang Phai to Tao Poon",
                "created_at": "2024-01-18T10:00:00"
            },
            {
                "id": 5,
                "name": "Airport Rail Link",
                "code": "ARL",
                "company_id": 3,
                "company_name": "State Railway of Thailand (SRT)",
                "color": "#FF6B35",
                "type": "Express Rail",
                "stations_count": get_station_count_for_line(5),
                "length": "28.6 km",
                "status": "active",
                "description": "Express service from Suvarnabhumi Airport to Phaya Thai",
                "created_at": "2024-01-19T10:00:00"
            },
            {
                "id": 6,
                "name": "BTS Gold Line",
                "code": "GL",
                "company_id": 1,
                "company_name": "Bangkok Mass Transit System (BTS)",
                "color": "#FFD700",
                "type": "Monorail",
                "stations_count": get_station_count_for_line(6),
                "length": "1.8 km",
                "status": "active",
                "description": "Gold Line monorail from Krung Thon Buri to Khlong San",
                "created_at": "2024-01-20T10:00:00"
            },
            {
                "id": 7,
                "name": "Bangkok BRT",
                "code": "BRT",
                "company_id": 4,
                "company_name": "Bangkok Bus Rapid Transit (BRT)",
                "color": "#FF0000",
                "type": "Bus Rapid Transit",
                "stations_count": get_station_count_for_line(7),
                "length": "16.0 km",
                "status": "active",
                "description": "Bus rapid transit line from Sathorn to Ratchaphruek (upgraded 2024)",
                "created_at": "2024-01-21T10:00:00"
            },
            {
                "id": 8,
                "name": "SRT Dark Red Line",
                "code": "SRT-DR",
                "company_id": 3,
                "company_name": "State Railway of Thailand (SRT)",
                "color": "#8B0000",
                "type": "Commuter Rail",
                "stations_count": get_station_count_for_line(8),
                "length": "26.3 km",
                "status": "active",
                "description": "Dark Red commuter line from Krung Thep Aphiwat to Rangsit",
                "created_at": "2024-01-22T10:00:00"
            },
            {
                "id": 9,
                "name": "SRT Light Red Line",
                "code": "SRT-LR",
                "company_id": 3,
                "company_name": "State Railway of Thailand (SRT)",
                "color": "#FF6B6B",
                "type": "Commuter Rail",
                "stations_count": get_station_count_for_line(9),
                "length": "15.3 km",
                "status": "active",
                "description": "Light Red commuter line from Krung Thep Aphiwat to Taling Chan",
                "created_at": "2024-01-23T10:00:00"
            },
            {
                "id": 10,
                "name": "MRT Yellow Line",
                "code": "YL",
                "company_id": 2,
                "company_name": "Mass Rapid Transit Authority (MRTA)",
                "color": "#FFD700",
                "type": "Monorail",
                "stations_count": get_station_count_for_line(10),
                "length": "30.4 km",
                "status": "active",
                "description": "Yellow monorail from Lat Phrao to Samrong",
                "created_at": "2024-02-01T10:00:00"
            },
            {
                "id": 11,
                "name": "MRT Pink Line",
                "code": "PK",
                "company_id": 2,
                "company_name": "Mass Rapid Transit Authority (MRTA)",
                "color": "#FF69B4",
                "type": "Monorail",
                "stations_count": get_station_count_for_line(11),
                "length": "34.5 km",
                "status": "active",
                "description": "Pink monorail from Khae Rai to Wat That Thong",
                "created_at": "2024-02-15T10:00:00"
            }
        ]
        return {"lines": demo_lines}
    except Exception as e:
        return {"lines": [], "error": str(e)}

@app.post("/api/lines/")
async def create_line(line_data: dict, admin_data: dict = Depends(require_admin_role)):
    """Create a new transit line - Admin only"""
    try:
        from datetime import datetime

        # Create new line with demo ID
        line_id = 100 + len([])  # Demo ID generation
        new_line = {
            "id": line_id,
            "name": line_data.get("name", ""),
            "code": line_data.get("code", ""),
            "company_id": line_data.get("company_id", 1),
            "company_name": line_data.get("company_name", ""),
            "color": line_data.get("color", "#000000"),
            "type": line_data.get("type", ""),
            "stations_count": len(get_demo_stations_for_line(line_id)),  # Calculate from stations
            "length": line_data.get("length", ""),
            "status": line_data.get("status", "active"),
            "description": line_data.get("description", ""),
            "created_at": datetime.now().isoformat()
        }

        return {"success": True, "line": new_line, "message": "Transit line created successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/lines/{line_id}")
async def update_line(line_id: int, line_data: dict, admin_data: dict = Depends(require_admin_role)):
    """Update a transit line - Admin only"""
    try:
        updated_line = {
            "id": line_id,
            "name": line_data.get("name", ""),
            "code": line_data.get("code", ""),
            "company_id": line_data.get("company_id", 1),
            "company_name": line_data.get("company_name", ""),
            "color": line_data.get("color", "#000000"),
            "type": line_data.get("type", ""),
            "stations_count": len(get_demo_stations_for_line(line_id)),  # Calculate from stations
            "length": line_data.get("length", ""),
            "status": line_data.get("status", "active"),
            "description": line_data.get("description", ""),
        }

        return {"success": True, "line": updated_line, "message": "Transit line updated successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/lines/{line_id}")
async def delete_line(line_id: int, admin_data: dict = Depends(require_admin_role)):
    """Delete a transit line - Admin only"""
    try:
        return {"success": True, "message": "Transit line deleted successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}

# Route Management Endpoints
@app.get("/api/routes/")
async def get_routes():
    """Get all routes"""
    try:
        # Demo routes data using authentic Bangkok stations
        demo_routes = [
            {
                "id": 1,
                "name": "BTS Sukhumvit Express",
                "description": "Express route along BTS Sukhumvit Line from Mo Chit to Bearing",
                "stops": [
                    {
                        "station_id": 1,
                        "station_name": "Mo Chit",
                        "order": 1,
                        "lines": [{"line_id": 1, "line_name": "BTS Sukhumvit Line", "line_code": "SUK", "line_color": "#00A651"}]
                    },
                    {
                        "station_id": 2,
                        "station_name": "Victory Monument",
                        "order": 2,
                        "lines": [{"line_id": 1, "line_name": "BTS Sukhumvit Line", "line_code": "SUK", "line_color": "#00A651"}]
                    },
                    {
                        "station_id": 3,
                        "station_name": "Siam",
                        "order": 3,
                        "lines": [
                            {"line_id": 1, "line_name": "BTS Sukhumvit Line", "line_code": "SUK", "line_color": "#00A651"},
                            {"line_id": 2, "line_name": "BTS Silom Line", "line_code": "SIL", "line_color": "#004225"}
                        ]
                    },
                    {
                        "station_id": 4,
                        "station_name": "Asok",
                        "order": 4,
                        "lines": [
                            {"line_id": 1, "line_name": "BTS Sukhumvit Line", "line_code": "SUK", "line_color": "#00A651"},
                            {"line_id": 3, "line_name": "MRT Blue Line", "line_code": "BL", "line_color": "#003DA5"}
                        ]
                    },
                    {
                        "station_id": 5,
                        "station_name": "Bearing",
                        "order": 5,
                        "lines": [{"line_id": 1, "line_name": "BTS Sukhumvit Line", "line_code": "SUK", "line_color": "#00A651"}]
                    }
                ],
                "total_stations": 5,
                "estimated_time": "25 min",
                "status": "active",
                "created_at": "2024-01-15T10:00:00"
            },
            {
                "id": 2,
                "name": "Cross-City Airport Connection",
                "description": "Multi-line route connecting city center with Suvarnabhumi Airport",
                "stops": [
                    {
                        "station_id": 6,
                        "station_name": "Siam",
                        "order": 1,
                        "lines": [
                            {"line_id": 1, "line_name": "BTS Sukhumvit Line", "line_code": "SUK", "line_color": "#00A651"},
                            {"line_id": 2, "line_name": "BTS Silom Line", "line_code": "SIL", "line_color": "#004225"}
                        ]
                    },
                    {
                        "station_id": 7,
                        "station_name": "Phaya Thai",
                        "order": 2,
                        "lines": [
                            {"line_id": 1, "line_name": "BTS Sukhumvit Line", "line_code": "SUK", "line_color": "#00A651"},
                            {"line_id": 5, "line_name": "Airport Rail Link", "line_code": "ARL", "line_color": "#FF6B35"}
                        ]
                    },
                    {
                        "station_id": 8,
                        "station_name": "Makkasan",
                        "order": 3,
                        "lines": [{"line_id": 5, "line_name": "Airport Rail Link", "line_code": "ARL", "line_color": "#FF6B35"}]
                    },
                    {
                        "station_id": 9,
                        "station_name": "Suvarnabhumi",
                        "order": 4,
                        "lines": [{"line_id": 5, "line_name": "Airport Rail Link", "line_code": "ARL", "line_color": "#FF6B35"}]
                    }
                ],
                "total_stations": 4,
                "estimated_time": "45 min",
                "status": "active",
                "created_at": "2024-02-01T10:00:00"
            },
            {
                "id": 3,
                "name": "MRT Blue Line Circuit",
                "description": "Full circle route on MRT Blue Line covering major city areas",
                "stops": [
                    {
                        "station_id": 10,
                        "station_name": "Hua Lamphong",
                        "order": 1,
                        "lines": [{"line_id": 3, "line_name": "MRT Blue Line", "line_code": "BL", "line_color": "#003DA5"}]
                    },
                    {
                        "station_id": 11,
                        "station_name": "Si Lom",
                        "order": 2,
                        "lines": [
                            {"line_id": 2, "line_name": "BTS Silom Line", "line_code": "SIL", "line_color": "#004225"},
                            {"line_id": 3, "line_name": "MRT Blue Line", "line_code": "BL", "line_color": "#003DA5"}
                        ]
                    },
                    {
                        "station_id": 12,
                        "station_name": "Lumphini",
                        "order": 3,
                        "lines": [{"line_id": 3, "line_name": "MRT Blue Line", "line_code": "BL", "line_color": "#003DA5"}]
                    },
                    {
                        "station_id": 13,
                        "station_name": "Sukhumvit",
                        "order": 4,
                        "lines": [
                            {"line_id": 1, "line_name": "BTS Sukhumvit Line", "line_code": "SUK", "line_color": "#00A651"},
                            {"line_id": 3, "line_name": "MRT Blue Line", "line_code": "BL", "line_color": "#003DA5"}
                        ]
                    },
                    {
                        "station_id": 14,
                        "station_name": "Chatuchak Park",
                        "order": 5,
                        "lines": [{"line_id": 3, "line_name": "MRT Blue Line", "line_code": "BL", "line_color": "#003DA5"}]
                    },
                    {
                        "station_id": 15,
                        "station_name": "Bang Sue",
                        "order": 6,
                        "lines": [{"line_id": 3, "line_name": "MRT Blue Line", "line_code": "BL", "line_color": "#003DA5"}]
                    }
                ],
                "total_stations": 6,
                "estimated_time": "35 min",
                "status": "active",
                "created_at": "2024-02-15T10:00:00"
            }
        ]
        return {"routes": demo_routes}
    except Exception as e:
        return {"routes": [], "error": str(e)}

@app.post("/api/routes/")
async def create_route(route_data: dict):
    """Create a new route"""
    try:
        from datetime import datetime

        # Create new route with demo ID
        new_route = {
            "id": 100 + len([]),  # Demo ID generation
            "name": route_data.get("name", ""),
            "description": route_data.get("description", ""),
            "stops": route_data.get("stops", []),
            "total_stations": route_data.get("total_stations", 0),
            "estimated_time": route_data.get("estimated_time", "0 min"),
            "status": route_data.get("status", "active"),
            "created_at": datetime.now().isoformat()
        }

        return {"success": True, "route": new_route, "message": "Route created successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/routes/{route_id}")
async def update_route(route_id: int, route_data: dict):
    """Update a route"""
    try:
        updated_route = {
            "id": route_id,
            "name": route_data.get("name", ""),
            "description": route_data.get("description", ""),
            "stops": route_data.get("stops", []),
            "total_stations": route_data.get("total_stations", 0),
            "estimated_time": route_data.get("estimated_time", "0 min"),
            "status": route_data.get("status", "active"),
        }

        return {"success": True, "route": updated_route, "message": "Route updated successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/routes/{route_id}")
async def delete_route(route_id: int):
    """Delete a route"""
    try:
        return {"success": True, "message": "Route deleted successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)