import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import useAuthStore from './store/authStore';
import Auth from './components/Auth';
import AdminDashboard from './components/AdminDashboard';
import PublicMenuView from './components/PublicMenuView';
import '@/App.css';

function App() {
  const token = useAuthStore((state) => state.token);

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          {/* Public Route */}
          <Route path="/view/:itemId" element={<PublicMenuView />} />
          
          {/* Admin Routes */}
          <Route
            path="/"
            element={
              token ? <AdminDashboard /> : <Auth onSuccess={() => window.location.reload()} />
            }
          />
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-center" richColors />
    </div>
  );
}

export default App;