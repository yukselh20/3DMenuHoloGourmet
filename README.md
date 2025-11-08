# 3D/AR Restaurant Menu Platform

A full-stack web application that enables restaurants to create interactive, true-to-scale 3D/AR menus. Restaurant managers upload photos of dishes, and the system automatically generates photorealistic 3D models. Customers can then scan a QR code to view these models in their browser, rotate them, zoom in, and even place them on their table using Augmented Reality.

This project has evolved from a simple proof-of-concept to a scalable, multi-tenant platform with a real, asynchronous 3D processing pipeline.

![Demo Gif Placeholder - A short gif showing the app in action would go here]

## Key Features

### For Restaurant Managers (Admin Dashboard)
*   **Multi-Tenant Architecture**: Secure registration for multiple restaurants, with each restaurant's data completely isolated.
*   **Menu Management**: Full CRUD (Create, Read, Update, Delete) functionality for menu items.
*   **Automated 3D Model Generation**: Simply upload a `.zip` file containing photos of a dish. The system handles the rest.
*   **Asynchronous Processing**: Photogrammetry jobs are processed in the background, allowing managers to continue working without waiting.
*   **Real-time Job Monitoring**: See the status of your 3D model generation in real-time (`PENDING` -> `PROCESSING` -> `COMPLETED`/`FAILED`).
*   **Interactive 3D Preview**: Once a model is successfully generated, an interactive 3D preview is shown directly on the admin dashboard.
*   **QR Code & Public URL Generation**: A unique QR code and shareable URL are automatically created for each completed menu item.

### For Customers (Public View)
*   **Interactive 3D Viewer**: A high-performance viewer with smooth touch controls for rotation and zooming.
*   **True-to-Scale AR Mode**: Place a life-sized virtual model of the dish on your own table using WebXR to see its exact portion size and presentation before ordering.
*   **Detailed Information**: View the dish's name, description, price, allergens, and dimensions.
*   **Optimized Experience**: Features a progress indicator for loading large 3D models.

---

## Technology Stack

The platform is built on a modern, scalable, and containerized architecture.

| Component                 | Technology                                                                                                  | Description                                                                     |
| ------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Backend Framework**     | **FastAPI (Python)**                                                                                        | High-performance, asynchronous API development.                                 |
| **Database**              | **MongoDB** with **Motor**                                                                                  | Asynchronous, NoSQL database for flexible data storage.                         |
| **Task Queue**            | **Celery** with **Redis**                                                                                   | Manages the long-running photogrammetry tasks asynchronously.                   |
| **Photogrammetry Engine** | **Meshroom CLI**                                                                                            | Core open-source software for generating 3D models from photos.                 |
| **3D Model Optimization** | **gltf-pipeline**                                                                                           | Converts and optimizes models to the web-ready `.glb` format with Draco compression. |
| **File Storage**          | **AWS S3**                                                                                                  | Scalable, reliable storage for uploaded images and generated 3D models.         |
| **Frontend Framework**    | **React**                                                                                                   | Building the user interface for both the admin dashboard and public views.      |
| **3D Rendering**          | **React Three Fiber** & **Drei**                                                                            | Powerful libraries for creating and interacting with 3D scenes in React.        |
| **Augmented Reality**     | **React Three XR**                                                                                          | Enables the immersive WebXR-based Augmented Reality experience.                 |
| **UI / Styling**          | **Tailwind CSS** & **Shadcn UI**                                                                            | A modern utility-first CSS framework and a set of beautifully designed components. |
| **Containerization**      | **Docker** & **Docker Compose**                                                                             | Ensures a consistent and reproducible development and deployment environment.   |

---

## Getting Started

The entire application stack is containerized, making the setup process straightforward.

### Prerequisites

*   **Docker & Docker Compose**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
*   **An AWS Account**: Required for file storage. You will need an S3 bucket and IAM credentials. The AWS Free Tier is more than sufficient for development.

