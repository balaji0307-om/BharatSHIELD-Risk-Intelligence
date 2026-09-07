import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Shield, Lock, Mail, AlertCircle, ArrowRight, CheckCircle2, RefreshCw } from 'lucide-react';
import { authAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import CaptchaWidget from '../components/CaptchaWidget';

const Login = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [captchaToken, setCaptchaToken] = useState(null);
  const [error, setError] = useState(null);
  const [captchaError, setCaptchaError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setCaptchaError(null);

    if (!captchaToken) {
      setCaptchaError('Please complete the CAPTCHA challenge before signing in.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await authAPI.login({
        email: identifier.includes('@') ? identifier : undefined,
        merchantId: !identifier.includes('@') ? identifier : undefined,
        password,
        rememberMe,
        captchaToken,
      });

      login(res, rememberMe);
      navigate(from, { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 404 || detail === 'Not Found') {
        setError('Authentication service is temporarily unreachable. Please retry in a few moments.');
      } else if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg || JSON.stringify(d)).join(', '));
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Authentication failed. Please verify credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-emerald-500 selection:text-slate-950">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center z-10">
        <div className="inline-flex items-center justify-center p-3 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl mb-4">
          <img src="/logo.svg" alt="BharatSHIELD" className="w-10 h-10" />
        </div>
        <h2 className="text-3xl font-black tracking-tight text-white">
          Sign In to <span className="text-emerald-400">BharatSHIELD</span>
        </h2>
        <p className="mt-1.5 text-xs text-slate-400">
          AI-Powered Merchant Risk Intelligence & Fraud Defense Console
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md z-10">
        <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800/90 py-8 px-6 sm:px-8 rounded-3xl shadow-2xl shadow-slate-950/80 space-y-6">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              <div className="leading-relaxed">{error}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider font-mono">
                Merchant Email or ID
              </label>
              <div className="relative">
                <input
                  type="text"
                  required
                  value={identifier}
                  onChange={(e) => {
                    setIdentifier(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="admin@bharatshield.com or MER_razorpay_001"
                  className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition"
                />
                <Mail size={16} className="absolute right-3.5 top-3 text-slate-500" />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-emerald-400 hover:text-emerald-300 transition"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="••••••••"
                  className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition"
                />
                <Lock size={16} className="absolute right-3.5 top-3 text-slate-500" />
              </div>
            </div>

            {/* Remember Me Checkbox */}
            <div className="flex items-center justify-between py-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded bg-slate-950 border-slate-700 text-emerald-500 focus:ring-0 focus:ring-offset-0 cursor-pointer"
                />
                <span className="text-xs text-slate-300">
                  Remember me <span className="text-slate-500">(30-day session)</span>
                </span>
              </label>
            </div>

            {/* CAPTCHA Widget */}
            <div className="pt-1">
              <CaptchaWidget onVerify={setCaptchaToken} error={captchaError} />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-sm font-bold shadow-lg shadow-emerald-950/40 flex items-center justify-center gap-2 transition active:scale-[0.98] disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  <span>Validating Credentials...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <div className="pt-3 border-t border-slate-800/80 text-center">
            <p className="text-xs text-slate-400">
              New merchant organization?{' '}
              <Link to="/signup" className="text-emerald-400 font-bold hover:underline">
                Create an account
              </Link>
            </p>
          </div>
        </div>

        {/* Demo Fast Login Banner */}
        <div className="mt-4 p-3 rounded-2xl bg-slate-900/40 border border-slate-800/60 text-center">
          <span className="text-[11px] text-slate-400">Demo Login: </span>
          <code className="text-[11px] font-mono text-emerald-400 font-bold bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
            MER_razorpay_001
          </code>{' '}
          <span className="text-[11px] text-slate-500">/</span>{' '}
          <code className="text-[11px] font-mono text-emerald-400 font-bold bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
            demo123
          </code>
        </div>
      </div>
    </div>
  );
};

export default Login;
