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

function AppContent() {
  const navigate = useNavigate();

  const handleTransactionInjected = (scoredTxn) => {
    // When simulation button is clicked in Navbar, optionally navigate to its details
    if (scoredTxn && scoredTxn.transaction_id) {
      navigate(`/transactions/${scoredTxn.transaction_id}`);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 selection:bg-emerald-500 selection:text-slate-950">
      {/* Fixed Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950">
        <Navbar onTransactionInjected={handleTransactionInjected} />

        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/transactions/:id" element={<TransactionDetails />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/assistant" element={<RiskAssistant />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
