from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
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
from botocore.exceptions import ClientError
import io
import zipfile

# Import S3 utility and the new Celery task
from s3_utils import upload_file_obj_to_s3
from tasks import process_photogrammetry_job

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')


# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]


# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()


# Models
class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    organization_id: str # Foreign key to Organization
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    organization_name: str # New field for registration

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
    dimensions_cm: dict # {"diameter": 28, "height": 10}
    model_url: Optional[str] = None
    owner_id: str
    organization_id: str # Foreign key to Organization
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
    organization_id: str # Foreign key to Organization
    status: str # PENDING, PROCESSING, COMPLETED, FAILED
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

    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])

    return User(**user)


# Auth Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_create: UserCreate):
    existing_user = await db.users.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    organization = Organization(name=user_create.organization_name)
    org_doc = organization.model_dump()
    org_doc['created_at'] = org_doc['created_at'].isoformat()
    await db.organizations.insert_one(org_doc)

    user = User(
        email=user_create.email,
        organization_id=organization.id
    )

    user_doc = user.model_dump()
    user_doc['created_at'] = user_doc['created_at'].isoformat()
    user_doc['hashed_password'] = get_password_hash(user_create.password)

    await db.users.insert_one(user_doc)

    access_token = create_access_token(data={"sub": user.id, "org_id": user.organization_id})
    return Token(access_token=access_token, token_type="bearer")

@api_router.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    user_doc = await db.users.find_one({"email": user_login.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user_login.password, user_doc.get('hashed_password', '')):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user_doc['id'], "org_id": user_doc['organization_id']})
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
        owner_id=current_user.id,
        organization_id=current_user.organization_id
    )

    item_doc = item.model_dump()
    item_doc['created_at'] = item_doc['created_at'].isoformat()

    await db.menu_items.insert_one(item_doc)
    return item

@api_router.get("/menu-items", response_model=List[MenuItem])
async def get_menu_items(current_user: User = Depends(get_current_user)):
    items = await db.menu_items.find(
        {"organization_id": current_user.organization_id},
        {"_id": 0}
    ).to_list(1000)

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
        {"id": item_id, "organization_id": current_user.organization_id},
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
    existing_item = await db.menu_items.find_one(
        {"id": item_id, "organization_id": current_user.organization_id}
    )

    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    update_data = {k: v for k, v in menu_item_update.model_dump().items() if v is not None}

    if update_data:
        await db.menu_items.update_one(
            {"id": item_id},
            {"$set": update_data}
        )

    updated_item = await db.menu_items.find_one(
        {"id": item_id, "organization_id": current_user.organization_id},
        {"_id": 0}
    )

    if isinstance(updated_item.get('created_at'), str):
        updated_item['created_at'] = datetime.fromisoformat(updated_item['created_at'])

    return MenuItem(**updated_item)

@api_router.delete("/menu-items/{item_id}")
async def delete_menu_item(
        item_id: str,
        current_user: User = Depends(get_current_user)
):
    existing_item = await db.menu_items.find_one(
        {"id": item_id, "organization_id": current_user.organization_id}
    )

    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    await db.photogrammetry_jobs.delete_many(
        {"menu_item_id": item_id, "organization_id": current_user.organization_id}
    )

    await db.menu_items.delete_one(
        {"id": item_id, "organization_id": current_user.organization_id}
    )

    return {"message": "Menu item deleted successfully"}

@api_router.post("/menu-items/{item_id}/upload-images")
async def upload_images(
        item_id: str,
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user)
):
    existing_item = await db.menu_items.find_one(
        {"id": item_id, "organization_id": current_user.organization_id}
    )

    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a zip archive")

    # Read the entire file into memory for robust validation.
    file_content = await file.read()

    # Create an in-memory binary stream (file-like object) from the content.
    file_buffer = io.BytesIO(file_content)

    try:
        # Validate the entire in-memory file.
        with zipfile.ZipFile(file_buffer, 'r') as zip_file:
            image_extensions = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
            image_files = [f for f in zip_file.namelist() if f.lower().endswith(image_extensions)]

            if len(image_files) < 1:
                raise HTTPException(
                    status_code=400,
                    detail="Zip file must contain at least one image file."
                )
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file")

    # IMPORTANT: Reset the buffer's pointer to the beginning for the S3 upload.
    file_buffer.seek(0)

    job_id = str(uuid.uuid4())
    s3_key = f"raw-uploads/{job_id}.zip"
    try:
        # Upload the in-memory buffer to S3.
        zip_url = upload_file_obj_to_s3(file_buffer, s3_key, 'application/zip')
    except ClientError:
        raise HTTPException(status_code=500, detail="Failed to upload file to S3")

    job = PhotogrammetryJob(
        id=job_id,
        menu_item_id=item_id,
        organization_id=current_user.organization_id,
        status="PENDING",
        raw_images_zip_url=zip_url
    )

    job_doc = job.model_dump()
    job_doc['created_at'] = job_doc['created_at'].isoformat()

    await db.photogrammetry_jobs.insert_one(job_doc)

    process_photogrammetry_job.delay(job_id, item_id)

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
    existing_item = await db.menu_items.find_one(
        {"id": item_id, "organization_id": current_user.organization_id}
    )

    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    job = await db.photogrammetry_jobs.find_one(
        {"menu_item_id": item_id, "organization_id": current_user.organization_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )

    if not job:
        return {"status": "NO_JOB", "message": "No processing job found"}

    if isinstance(job.get('created_at'), str):
        job['created_at'] = datetime.fromisoformat(job['created_at'])
    if job.get('completed_at') and isinstance(job.get('completed_at'), str):
        job['completed_at'] = datetime.fromisoformat(job['completed_at'])

    return PhotogrammetryJob(**job)

# Public Routes
@api_router.get("/public/menu-item/{item_id}")
async def get_public_menu_item(item_id: str):
    item = await db.menu_items.find_one({"id": item_id}, {"_id": 0, "owner_id": 0, "organization_id": 0})

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