### Setup Instructions

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-name>
    ```

2.  **Configure Backend Environment**
    Create a file named `.env` inside the `backend/` directory and populate it with your credentials.

    **File:** `backend/.env`
    ```env
    # MongoDB Configuration (uses the service name 'mongo' from docker-compose)
    MONGO_URL="mongodb://mongo:27017"
    DB_NAME="restaurant_3d_menu"

    # JWT Configuration - IMPORTANT: Change this to a long, random, secret string!
    JWT_SECRET_KEY="a-very-strong-and-secret-key-that-you-must-change"

    # CORS Configuration
    CORS_ORIGINS="*"

    # Celery Configuration (uses the service name 'redis' from docker-compose)
    CELERY_BROKER_URL="redis://redis:6379/0"

    # Backend URL for generating public links
    BACKEND_BASE_URL="http://localhost:8001"
    
    # Sentry DSN for error monitoring (optional)
    SENTRY_DSN=""

    # AWS S3 Configuration - IMPORTANT: FILL THESE OUT
    AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_ACCESS_KEY"
    S3_BUCKET_NAME="your-s3-bucket-name"
    S3_REGION="your-bucket-region" # e.g., us-east-1
    ```

3.  **Configure Frontend Environment**
    Create a file named `.env` inside the `frontend/` directory.

    **File:** `frontend/.env`
    ```env
    # This URL tells the React app where to find the backend API.
    REACT_APP_BACKEND_URL=http://localhost:8001

    # Sentry DSN for error monitoring (optional)
    REACT_APP_SENTRY_DSN=""
    ```

4.  **Build and Run the Application**
    From the **root directory** of the project, run the following command:
    ```bash
    docker-compose up --build
    ```
    The first build will take several minutes as it needs to download Meshroom and install all dependencies. Subsequent builds will be much faster.

5.  **Access the Services**
    *   **Frontend Application**: [http://localhost:3000](http://localhost:3000)
    *   **Backend API Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## How to Test the Full Workflow

1.  **Register:** Go to `http://localhost:3000`, switch to the "Register" tab, and create a new restaurant account.
2.  **Create Item:** On the dashboard, click "Create Menu Item" and fill out the form.
3.  **Prepare Photos:** Create a `.zip` archive containing at least 5 photos (`.jpg`, `.png`) of an object, taken from multiple angles.
4.  **Upload Photos:** On the newly created menu item card, select your `.zip` file and click the upload button.
5.  **Monitor Processing:** The status badge will change from `PENDING` to `PROCESSING`. You can monitor the detailed progress in your terminal by watching the logs from the `restaurant-worker` container. This step can take several minutes.
6.  **View Result:** Once the status changes to `COMPLETED`, the card will refresh to show an interactive 3D preview of your generated model.
7.  **Test AR:** Click "View Public" to open the customer-facing page. On a compatible mobile device, you can test the "View on Your Table (AR)" functionality.

---

## API Endpoints

All protected endpoints require a `Bearer <token>` in the `Authorization` header.

### Authentication

*   `POST /api/auth/register`: Register a new organization and user.
*   `POST /api/auth/login`: Log in and receive a JWT.
*   `GET /api/auth/me`: Get the current authenticated user's details.

### Menu Items (Protected)

*   `POST /api/menu-items`: Create a new menu item.
*   `GET /api/menu-items`: List all menu items for the user's organization.
*   `GET /api/menu-items/{item_id}`: Get a single menu item.
*   `PUT /api/menu-items/{item_id}`: Update a menu item.
*   `DELETE /api/menu-items/{item_id}`: Delete a menu item.
*   `POST /api/menu-items/{item_id}/upload-images`: Upload a `.zip` file of photos to start a processing job.

### Jobs (Protected)

*   `GET /api/jobs/{item_id}`: Get the latest processing job status for a menu item.

### Public

*   `GET /api/public/menu-item/{item_id}`: Get the public details of a menu item (unauthenticated).
*   `/storage/processed-models/{item_id}.glb`: Endpoint to serve the static 3D model files.
