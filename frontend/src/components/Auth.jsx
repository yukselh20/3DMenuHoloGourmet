import React, { useState } from 'react';
import axios from 'axios';
import useAuthStore from '../store/authStore';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Auth = ({ onSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [organizationName, setOrganizationName] = useState(''); // New state for organization name
  const [loading, setLoading] = useState(false);
  const setAuth = useAuthStore((state) => state.setAuth);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';

      const payload = isLogin
          ? { email, password }
          : { email, password, organization_name: organizationName };

      const response = await axios.post(`${API}${endpoint}`, payload);

      const { access_token } = response.data;

      // Get user details
      const userResponse = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${access_token}` },
      });

      setAuth(access_token, userResponse.data);
      toast.success(isLogin ? 'Logged in successfully!' : 'Account created successfully!');

      if (onSuccess) onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
      <Card className="w-full max-w-md mx-auto" data-testid="auth-card">
        <CardHeader>
          <CardTitle data-testid="auth-title">{isLogin ? 'Login' : 'Register'}</CardTitle>
          <CardDescription data-testid="auth-description">
            {isLogin ? 'Welcome back to your 3D menu manager' : 'Create your restaurant account'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
                <div className="space-y-2">
                  <Label htmlFor="organizationName">Restaurant Name</Label>
                  <Input
                      id="organizationName"
                      type="text"
                      placeholder="e.g., The Gourmet Place"
                      value={organizationName}
                      onChange={(e) => setOrganizationName(e.target.value)}
                      required
                      data-testid="org-name-input"
                  />
                </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                  id="email"
                  type="email"
                  placeholder="restaurant@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  data-testid="email-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  data-testid="password-input"
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading} data-testid="auth-submit-btn">
              {loading ? 'Loading...' : isLogin ? 'Login' : 'Register'}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <button
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                className="text-sm text-blue-600 hover:underline"
                data-testid="toggle-auth-mode-btn"
            >
              {isLogin ? "Don't have an account? Register" : 'Already have an account? Login'}
            </button>
          </div>
        </CardContent>
      </Card>
  );
};

export default Auth;