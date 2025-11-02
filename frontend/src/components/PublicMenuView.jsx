import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import ModelViewer from './ModelViewer';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { Maximize2, RotateCw, ZoomIn, AlertCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PublicMenuView = () => {
  const { itemId } = useParams();
  const [menuItem, setMenuItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [arSupported, setArSupported] = useState(false);

  useEffect(() => {
    fetchMenuItem();
    checkArSupport();
  }, [itemId]);

  const fetchMenuItem = async () => {
    try {
      const response = await axios.get(`${API}/public/menu-item/${itemId}`);
      setMenuItem(response.data);
      setLoading(false);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to load menu item');
      setLoading(false);
    }
  };

  const checkArSupport = () => {
    // Check if WebXR is supported
    if (navigator.xr) {
      navigator.xr.isSessionSupported('immersive-ar').then((supported) => {
        setArSupported(supported);
      }).catch(() => {
        setArSupported(false);
      });
    }
  };

  const handleViewInAr = () => {
    if (!arSupported) {
      toast.info('AR is not supported on this device. WebXR support required.');
      return;
    }
    
    // AR functionality will be implemented in Phase 2
    toast.info('AR feature coming soon! For now, use touch gestures to rotate and zoom the model.');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center" data-testid="loading-screen">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-white mx-auto mb-4"></div>
          <p className="text-lg">Loading your dish...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center p-4" data-testid="error-screen">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              Error
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p>{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!menuItem || !menuItem.model_url) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center p-4" data-testid="no-model-screen">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Model Not Available</CardTitle>
          </CardHeader>
          <CardContent>
            <p>The 3D model for this menu item is still being processed. Please check back later.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800" data-testid="public-menu-view">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-white" data-testid="dish-name">{menuItem.name}</h1>
          <p className="text-white/80 text-sm" data-testid="restaurant-name">Interactive 3D Menu</p>
        </div>
      </div>

      {/* 3D Viewer */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Viewer Column */}
          <div className="lg:col-span-2">
            <Card className="overflow-hidden bg-slate-800/50 backdrop-blur-md border-white/20">
              <div className="aspect-square lg:aspect-video w-full">
                <ModelViewer
                  modelUrl={menuItem.model_url}
                  dimensions={menuItem.dimensions_cm}
                  className="w-full h-full"
                />
              </div>
              <CardContent className="p-4 bg-slate-900/50">
                <div className="flex items-center justify-between text-white/80 text-sm">
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1">
                      <RotateCw className="h-4 w-4" />
                      Drag to rotate
                    </span>
                    <span className="flex items-center gap-1">
                      <ZoomIn className="h-4 w-4" />
                      Pinch to zoom
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* AR Button */}
            <div className="mt-4">
              <Button
                size="lg"
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold"
                onClick={handleViewInAr}
                disabled={!arSupported}
                data-testid="ar-button"
              >
                <Maximize2 className="mr-2 h-5 w-5" />
                {arSupported ? 'View on Your Table (AR)' : 'AR Not Supported'}
              </Button>
              {!arSupported && (
                <p className="text-white/60 text-xs text-center mt-2">
                  AR requires a compatible device with WebXR support
                </p>
              )}
            </div>
          </div>

          {/* Info Column */}
          <div className="space-y-4">
            <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
              <CardHeader>
                <CardTitle className="text-2xl" data-testid="menu-item-title">{menuItem.name}</CardTitle>
                <CardDescription className="text-3xl font-bold text-blue-300" data-testid="menu-item-price">
                  ${menuItem.price.toFixed(2)}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Description</h3>
                  <p className="text-white/80 text-sm" data-testid="menu-item-desc">{menuItem.description}</p>
                </div>

                {menuItem.allergens && menuItem.allergens.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-2">Allergens</h3>
                    <div className="flex flex-wrap gap-2" data-testid="allergens-list">
                      {menuItem.allergens.map((allergen, index) => (
                        <Badge key={index} variant="secondary" className="bg-red-500/20 text-red-200">
                          {allergen}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <h3 className="font-semibold mb-2">Portion Size</h3>
                  <div className="text-sm text-white/80 space-y-1" data-testid="dimensions-info">
                    <p>Diameter: {menuItem.dimensions_cm.diameter} cm</p>
                    <p>Height: {menuItem.dimensions_cm.height} cm</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-blue-500/10 backdrop-blur-md border-blue-400/30 text-white">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-blue-500/20 mb-3">
                    <Maximize2 className="h-6 w-6 text-blue-300" />
                  </div>
                  <h4 className="font-semibold mb-2">True-to-Scale AR</h4>
                  <p className="text-sm text-white/70">
                    Use AR to see this dish in real size on your table before ordering!
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PublicMenuView;