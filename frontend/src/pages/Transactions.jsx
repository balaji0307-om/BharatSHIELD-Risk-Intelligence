import React, { useState, useEffect } from 'react';
import { Filter, ChevronLeft, ChevronRight, RefreshCw, Search } from 'lucide-react';
import TransactionTable from '../components/TransactionTable';
import { transactionsAPI } from '../services/api';

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [riskFilter, setRiskFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const fetchTransactions = async (currentPage = 1, currentRisk = '') => {
    setIsLoading(true);
    try {
      const params = {
        page: currentPage,
        page_size: 15,
      };
      if (currentRisk) {
        params.risk_level = currentRisk;
      }
      const data = await transactionsAPI.listTransactions(params);
      setTransactions(data.items || []);
      setTotal(data.total || 0);
      setPage(data.page || 1);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error('Error listing transactions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions(page, riskFilter);
  }, [page, riskFilter]);

  const handleFilterChange = (filter) => {
    setRiskFilter(filter);
    setPage(1);
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white">
            Transaction Risk Ledger
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Complete audit trail of all merchant payment evaluations and risk scores.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {['', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((level) => {
            const isSelected = riskFilter === level;
            const label = level === '' ? 'ALL BANDS' : level;
            return (
              <button
                key={level}
                onClick={() => handleFilterChange(level)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold tracking-wider transition ${
                  isSelected
                    ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20'
                    : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 border border-slate-700/60'
                }`}
              >
                {label}
              </button>
            );
          })}

          <button
            onClick={() => fetchTransactions(page, riskFilter)}
            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 ml-2"
            title="Refresh Ledger"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Table */}
      <TransactionTable transactions={transactions} isLoading={isLoading} />

      {/* Pagination Controls */}
      <div className="flex items-center justify-between pt-2">
        <span className="text-xs text-slate-400 font-mono">
          Showing {transactions.length} of {total} transactions
        </span>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-700"
          >
            <ChevronLeft size={14} /> Previous
          </button>
          <span className="text-xs font-mono text-slate-400 px-2">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-700"
          >
            Next <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Transactions;
