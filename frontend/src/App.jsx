import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import { FiltersProvider } from './context/FiltersContext';
import { LocaleProvider } from './context/LocaleContext';
import { ThemeProvider } from './context/ThemeContext';
import Layout from './components/layout/Layout';
import ComingSoon from './pages/ComingSoon';
import GlobalOverview from './pages/GlobalOverview';
import IPLifecycle from './pages/IPLifecycle';
import Login from './pages/Login';
import Register from './pages/Register';

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <LocaleProvider>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              <Route element={<ProtectedRoute />}>
                <Route
                  element={
                    <FiltersProvider>
                      <Layout />
                    </FiltersProvider>
                  }
                >
                  <Route index element={<GlobalOverview />} />
                  <Route path="lifecycle" element={<IPLifecycle />} />
                  <Route path="upload" element={<ComingSoon pageKey="upload" />} />
                  <Route path="prediction" element={<ComingSoon pageKey="prediction" />} />
                  <Route path="decision" element={<ComingSoon pageKey="decision" />} />
                </Route>
              </Route>

              <Route path="*" element={<Navigate to="/lifecycle" replace />} />
            </Routes>
          </AuthProvider>
        </LocaleProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
