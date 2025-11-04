# 3D/AR Restaurant Menu Platform - MVP

A full-stack web application that enables restaurants to create interactive 3D menus. Restaurant managers upload photos of dishes, and customers scan QR codes to view photorealistic 3D models in their browser.

## Features

### Restaurant Manager Features
- **User Authentication**: Secure JWT-based registration and login
- **Menu Item Management**: Create, read, update, and delete menu items
- **Photo Upload**: Upload .zip files containing multiple photos of dishes (30-50 images)
- **Automatic Processing**: Photos are processed to generate 3D models (MVP uses mock processing)
- **Job Monitoring**: Real-time status updates (PENDING → PROCESSING → COMPLETED)
- **QR Code Generation**: Automatic QR code creation for each menu item
- **Public URLs**: Shareable links for customer access

### Customer Features
- **3D Model Viewer**: Interactive 3D visualization with touch controls
- **Rotation & Zoom**: Drag to rotate, pinch to zoom
- **Dish Information**: View name, description, price, allergens, and portion size
- **True-to-Scale Display**: Models scaled to real-world dimensions
- **AR Ready**: Infrastructure for AR viewing (Phase 2)

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT tokens with bcrypt password hashing
- **File Storage**: AWS S3 (mock storage for MVP)
- **Task Queue**: Celery with Redis broker
- **ORM**: Pydantic models

### Frontend
- **Framework**: React 19
- **3D Rendering**: react-three-fiber + @react-three/drei (Three.js)
- **State Management**: Zustand
- **Styling**: Tailwind CSS + Shadcn UI components
- **Routing**: React Router v7
- **QR Codes**: qrcode.react

### Processing Pipeline (MVP - Mocked)
- **Photogrammetry**: Simulated 8-second processing
- **Output**: Sample .glb model from Khronos glTF repository
- **Future**: Integration with Meshroom CLI for real 3D reconstruction

## Getting Started

This project is fully containerized using Docker. This is the recommended way to run the application for development.

### Prerequisites
- Docker and Docker Compose
- Node.js 20+ and Yarn (for frontend type-checking/linting locally)

### Development Setup with Docker

1.  **Configure Backend Environment**
    Create a `.env` file inside `/app/backend/`. You can copy the example below. At a minimum, set your `JWT_SECRET_KEY`.

    ```env
    # /app/backend/.env
    MONGO_URL="mongodb://mongo:27017"
    DB_NAME="restaurant_3d_menu"
    JWT_SECRET_KEY="your-super-secret-key-here"
    CORS_ORIGINS="*"
    CELERY_BROKER_URL="redis://redis:6379/0"

    # Optional: AWS S3 for real file storage
    # AWS_ACCESS_KEY_ID="your-key"
    # AWS_SECRET_ACCESS_KEY="your-secret"
    # S3_BUCKET_NAME="your-bucket-name"
    # S3_REGION="us-east-1"
    ```

2.  **Configure Frontend Environment**
    Create a `.env` file inside `/app/frontend/`. This tells the React app how to communicate with the backend.

    ```env
    # /app/frontend/.env
    REACT_APP_BACKEND_URL=http://localhost:8001
    ```

3.  **Build and Run the Application**
    From the root directory of the project, run:
    ```bash
    docker-compose up --build
    ```
    This command will build the images for the frontend and backend services and start all containers.

    -   Frontend will be available at `http://localhost:3000`
    -   Backend API will be available at `http://localhost:8001`
    -   Backend API docs will be at `http://localhost:8001/docs`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user (protected)

### Menu Items (Protected)
- `POST /api/menu-items` - Create menu item
- `GET /api/menu-items` - List user's menu items
- `GET /api/menu-items/{id}` - Get single menu item
- `PUT /api/menu-items/{id}` - Update menu item
- `DELETE /api/menu-items/{id}` - Delete menu item
- `POST /api/menu-items/{id}/upload-images` - Upload photos (.zip)

### Jobs (Protected)
- `GET /api/jobs/{item_id}` - Get processing job status

### Public
- `GET /api/public/menu-item/{id}` - Get menu item for public viewing