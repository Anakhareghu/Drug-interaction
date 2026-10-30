import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import Home from './pages/Home';
import Methodology from './pages/Methodology';
import Dashboard from './pages/Dashboard';
import DrugExplorer from './pages/DrugExplorer';
import PKAnalysis from './pages/PKAnalysis';
import NetworkAnalysis from './pages/NetworkAnalysis';
import IntegratedResults from './pages/IntegratedResults';
import Login from './pages/Login';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Standalone Login Route without sidebar */}
          <Route path="/login" element={<Login />} />

          {/* Main App Layout */}
          <Route
            path="/*"
            element={
              <div style={{ display: 'flex', minHeight: '100vh' }}>
                <Sidebar />
                <main style={{ flex: 1, overflowY: 'auto', padding: '1.75rem', background: '#f8fafc' }}>
                  <Routes>
                    {/* Publicly Accessible Information Routes */}
                    <Route path="/"            element={<Home />} />
                    <Route path="/methodology" element={<Methodology />} />

                    {/* Authenticated / Protected Research & Data Routes */}
                    <Route path="/dashboard"   element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                    <Route path="/explorer"    element={<ProtectedRoute><DrugExplorer /></ProtectedRoute>} />
                    <Route path="/pk-analysis" element={<ProtectedRoute><PKAnalysis /></ProtectedRoute>} />
                    <Route path="/network"     element={<ProtectedRoute><NetworkAnalysis /></ProtectedRoute>} />
                    <Route path="/results"     element={<ProtectedRoute><IntegratedResults /></ProtectedRoute>} />

                    {/* Catch all fallback */}
                    <Route path="*"            element={<Navigate to="/" replace />} />
                  </Routes>
                </main>
              </div>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
