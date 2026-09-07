import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import TransactionDetails from './pages/TransactionDetails';
import Alerts from './pages/Alerts';
import Analytics from './pages/Analytics';
import RiskAssistant from './pages/RiskAssistant';
import Threats from './pages/Threats';
import FraudNetwork from './pages/FraudNetwork';
import RiskSimulator from './pages/RiskSimulator';
import Investigations from './pages/Investigations';
import AuditTrail from './pages/AuditTrail';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import CinematicSplash from './components/CinematicSplash';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';

function AuthenticatedApp() {
  const navigate = useNavigate();
  const [showSplash, setShowSplash] = useState(() => {
    return !sessionStorage.getItem('bharatshield_intro_seen');
  });

  const handleSplashComplete = () => {
    sessionStorage.setItem('bharatshield_intro_seen', 'true');
    setShowSplash(false);
  };

  const handleTransactionInjected = (scoredTxn) => {
    if (scoredTxn && scoredTxn.transaction_id) {
      navigate(`/transactions/${scoredTxn.transaction_id}`);
    }
  };

  return (
    <>
      {showSplash && <CinematicSplash onComplete={handleSplashComplete} />}
      <div className="flex min-h-screen bg-slate-950 text-slate-100 selection:bg-emerald-500 selection:text-slate-950">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950">
          <Navbar onTransactionInjected={handleTransactionInjected} />
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/threats" element={<Threats />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/transactions/:id" element={<TransactionDetails />} />
              <Route path="/fraud-network" element={<FraudNetwork />} />
              <Route path="/investigations" element={<Investigations />} />
              <Route path="/simulator" element={<RiskSimulator />} />
              <Route path="/assistant" element={<RiskAssistant />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/audit" element={<AuditTrail />} />
            </Routes>
          </main>
        </div>
      </div>
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Auth Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />

          {/* All internal application routes are protected */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AuthenticatedApp />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
