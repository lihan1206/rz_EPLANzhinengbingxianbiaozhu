import type { ReactNode } from 'react';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';

import { MainLayout } from './components/MainLayout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AnnotationPage } from './pages/AnnotationPage';
import { AnalysisPage } from './pages/AnalysisPage';
import { DashboardPage } from './pages/DashboardPage';
import { ImportPage } from './pages/ImportPage';
import { LoginPage } from './pages/LoginPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { UsersPage } from './pages/UsersPage';

const GuardedPage = ({ children }: { children: ReactNode }) => (
  <ProtectedRoute>
    <MainLayout>{children}</MainLayout>
  </ProtectedRoute>
);

export const App = () => (
  <Router>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <GuardedPage>
            <DashboardPage />
          </GuardedPage>
        }
      />
      <Route
        path="/projects"
        element={
          <GuardedPage>
            <ProjectsPage />
          </GuardedPage>
        }
      />
      <Route
        path="/imports"
        element={
          <GuardedPage>
            <ImportPage />
          </GuardedPage>
        }
      />
      <Route
        path="/analysis"
        element={
          <GuardedPage>
            <AnalysisPage />
          </GuardedPage>
        }
      />
      <Route
        path="/annotations"
        element={
          <GuardedPage>
            <AnnotationPage />
          </GuardedPage>
        }
      />
      <Route
        path="/users"
        element={
          <GuardedPage>
            <UsersPage />
          </GuardedPage>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </Router>
);
