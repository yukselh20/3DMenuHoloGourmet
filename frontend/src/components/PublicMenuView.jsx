import React, { useState, useEffect, Suspense, useRef } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Canvas } from '@react-three/fiber';
import { XR, useXR } from '@react-three/xr';
import { ModelViewer, ARModelPlacer, LoadingFallback } from './ModelViewer';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Maximize2, RotateCw, ZoomIn, AlertCircle, X } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PublicMenuView = () => {
  const { itemId } = useParams();
  const [menuItem, setMenuItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [arSupported, setArSupported] = useState(false);
  const [inAR, setInAR] = useState(false);
  const [showPlacementHelper, setShowPlacementHelper] = useState(false);
  const [loadedModel, setLoadedModel] = useState(null);
  const glRef = useRef(null);

  useEffect(() => {
    const checkArSupport = async () => {
      if (navigator.xr) {
        try {
          const supported = await navigator.xr.isSessionSupported('immersive-ar');
          setArSupported(supported);
        } catch {
          setArSupported(false);
        }
      }
    };
    checkArSupport();
  }, []);

  useEffect(() => {
    const fetchMenuItem = async () => {
      try {
        const response = await axios.get(`${API}/public/menu-item/${itemId}`);
        setMenuItem(response.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load menu item');
      } finally {
        setLoading(false);
      }
    };
    fetchMenuItem();
  }, [itemId]);

  const startARSession = async () => {
    if (!glRef.current) return;

    try {
      const session = await navigator.xr.requestSession('immersive-ar', {
        requiredFeatures: ['hit-test', 'local-floor'],
      });

      glRef.current.xr.setSession(session);
      setInAR(true);
      setShowPlacementHelper(true);

      session.addEventListener('end', () => setInAR(false));
    } catch (e) {
      console.error('Failed to start AR session:', e);
    }
  };

  if (loading) {
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center">
          <div className="text-white text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-white mx-auto mb-4"></div>
            <p className="text-lg">Loading your dish...</p>
          </div>
        </div>
    );
  }

  if (error) {
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center p-4">
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
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center p-4">
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
      <>
        {/* Normal 3D Menu View */}
        <div className={`min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 ${inAR ? 'hidden' : ''}`}>
          <div className="bg-white/10 backdrop-blur-md border-b border-white/20">
            <div className="container mx-auto px-4 py-4">
              <h1 className="text-2xl font-bold text-white">{menuItem.name}</h1>
              <p className="text-white/80 text-sm">Interactive 3D Menu</p>
            </div>
          </div>

          <div className="container mx-auto px-4 py-8">
            <div className="grid lg:grid-cols-3 gap-8">
              {/* Viewer Column */}
              <div className="lg:col-span-2">
                <Card className="overflow-hidden bg-slate-800/50 backdrop-blur-md border-white/20">
                  <div className="aspect-square lg:aspect-video w-full">
                    <ModelViewer
                        modelUrl={menuItem.model_url}
                        dimensions={menuItem.dimensions_cm}
                        onModelLoaded={setLoadedModel}
                    />
                  </div>
                  <CardContent className="p-4 bg-slate-900/50">
                    <div className="flex items-center justify-between text-white/80 text-sm">
                      <div className="flex items-center gap-4">
                      <span className="flex items-center gap-1">
                        <RotateCw className="h-4 w-4" /> Drag to rotate
                      </span>
                        <span className="flex items-center gap-1">
                        <ZoomIn className="h-4 w-4" /> Pinch to zoom
                      </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* New AR Button */}
                <div className="mt-4">
                  <Button
                      onClick={startARSession}
                      disabled={!arSupported || !loadedModel}
                      className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 px-6 rounded-lg flex items-center justify-center text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {arSupported ? (
                        <>
                          <Maximize2 className="mr-2 h-5 w-5" /> View on Your Table (AR)
                        </>
                    ) : (
                        'AR Not Supported'
                    )}
                  </Button>
                  {!arSupported && (
                      <p className="text-white/60 text-xs text-center mt-2">
                        AR requires a compatible device and browser (e.g., Chrome on Android or Safari on iOS).
                      </p>
                  )}
                </div>
              </div>

              {/* Info Column */}
              <div className="space-y-4">
                <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
                  <CardHeader>
                    <CardTitle className="text-2xl">{menuItem.name}</CardTitle>
                    <CardDescription className="text-3xl font-bold text-blue-300">
                      ${menuItem.price.toFixed(2)}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h3 className="font-semibold mb-2">Description</h3>
                      <p className="text-white/80 text-sm">{menuItem.description}</p>
                    </div>
                    {menuItem.allergens?.length > 0 && (
                        <div>
                          <h3 className="font-semibold mb-2">Allergens</h3>
                          <div className="flex flex-wrap gap-2">
                            {menuItem.allergens.map((a, i) => (
                                <Badge key={i} variant="secondary" className="bg-red-500/20 text-red-200">
                                  {a}
                                </Badge>
                            ))}
                          </div>
                        </div>
                    )}
                    <div>
                      <h3 className="font-semibold mb-2">Portion Size</h3>
                      <div className="text-sm text-white/80 space-y-1">
                        <p>Diameter: {menuItem.dimensions_cm.diameter} cm</p>
                        <p>Height: {menuItem.dimensions_cm.height} cm</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </div>

        {/* AR View */}
        {inAR && loadedModel && (
            <>
              <Canvas ref={glRef} className="fixed inset-0 z-50">
                <XR sessionInit={{ requiredFeatures: ['hit-test', 'local-floor'] }}>
                  <ambientLight intensity={1.5} />
                  <Suspense fallback={null}>
                    <ARModelPlacer model={loadedModel} onPlace={() => setShowPlacementHelper(false)} />
                  </Suspense>
                </XR>
              </Canvas>

              {showPlacementHelper && (
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-white text-center p-4 bg-black/50 rounded-lg">
                    <p>Point your camera at a flat surface, then tap the screen to place the dish.</p>
                  </div>
              )}

              <button
                  onClick={() => {
                    const session = glRef.current?.xr?.getSession();
                    if (session) session.end();
                    setInAR(false);
                  }}
                  className="absolute top-4 right-4 bg-black/50 text-white rounded-full p-3 z-50"
              >
                <X className="h-6 w-6" />
              </button>
            </>
        )}
      </>
  );
};

export default PublicMenuView;
