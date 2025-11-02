import { create } from 'zustand';

const useAuthStore = create((set) => ({
  token: localStorage.getItem('auth-token') || null,
  user: JSON.parse(localStorage.getItem('auth-user') || 'null'),
  setAuth: (token, user) => {
    localStorage.setItem('auth-token', token);
    localStorage.setItem('auth-user', JSON.stringify(user));
    set({ token, user });
  },
  logout: () => {
    localStorage.removeItem('auth-token');
    localStorage.removeItem('auth-user');
    set({ token: null, user: null });
  },
}));

export default useAuthStore;