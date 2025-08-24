import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { Login } from './components/auth/Login';
import { Register } from './components/auth/Register';
import { Dashboard } from './components/Dashboard';
import { ProfileSetup } from './components/profile/ProfileSetup';
import { GuidedIntake } from './components/motion/GuidedIntake';
import { MotionPreview } from './components/motion/MotionPreview';
import { PrivateRoute } from './components/PrivateRoute';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/profile/setup"
            element={
              <PrivateRoute>
                <ProfileSetup />
              </PrivateRoute>
            }
          />
          <Route
            path="/motion/new/:motionType"
            element={
              <PrivateRoute>
                <GuidedIntake />
              </PrivateRoute>
            }
          />
          <Route
            path="/motion/:motionId/preview"
            element={
              <PrivateRoute>
                <MotionPreview />
              </PrivateRoute>
            }
          />
          <Route
            path="/motion/:motionId/edit/:stepNumber"
            element={
              <PrivateRoute>
                <GuidedIntake />
              </PrivateRoute>
            }
          />
          <Route
            path="/motion/:motionId"
            element={
              <PrivateRoute>
                <MotionPreview />
              </PrivateRoute>
            }
          />
          
          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;