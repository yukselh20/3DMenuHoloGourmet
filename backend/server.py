from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import boto3
from botocore.exceptions import ClientError
import io
import zipfile
import asyncio
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# S3 Configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
S3_REGION = os.environ.get('S3_REGION', 'us-east-1')

# Initialize S3 client (will be None if credentials not provided)
s3_client = None
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and S3_BUCKET_NAME:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=S3_REGION
    )

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class MenuItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    allergens: Optional[List[str]] = None
    dimensions_cm: dict  # {"diameter": 28, "height": 10}
    model_url: Optional[str] = None
    owner_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MenuItemCreate(BaseModel):
    name: str
    description: str
    price: float
    allergens: Optional[List[str]] = None
    dimensions_cm: dict

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    allergens: Optional[List[str]] = None
    dimensions_cm: Optional[dict] = None

class PhotogrammetryJob(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    menu_item_id: str
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    raw_images_zip_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user is None:
        raise credentials_exception
    
    # Convert ISO string to datetime if needed
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return User(**user)

def upload_to_s3(file_content: bytes, key: str, content_type: str = 'application/zip') -> str:
    """Upload file to S3 and return the URL"""
    if not s3_client:
        # Mock S3 upload for local development
        return f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{key}"
    
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=file_content,
            ContentType=content_type
        )
        return f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{key}"
    except ClientError as e:
        logging.error(f"Error uploading to S3: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

async def process_photogrammetry_job(job_id: str, menu_item_id: str):
    """Mock photogrammetry processing - simulates the Meshroom pipeline"""
    try:
        # Update job status to PROCESSING
        await db.photogrammetry_jobs.update_one(
            {"id": job_id},
            {"$set": {"status": "PROCESSING"}}
        )
        
        # Simulate processing time (5-10 seconds)
        await asyncio.sleep(8)
        
        # Use a sample GLB model URL (this would be the converted output in production)
        # For MVP, we're using a publicly available sample model
        sample_model_url = "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Duck/glTF-Binary/Duck.glb"
        
        # Update menu item with model URL
        await db.menu_items.update_one(
            {"id": menu_item_id},
            {"$set": {"model_url": sample_model_url}}
        )
        
        # Update job status to COMPLETED
        await db.photogrammetry_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "COMPLETED",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
    except Exception as e:
        # Update job status to FAILED
        await db.photogrammetry_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "FAILED",
                "error_message": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )

# Auth Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_create: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = User(
        email=user_create.email
    )
    
    # Store user with hashed password
    user_doc = user.model_dump()
    user_doc['created_at'] = user_doc['created_at'].isoformat()
    user_doc['hashed_password'] = get_password_hash(user_create.password)
    
    await db.users.insert_one(user_doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token, token_type="bearer")

