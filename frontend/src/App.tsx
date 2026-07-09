import React from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { Login } from './components/auth/Login';
import { Register } from './components/auth/Register';
import { Dashboard } from './components/Dashboard';
import { ProfileSetup } from './components/profile/ProfileSetup';
import { GuidedIntake } from './components/motion/GuidedIntake';
import { MotionPreview } from './components/motion/MotionPreview';
import { MotionFlowSelector } from './components/motion/MotionFlowSelector';
import { FormFlowSelector } from './components/forms/FormFlowSelector';
import { CaseIntake } from './components/case/CaseIntake';
import { GameplanCreation } from './components/case/GameplanCreation';
import { FormExecution } from './components/case/FormExecution';
import { PrivateRoute } from './components/PrivateRoute';
import { EmergencyHelp } from './components/emergency/EmergencyHelp';
import { ViolationIntake } from './components/violation/ViolationIntake';
import { EvidenceManager } from './components/evidence/EvidenceManager';
import { BulkTextImport } from './components/evidence/BulkTextImport';
import { GmailCallback } from './components/evidence/GmailCallback';
import { PrivacyPolicy } from './components/legal/PrivacyPolicy';
import { Terms } from './components/legal/Terms';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/emergency" element={<EmergencyHelp />} />
          
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
          {/* New case-first flow */}
          <Route
            path="/case/intake"
            element={
              <PrivateRoute>
                <CaseIntake />
              </PrivateRoute>
            }
          />
          <Route
            path="/case/gameplan"
            element={
              <PrivateRoute>
                <GameplanCreation />
              </PrivateRoute>
            }
          />
          <Route
            path="/case/forms"
            element={
              <PrivateRoute>
                <FormExecution />
              </PrivateRoute>
            }
          />

          {/* Legacy form flow: Show selector first */}
          <Route
            path="/form/new/:formType"
            element={
              <PrivateRoute>
                <FormFlowSelector />
              </PrivateRoute>
            }
          />
          {/* Guided forms path */}
          <Route
            path="/form/guided/:formType"
            element={
              <PrivateRoute>
                <GuidedIntake />
              </PrivateRoute>
            }
          />
          {/* Legacy motion routes - redirect to new form routes */}
          <Route
            path="/motion/new/:motionType"
            element={
              <PrivateRoute>
                <MotionFlowSelector />
              </PrivateRoute>
            }
          />
          <Route
            path="/motion/guided/:motionType"
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
          
          {/* Evidence manager */}
          <Route
            path="/motion/:motionId/evidence"
            element={
              <PrivateRoute>
                <EvidenceManager />
              </PrivateRoute>
            }
          />
          <Route
            path="/motion/:motionId/evidence/bulk-import"
            element={
              <PrivateRoute>
                <BulkTextImport />
              </PrivateRoute>
            }
          />

          {/* Violation/enforcement intake */}
          <Route
            path="/violation/intake"
            element={
              <PrivateRoute>
                <ViolationIntake />
              </PrivateRoute>
            }
          />

          {/* Gmail OAuth callback (protected) */}
          <Route
            path="/evidence/gmail/callback"
            element={
              <PrivateRoute>
                <GmailCallback />
              </PrivateRoute>
            }
          />

          {/* Legal pages (public) */}
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/terms" element={<Terms />} />

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;