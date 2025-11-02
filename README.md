# 3D/AR Restaurant Menu Platform - MVP

A full-stack web application that enables restaurants to create interactive 3D menus. Restaurant managers upload photos of dishes, and customers scan QR codes to view photorealistic 3D models in their browser.

## 🎯 Features

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

## 🏗️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT tokens with bcrypt password hashing
- **File Storage**: AWS S3 (mock storage for MVP)
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

## 📁 Project Structure

```
/app/
├── backend/
│   ├── server.py           # FastAPI application
│   ├── .env               # Environment variables
│   └── requirements.txt    # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Auth.jsx              # Login/Register
│   │   │   ├── AdminDashboard.jsx    # Manager dashboard
│   │   │   ├── PublicMenuView.jsx    # Customer view
│   │   │   ├── ModelViewer.jsx       # 3D renderer
│   │   │   └── ui/                   # Shadcn components
│   │   ├── store/
│   │   │   └── authStore.js          # Auth state management
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── .env               # Frontend environment
│
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Node.js 20+ and Yarn
- Python 3.10+
- MongoDB

### Backend Setup

1. **Install dependencies**:
```bash
cd /app/backend
pip install -r requirements.txt
```

2. **Configure environment** (`.env`):
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="restaurant_3d_menu"
JWT_SECRET_KEY="your-secret-key-here"
CORS_ORIGINS="*"

# Optional: S3 Configuration
# AWS_ACCESS_KEY_ID="your-key"
# AWS_SECRET_ACCESS_KEY="your-secret"
# S3_BUCKET_NAME="your-bucket"
# S3_REGION="us-east-1"
```

3. **Run the server**:
```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup

1. **Install dependencies**:
```bash
cd /app/frontend
yarn install --ignore-engines
```

2. **Configure environment** (`.env`):
```env
REACT_APP_BACKEND_URL=https://your-domain.com
```

3. **Start development server**:
```bash
yarn start
```

## 📡 API Endpoints

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

## 🧪 Testing

### Quick Test Flow

```bash
# 1. Register user
curl -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@restaurant.com","password":"test123"}'

# 2. Create menu item
curl -X POST "$API_URL/menu-items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Grilled Salmon",
    "description": "Fresh Atlantic salmon",
    "price": 24.99,
    "allergens": ["fish"],
    "dimensions_cm": {"diameter": 28, "height": 10}
  }'

# 3. Upload photos
curl -X POST "$API_URL/menu-items/{ITEM_ID}/upload-images" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@photos.zip"

# 4. Check job status
curl -X GET "$API_URL/jobs/{ITEM_ID}" \
  -H "Authorization: Bearer $TOKEN"

# 5. View public page
# Visit: https://your-domain.com/view/{ITEM_ID}
```

## 🎨 Design Features

- **Modern UI**: Clean, professional interface with Tailwind CSS
- **Gradient Backgrounds**: Subtle blue-slate gradients
- **Glass Morphism**: Backdrop blur effects for depth
- **Responsive Design**: Mobile-first approach
- **Interactive 3D**: Smooth controls with OrbitControls
- **Loading States**: Skeleton screens and spinners
- **Toast Notifications**: Real-time feedback with Sonner

## 📦 Database Schema

### Users Collection
```javascript
{
  id: "uuid",
  email: "user@example.com",
  hashed_password: "bcrypt_hash",
  created_at: "ISO datetime"
}
```

### Menu Items Collection
```javascript
{
  id: "uuid",
  name: "Dish Name",
  description: "Description",
  price: 24.99,
  allergens: ["gluten", "dairy"],
  dimensions_cm: {diameter: 28, height: 10},
  model_url: "s3://bucket/models/item.glb",
  owner_id: "user_uuid",
  created_at: "ISO datetime"
}
```

### Photogrammetry Jobs Collection
```javascript
{
  id: "uuid",
  menu_item_id: "item_uuid",
  status: "COMPLETED",  // PENDING, PROCESSING, COMPLETED, FAILED
  raw_images_zip_url: "s3://bucket/raw-zips/job.zip",
  error_message: null,
  created_at: "ISO datetime",
  completed_at: "ISO datetime"
}
```

## 🔒 Security

- JWT tokens with secure secret keys
- Bcrypt password hashing
- CORS protection
- Input validation with Pydantic
- File type validation (.zip only)
- Minimum image requirements (5+ images per upload)

## 🚧 MVP Limitations & Future Enhancements

### Current MVP Limitations
- **Mock Photogrammetry**: Uses sample model instead of real 3D reconstruction
- **Mock S3 Storage**: Local development uses mock URLs
- **No AR**: AR button present but not functional (requires WebXR Phase 2)
- **Sample Model**: All items use the same Duck.glb model

### Phase 2 Enhancements
1. **Real Photogrammetry**:
   - Meshroom CLI integration
   - GPU-accelerated processing
   - Celery worker queue
   - gltf-pipeline optimization

2. **AR Features**:
   - WebXR implementation
   - Device camera integration
   - True-to-scale placement
   - Surface detection

3. **Additional Features**:
   - Multiple 3D model formats
   - Model preview in admin
   - Batch processing
   - Analytics dashboard
   - Custom QR code designs
   - Menu categories
   - Restaurant branding

## 🐛 Known Issues

- First load may be slow due to 3D model download
- AR detection not implemented (Phase 2)
- No model caching (future optimization)

## 📝 Environment Variables

### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=restaurant_3d_menu
JWT_SECRET_KEY=your-secret-key
CORS_ORIGINS=*
AWS_ACCESS_KEY_ID=optional
AWS_SECRET_ACCESS_KEY=optional
S3_BUCKET_NAME=optional
S3_REGION=us-east-1
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=https://your-api-domain.com
```

## 📄 License

MIT License - Feel free to use this project for your restaurant!

## 🤝 Contributing

Contributions welcome! Please follow standard PR practices.

## 📞 Support

For issues or questions, please open a GitHub issue.

---

**Built with ❤️ for the future of dining experiences**