@api_router.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    # Find user
    user_doc = await db.users.find_one({"email": user_login.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(user_login.password, user_doc.get('hashed_password', '')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token = create_access_token(data={"sub": user_doc['id']})
    return Token(access_token=access_token, token_type="bearer")

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Menu Item Routes
@api_router.post("/menu-items", response_model=MenuItem)
async def create_menu_item(
    menu_item: MenuItemCreate,
    current_user: User = Depends(get_current_user)
):
    item = MenuItem(
        **menu_item.model_dump(),
        owner_id=current_user.id
    )
    
    item_doc = item.model_dump()
    item_doc['created_at'] = item_doc['created_at'].isoformat()
    
    await db.menu_items.insert_one(item_doc)
    return item

@api_router.get("/menu-items", response_model=List[MenuItem])
async def get_menu_items(current_user: User = Depends(get_current_user)):
    items = await db.menu_items.find({"owner_id": current_user.id}, {"_id": 0}).to_list(1000)
    
    for item in items:
        if isinstance(item.get('created_at'), str):
            item['created_at'] = datetime.fromisoformat(item['created_at'])
    
    return items

@api_router.get("/menu-items/{item_id}", response_model=MenuItem)
async def get_menu_item(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    item = await db.menu_items.find_one(
        {"id": item_id, "owner_id": current_user.id},
        {"_id": 0}
    )
    
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    if isinstance(item.get('created_at'), str):
        item['created_at'] = datetime.fromisoformat(item['created_at'])
    
    return MenuItem(**item)

@api_router.put("/menu-items/{item_id}", response_model=MenuItem)
async def update_menu_item(
    item_id: str,
    menu_item_update: MenuItemUpdate,
    current_user: User = Depends(get_current_user)
):
    # Check if item exists and belongs to user
    existing_item = await db.menu_items.find_one(
        {"id": item_id, "owner_id": current_user.id}
    )
    
    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    # Update only provided fields
    update_data = {k: v for k, v in menu_item_update.model_dump().items() if v is not None}
    
    if update_data:
        await db.menu_items.update_one(
            {"id": item_id},
            {"$set": update_data}
        )
    
    # Fetch and return updated item
    updated_item = await db.menu_items.find_one({"id": item_id}, {"_id": 0})
    
    if isinstance(updated_item.get('created_at'), str):
        updated_item['created_at'] = datetime.fromisoformat(updated_item['created_at'])
    
    return MenuItem(**updated_item)

@api_router.delete("/menu-items/{item_id}")
async def delete_menu_item(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    # Check if item exists and belongs to user
    existing_item = await db.menu_items.find_one(
        {"id": item_id, "owner_id": current_user.id}
    )
    
    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    # Delete associated jobs
    await db.photogrammetry_jobs.delete_many({"menu_item_id": item_id})
    
    # Delete menu item
    await db.menu_items.delete_one({"id": item_id})
    
    return {"message": "Menu item deleted successfully"}

@api_router.post("/menu-items/{item_id}/upload-images")
async def upload_images(
    item_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Check if item exists and belongs to user
    existing_item = await db.menu_items.find_one(
        {"id": item_id, "owner_id": current_user.id}
    )
    
    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    # Validate file is a zip
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a zip archive")
    
    # Read file content
    file_content = await file.read()
    
    # Validate it's a valid zip file
    try:
        with zipfile.ZipFile(io.BytesIO(file_content)) as zip_file:
            # Check if zip contains image files
            image_extensions = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
            image_files = [f for f in zip_file.namelist() if f.lower().endswith(image_extensions)]
            
            if len(image_files) < 5:
                raise HTTPException(
                    status_code=400,
                    detail="Zip file must contain at least 5 images"
                )
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file")
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    # Upload to S3
    s3_key = f"raw-zips/{job_id}.zip"
    zip_url = upload_to_s3(file_content, s3_key, 'application/zip')
    
    # Create photogrammetry job
    job = PhotogrammetryJob(
        id=job_id,
        menu_item_id=item_id,
        status="PENDING",
        raw_images_zip_url=zip_url
    )
    
    job_doc = job.model_dump()
    job_doc['created_at'] = job_doc['created_at'].isoformat()
    
    await db.photogrammetry_jobs.insert_one(job_doc)
    
    # Start background task to process photogrammetry
    asyncio.create_task(process_photogrammetry_job(job_id, item_id))
    
    return {
        "message": "Upload successful",
        "job_id": job_id,
        "status": "PENDING"
    }

# Job Status Routes
@api_router.get("/jobs/{item_id}")
async def get_job_status(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    # Check if item belongs to user
    existing_item = await db.menu_items.find_one(
        {"id": item_id, "owner_id": current_user.id}
    )
    
    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    # Get latest job for this item
    job = await db.photogrammetry_jobs.find_one(
        {"menu_item_id": item_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    if not job:
        return {"status": "NO_JOB", "message": "No processing job found"}
    
    # Convert dates if needed
    if isinstance(job.get('created_at'), str):
        job['created_at'] = datetime.fromisoformat(job['created_at'])
    if job.get('completed_at') and isinstance(job['completed_at'], str):
        job['completed_at'] = datetime.fromisoformat(job['completed_at'])
    
    return PhotogrammetryJob(**job)

# Public Routes
@api_router.get("/public/menu-item/{item_id}")
async def get_public_menu_item(item_id: str):
    item = await db.menu_items.find_one({"id": item_id}, {"_id": 0, "owner_id": 0})
    
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    if isinstance(item.get('created_at'), str):
        item['created_at'] = datetime.fromisoformat(item['created_at'])
    
    return item

@api_router.get("/")
async def root():
    return {"message": "3D/AR Restaurant Menu API"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()