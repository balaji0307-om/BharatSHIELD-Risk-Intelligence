import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Network, ShieldAlert, Laptop, MapPin, Layers, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import RiskBadge from '../components/RiskBadge';

const FraudNetwork = () => {
  const [networkData, setNetworkData] = useState({ nodes: [], edges: [], clusters: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const navigate = useNavigate();

  const fetchNetwork = async () => {
    try {
      const res = await axios.get('/api/fraud-network');
      setNetworkData(res.data || { nodes: [], edges: [], clusters: [] });
    } catch (err) {
      console.error('Failed to load fraud network:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNetwork();
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <Network className="text-emerald-400" size={26} />
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Fraud Network Intelligence
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Entity graph linking shared devices, IP subnet hops, and coordinated transaction syndicates.
          </p>
        </div>

        <button
          onClick={fetchNetwork}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-xs font-medium text-slate-200 transition self-start md:self-auto"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Graph</span>
        </button>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Identified Clusters</div>
            <div className="text-2xl font-black text-rose-400 mt-1">{networkData.clusters.length}</div>
          </div>
          <Layers className="text-rose-500" size={26} />
        </div>
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Compromised Devices</div>
            <div className="text-2xl font-black text-orange-400 mt-1">
              {networkData.nodes.filter((n) => n.type === 'device').length}
            </div>
          </div>
          <Laptop className="text-orange-500" size={26} />
        </div>
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Connected Transactions</div>
            <div className="text-2xl font-black text-emerald-400 mt-1">
              {networkData.nodes.filter((n) => n.type === 'transaction').length}
            </div>
          </div>
          <ShieldAlert className="text-emerald-400" size={26} />
        </div>
      </div>

      {/* Interactive Entity SVG Canvas */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6 relative overflow-hidden">
        <div className="flex items-center justify-between mb-4">
          <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
            Multi-Entity Relational Topology
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" /> Device</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" /> Transaction</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-sky-400 inline-block" /> IP / Location</span>
          </div>
        </div>

        {loading ? (
          <div className="h-96 flex items-center justify-center text-slate-500 font-mono text-sm">
            Generating graph coordinates...
          </div>
        ) : networkData.nodes.length === 0 ? (
          <div className="h-96 flex items-center justify-center text-slate-400 font-mono text-sm">
            No active multi-transaction rings detected. All transactions exhibit isolated fingerprints.
          </div>
        ) : (
          <div className="w-full h-96 relative border border-slate-900 rounded-xl bg-slate-900/20 flex items-center justify-center">
            {/* SVG Visualizer */}
            <svg className="w-full h-full" viewBox="0 0 800 400">
              {/* Edges */}
              {networkData.edges.map((edge, i) => {
                const sIndex = networkData.nodes.findIndex((n) => n.id === edge.source);
                const tIndex = networkData.nodes.findIndex((n) => n.id === edge.target);
                if (sIndex < 0 || tIndex < 0) return null;

                const sx = 100 + (sIndex * 70) % 650;
                const sy = 60 + ((sIndex * 110) % 280);
                const tx = 100 + (tIndex * 70) % 650;
                const ty = 60 + ((tIndex * 110) % 280);

                return (
                  <line
                    key={i}
                    x1={sx}
                    y1={sy}
                    x2={tx}
                    y2={ty}
                    stroke="#334155"
                    strokeWidth="1.5"
                    strokeDasharray={edge.relationship === 'same_ip' ? '4,4' : undefined}
                  />
                );
              })}

              {/* Nodes */}
              {networkData.nodes.map((node, i) => {
                const x = 100 + (i * 70) % 650;
                const y = 60 + ((i * 110) % 280);
                const isDevice = node.type === 'device';
                const isTxn = node.type === 'transaction';
                const fillColor = isDevice ? '#f43f5e' : isTxn ? '#f59e0b' : '#38bdf8';

                return (
                  <g
                    key={node.id}
                    className="cursor-pointer transition-transform hover:scale-125"
                    onClick={() => {
                      setSelectedNode(node);
                      if (isTxn) navigate(`/transactions/${node.id}`);
                    }}
                  >
                    <circle
                      cx={x}
                      cy={y}
                      r={isDevice ? 14 : isTxn ? 10 : 8}
                      fill={fillColor}
                      stroke="#0f172a"
                      strokeWidth="2"
                    />
                    <text
                      x={x}
                      y={y + 22}
                      textAnchor="middle"
                      fill="#94a3b8"
                      fontSize="9"
                      fontFamily="monospace"
                    >
                      {node.label ? node.label.slice(0, 10) : node.id.slice(0, 8)}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        )}
      </div>

      {/* Identified Syndicate Clusters */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Layers size={18} className="text-rose-400" />
          Detected Ring Clusters
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {networkData.clusters.map((cluster) => (
            <div
              key={cluster.id}
              className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Laptop className="text-rose-400" size={18} />
                  <span className="font-mono text-sm font-semibold text-slate-200">
                    Device: {cluster.device_id}
                  </span>
                </div>
                <RiskBadge level={cluster.risk_score >= 75 ? 'CRITICAL' : 'HIGH'} />
              </div>

              <div className="text-xs text-slate-400 space-y-1">
                <div>
                  <span className="text-slate-500">Linked Transactions:</span>{' '}
                  <span className="text-slate-200 font-mono font-medium">{cluster.transactions.length}</span>
                </div>
                <div>
                  <span className="text-slate-500">Cross-Geographies:</span>{' '}
                  <span className="text-slate-200">{cluster.locations.join(', ') || 'Multi-city hops'}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800 flex flex-wrap gap-2">
                {cluster.transactions.map((txId) => (
                  <button
                    key={txId}
                    onClick={() => navigate(`/transactions/${txId}`)}
                    className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[11px] font-mono text-slate-300 transition"
                  >
                    TXN-{txId.slice(0, 8)}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FraudNetwork;
