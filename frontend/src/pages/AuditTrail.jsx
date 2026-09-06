import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ShieldCheck, ShieldAlert, CheckCircle2, Link2, ExternalLink, RefreshCw, Key } from 'lucide-react';
import RiskBadge from '../components/RiskBadge';

const AuditTrail = () => {
  const [logs, setLogs] = useState([]);
  const [verification, setVerification] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchAuditData = async () => {
    setLoading(true);
    try {
      const [logsRes, verifyRes] = await Promise.all([
        axios.get('/api/audit/logs?limit=50'),
        axios.get('/api/audit/verify')
      ]);
      setLogs(logsRes.data.items || []);
      setVerification(verifyRes.data);
    } catch (err) {
      console.error('Failed to load cryptographic audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditData();
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="text-emerald-400" size={26} />
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Cryptographic Audit Trail
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Tamper-evident SHA-256 hash-linked blockchain for all merchant risk decisions and policy enforcements.
          </p>
        </div>

        <button
          onClick={fetchAuditData}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-xs font-medium text-slate-200 transition self-start md:self-auto"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Re-verify Chain</span>
        </button>
      </div>

      {/* Verification Status Card */}
      {verification && (
        <div
          className={`p-5 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
            verification.valid
              ? 'bg-emerald-950/20 border-emerald-900/60'
              : 'bg-rose-950/20 border-rose-900/60'
          }`}
        >
          <div className="flex items-center gap-3">
            {verification.valid ? (
              <CheckCircle2 className="text-emerald-400" size={32} />
            ) : (
              <ShieldAlert className="text-rose-400" size={32} />
            )}
            <div>
              <div className="text-sm font-bold text-white flex items-center gap-2">
                <span>{verification.valid ? 'Cryptographic Chain Valid & Intact' : 'Chain Integrity Compromised'}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                  SHA-256
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {verification.message || 'Every block accurately reflects decision metadata.'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs font-mono text-slate-400">
            <div>
              <span className="text-slate-500">Verified Records:</span>{' '}
              <span className="text-white font-semibold">{verification.total_records}</span>
            </div>
            <div>
              <span className="text-slate-500">Last Verified:</span>{' '}
              <span className="text-slate-300">
                {new Date(verification.last_verified).toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Log Entries Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="text-xs font-mono text-slate-300 uppercase tracking-wider font-semibold">
            Immutable Decision Ledger
          </div>
          <div className="text-xs font-mono text-slate-500">Showing last 50 blocks</div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 font-mono text-[11px] uppercase border-b border-slate-800">
              <tr>
                <th className="px-5 py-3">Block ID</th>
                <th className="px-5 py-3">Transaction</th>
                <th className="px-5 py-3">Score / Band</th>
                <th className="px-5 py-3">Enforced Action</th>
                <th className="px-5 py-3">SHA-256 Hash</th>
                <th className="px-5 py-3">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {loading ? (
                <tr>
                  <td colSpan="6" className="text-center py-10 text-slate-500">
                    Traversing cryptographic nodes...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-10 text-slate-400">
                    No audit records logged yet.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr
                    key={log.log_id}
                    onClick={() => setSelectedLog(log)}
                    className="hover:bg-slate-800/40 transition cursor-pointer"
                  >
                    <td className="px-5 py-3 font-semibold text-emerald-400">{log.log_id}</td>
                    <td className="px-5 py-3 text-slate-300">TXN-{log.transaction_id.slice(0, 8)}</td>
                    <td className="px-5 py-3">
                      <span className="font-bold text-white mr-2">{log.risk_score}</span>
                      <RiskBadge level={log.risk_level} />
                    </td>
                    <td className="px-5 py-3 text-slate-300">{log.recommended_action}</td>
                    <td className="px-5 py-3 text-slate-400 text-[11px]">
                      {log.hash ? log.hash.slice(0, 16) + '...' : 'GENESIS'}
                    </td>
                    <td className="px-5 py-3 text-slate-500 text-[11px]">
                      {log.created_at ? new Date(log.created_at).toLocaleTimeString() : 'N/A'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Block Modal / Card */}
      {selectedLog && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 max-w-2xl w-full rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Key className="text-emerald-400" size={18} />
                <span className="font-mono text-sm font-bold text-white">{selectedLog.log_id}</span>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕ Close
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div>
                <span className="text-slate-500">Block SHA-256 Hash:</span>
                <div className="p-2 rounded bg-slate-950 text-emerald-400 break-all select-all mt-1">
                  {selectedLog.hash || 'GENESIS'}
                </div>
              </div>

              <div>
                <span className="text-slate-500">Parent Link (Previous Hash):</span>
                <div className="p-2 rounded bg-slate-950 text-slate-400 break-all select-all mt-1">
                  {selectedLog.previous_hash || 'GENESIS_BLOCK_BHARATSHIELD'}
                </div>
              </div>

              <div>
                <span className="text-slate-500">Reasons Summary:</span>
                <div className="p-2 rounded bg-slate-950 text-slate-300 mt-1">
                  {selectedLog.reasons_summary}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditTrail;
