import React, { useState, useEffect } from 'react';
import axios from 'axios';
import useAuthStore from '../store/authStore';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import { Plus, Upload, ExternalLink, Eye, Trash2, LogOut } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const PUBLIC_URL = window.location.origin;

const AdminDashboard = () => {
  const { token, user, logout } = useAuthStore();
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [jobStatuses, setJobStatuses] = useState({});

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    allergens: '',
    diameter: '',
    height: '',
  });

  const [uploadFile, setUploadFile] = useState(null);

  useEffect(() => {
    if (token) {
      fetchMenuItems();
    }
  }, [token]);

  const fetchMenuItems = async () => {
    try {
      const response = await axios.get(`${API}/menu-items`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMenuItems(response.data);
      
      // Fetch job statuses for items
      response.data.forEach(item => {
        fetchJobStatus(item.id);
      });
    } catch (error) {
      toast.error('Failed to fetch menu items');
    }
  };

  const fetchJobStatus = async (itemId) => {
    try {
      const response = await axios.get(`${API}/jobs/${itemId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setJobStatuses(prev => ({ ...prev, [itemId]: response.data }));
    } catch (error) {
      console.error('Failed to fetch job status', error);
    }
  };

  const handleCreateMenuItem = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const allergensList = formData.allergens
        ? formData.allergens.split(',').map(a => a.trim())
        : [];

      const response = await axios.post(
        `${API}/menu-items`,
        {
          name: formData.name,
          description: formData.description,
          price: parseFloat(formData.price),
          allergens: allergensList,
          dimensions_cm: {
            diameter: parseFloat(formData.diameter),
            height: parseFloat(formData.height),
          },
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      toast.success('Menu item created successfully!');
      setMenuItems([...menuItems, response.data]);
      setShowCreateDialog(false);
      setFormData({
        name: '',
        description: '',
        price: '',
        allergens: '',
        diameter: '',
        height: '',
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create menu item');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadImages = async (itemId) => {
    if (!uploadFile) {
      toast.error('Please select a zip file');
      return;
    }

    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      toast.info('Uploading images...');
      const response = await axios.post(`${API}/menu-items/${itemId}/upload-images`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success('Images uploaded! Processing started...');
      setUploadFile(null);
      
      // Poll for job status
      const pollInterval = setInterval(async () => {
        try {
          const jobResponse = await axios.get(`${API}/jobs/${itemId}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          
          setJobStatuses(prev => ({ ...prev, [itemId]: jobResponse.data }));
          
          if (jobResponse.data.status === 'COMPLETED' || jobResponse.data.status === 'FAILED') {
            clearInterval(pollInterval);
            if (jobResponse.data.status === 'COMPLETED') {
              toast.success('3D model generated successfully!');
              fetchMenuItems();
            } else {
              toast.error('Processing failed: ' + jobResponse.data.error_message);
            }
          }
        } catch (error) {
          clearInterval(pollInterval);
        }
      }, 3000);
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (!window.confirm('Are you sure you want to delete this menu item?')) {
      return;
    }

    try {
      await axios.delete(`${API}/menu-items/${itemId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Menu item deleted');
      setMenuItems(menuItems.filter(item => item.id !== itemId));
    } catch (error) {
      toast.error('Failed to delete menu item');
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      PENDING: 'bg-yellow-100 text-yellow-800',
      PROCESSING: 'bg-blue-100 text-blue-800',
      COMPLETED: 'bg-green-100 text-green-800',
      FAILED: 'bg-red-100 text-red-800',
      NO_JOB: 'bg-gray-100 text-gray-800',
    };
    return statusMap[status] || statusMap.NO_JOB;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900" data-testid="dashboard-title">3D Menu Manager</h1>
            <p className="text-slate-600 mt-1" data-testid="user-email">Welcome, {user?.email}</p>
          </div>
          <Button variant="outline" onClick={logout} data-testid="logout-btn">
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </Button>
        </div>

        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="mb-6" data-testid="create-menu-item-btn">
              <Plus className="mr-2 h-4 w-4" />
              Create Menu Item
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Menu Item</DialogTitle>
              <DialogDescription>
                Add a new dish to your 3D menu. You'll be able to upload photos after creation.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateMenuItem} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Dish Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Grilled Salmon"
                  required
                  data-testid="dish-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe the dish..."
                  required
                  data-testid="dish-description-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="price">Price ($)</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    placeholder="24.99"
                    required
                    data-testid="dish-price-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="allergens">Allergens (comma-separated)</Label>
                  <Input
                    id="allergens"
                    value={formData.allergens}
                    onChange={(e) => setFormData({ ...formData, allergens: e.target.value })}
                    placeholder="nuts, dairy, gluten"
                    data-testid="dish-allergens-input"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="diameter">Plate Diameter (cm)</Label>
                  <Input
                    id="diameter"
                    type="number"
                    step="0.1"
                    value={formData.diameter}
                    onChange={(e) => setFormData({ ...formData, diameter: e.target.value })}
                    placeholder="28"
                    required
                    data-testid="dish-diameter-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="height">Dish Height (cm)</Label>
                  <Input
                    id="height"
                    type="number"
                    step="0.1"
                    value={formData.height}
                    onChange={(e) => setFormData({ ...formData, height: e.target.value })}
                    placeholder="10"
                    required
                    data-testid="dish-height-input"
                  />
                </div>
              </div>
              <Button type="submit" disabled={loading} className="w-full" data-testid="submit-menu-item-btn">
                {loading ? 'Creating...' : 'Create Menu Item'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {menuItems.map((item) => {
            const jobStatus = jobStatuses[item.id];
            const publicUrl = `${PUBLIC_URL}/view/${item.id}`;

            return (
              <Card key={item.id} className="relative hover:shadow-lg transition-shadow" data-testid="menu-item-card">
                <CardHeader>
                  <CardTitle className="text-xl" data-testid="menu-item-name">{item.name}</CardTitle>
                  <CardDescription data-testid="menu-item-price">${item.price}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-slate-600 line-clamp-2" data-testid="menu-item-description">{item.description}</p>
                  
                  {jobStatus && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-500">Status:</span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusBadge(jobStatus.status)}`} data-testid="job-status-badge">
                        {jobStatus.status || 'NO_JOB'}
                      </span>
                    </div>
                  )}

                  {!item.model_url && (
                    <div className="space-y-2">
                      <Label htmlFor={`upload-${item.id}`}>Upload Photos (.zip)</Label>
                      <div className="flex gap-2">
                        <Input
                          id={`upload-${item.id}`}
                          type="file"
                          accept=".zip"
                          onChange={(e) => setUploadFile(e.target.files[0])}
                          className="flex-1"
                          data-testid="upload-photos-input"
                        />
                        <Button
                          size="sm"
                          onClick={() => handleUploadImages(item.id)}
                          disabled={!uploadFile}
                          data-testid="upload-photos-btn"
                        >
                          <Upload className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}

                  {item.model_url && (
                    <div className="space-y-3">
                      <div className="flex justify-center bg-white p-2 rounded border">
                        <QRCodeSVG value={publicUrl} size={120} data-testid="qr-code" />
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="flex-1"
                          onClick={() => window.open(publicUrl, '_blank')}
                          data-testid="view-public-btn"
                        >
                          <Eye className="mr-2 h-4 w-4" />
                          View Public
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            navigator.clipboard.writeText(publicUrl);
                            toast.success('Link copied!');
                          }}
                          data-testid="copy-link-btn"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}

                  <Button
                    size="sm"
                    variant="destructive"
                    className="w-full"
                    onClick={() => handleDeleteItem(item.id)}
                    data-testid="delete-menu-item-btn"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {menuItems.length === 0 && (
          <Card className="text-center py-12">
            <CardContent>
              <p className="text-slate-500 mb-4">No menu items yet. Create your first 3D menu item!</p>
              <Button onClick={() => setShowCreateDialog(true)} data-testid="create-first-item-btn">
                <Plus className="mr-2 h-4 w-4" />
                Create First Item
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;