import React, { useState, useEffect } from 'react';
import { Search, FolderOpen, AlertCircle, CheckCircle2, User, Clock, MessageSquare, ShieldAlert } from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import { casesAPI } from '../services/api';

const Investigations = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState(null);
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [analystNote, setAnalystNote] = useState('');
  const [updating, setUpdating] = useState(false);

  const fetchCases = async () => {
    try {
      const data = await casesAPI.listCases();
      setCases(data || []);
      if (data && data.length > 0 && !selectedCase) {
        setSelectedCase(data[0]);
      }
    } catch (err) {
      console.error('Failed loading investigation cases:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleUpdateStatus = async (newStatus) => {
    if (!selectedCase) return;
    setUpdating(true);
    try {
      const data = await casesAPI.updateCase(selectedCase.case_id, {
        status: newStatus,
        notes: analystNote ? `${selectedCase.notes || ''}\n[${new Date().toLocaleTimeString()}]: ${analystNote}` : selectedCase.notes
      });
      setSelectedCase(data);
      setAnalystNote('');
      fetchCases();
    } catch (err) {
      console.error('Error updating case:', err);
    } finally {
      setUpdating(false);
    }
  };

  const filteredCases = cases.filter((c) => {
    if (activeFilter === 'ALL') return true;
    return c.status === activeFilter;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <Search className="text-emerald-400" size={26} />
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Case Management & Investigations
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Enterprise workflow for risk officers: assign, review, escalate, and resolve elevated threat holdings.
          </p>
        </div>

        {/* Tab Filters */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-medium">
          {['ALL', 'OPEN', 'UNDER_REVIEW', 'ESCALATED', 'RESOLVED'].map((status) => (
            <button
              key={status}
              onClick={() => setActiveFilter(status)}
              className={`px-3 py-1.5 rounded-lg transition ${
                activeFilter === status
                  ? 'bg-emerald-500 text-slate-950 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {status.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Main Investigation Split Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Cases List */}
        <div className="lg:col-span-5 space-y-3">
          {loading ? (
            <div className="p-12 text-center text-slate-500 font-mono text-xs">Loading investigation files...</div>
          ) : filteredCases.length === 0 ? (
            <div className="p-8 rounded-xl bg-slate-900/40 border border-slate-800 text-center text-slate-400 text-sm">
              No active cases matching the filter.
            </div>
          ) : (
            filteredCases.map((c) => {
              const isSelected = selectedCase && selectedCase.case_id === c.case_id;
              return (
                <div
                  key={c.case_id}
                  onClick={() => setSelectedCase(c)}
                  className={`p-4 rounded-xl border transition cursor-pointer space-y-2 ${
                    isSelected
                      ? 'border-emerald-500 bg-emerald-500/5'
                      : 'border-slate-800/80 bg-slate-900/40 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-white">{c.case_id}</span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase font-semibold ${
                        c.status === 'RESOLVED'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : c.status === 'ESCALATED'
                          ? 'bg-rose-500/20 text-rose-400'
                          : 'bg-amber-500/20 text-amber-400'
                      }`}
                    >
                      {c.status.replace('_', ' ')}
                    </span>
                  </div>

                  <div className="text-xs text-slate-300 line-clamp-1">{c.title}</div>

                  <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono pt-1">
                    <span>TXN-{c.transaction_id.slice(0, 8)}</span>
                    <span>Priority: {c.priority}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Selected Case Workspace */}
        <div className="lg:col-span-7">
          {selectedCase ? (
            <div className="bg-slate-900/40 p-6 rounded-2xl border border-slate-800 space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-white font-mono">{selectedCase.case_id}</h2>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                      {selectedCase.priority}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1">{selectedCase.title}</div>
                </div>

                <div className="text-right text-xs text-slate-500 font-mono">
                  Assigned: {selectedCase.assigned_to || 'Unassigned'}
                </div>
              </div>

              {/* Status Progression Pipeline */}
              <div>
                <div className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2">
                  Investigation Pipeline
                </div>
                <div className="grid grid-cols-4 gap-2 text-center text-xs font-mono">
                  {['OPEN', 'UNDER_REVIEW', 'ESCALATED', 'RESOLVED'].map((st, i) => {
                    const isCurrent = selectedCase.status === st;
                    return (
                      <div
                        key={st}
                        className={`p-2 rounded-lg border ${
                          isCurrent
                            ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300 font-bold'
                            : 'bg-slate-950/40 border-slate-800 text-slate-500'
                        }`}
                      >
                        {st.replace('_', ' ')}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Transaction Telemetry */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2 text-xs">
                <div className="font-semibold text-slate-300 font-mono">Transaction Reference</div>
                <div className="font-mono text-slate-400 flex items-center justify-between">
                  <span>ID: {selectedCase.transaction_id}</span>
                  <a
                    href={`/transactions/${selectedCase.transaction_id}`}
                    className="text-emerald-400 hover:underline"
                  >
                    View Deep Telemetry →
                  </a>
                </div>
              </div>

              {/* Notes Feed */}
              <div className="space-y-2">
                <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                  Analyst Log & Notes
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 max-h-36 overflow-y-auto text-xs text-slate-300 font-mono whitespace-pre-wrap">
                  {selectedCase.notes || 'No analyst notes recorded for this investigation.'}
                </div>

                <textarea
                  rows="2"
                  value={analystNote}
                  onChange={(e) => setAnalystNote(e.target.value)}
                  placeholder="Append observation or finding..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
                <button
                  onClick={() => handleUpdateStatus('UNDER_REVIEW')}
                  disabled={updating}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition"
                >
                  Mark Under Review
                </button>
                <button
                  onClick={() => handleUpdateStatus('ESCALATED')}
                  disabled={updating}
                  className="px-4 py-2 rounded-xl bg-rose-950/40 border border-rose-800/60 hover:bg-rose-900/60 text-xs font-medium text-rose-300 transition"
                >
                  Escalate to Risk Lead
                </button>
                <button
                  onClick={() => handleUpdateStatus('RESOLVED')}
                  disabled={updating}
                  className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-xs font-semibold text-slate-950 transition"
                >
                  Resolve Case
                </button>
              </div>
            </div>
          ) : (
            <div className="h-96 flex items-center justify-center text-slate-500 font-mono text-sm border border-slate-800 rounded-2xl bg-slate-900/20">
              Select an investigation case to view dossier.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Investigations;
