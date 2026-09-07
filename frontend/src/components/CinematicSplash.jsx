import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

/**
 * Cinematic Splash / Landing Intro Screen for BHARATSHIELD
 *
 * Design Spec:
 * - High-end, trustworthy, national digital security shield coming online.
 * - Extremely clean, minimal, low-contrast, almost-white / very light cool background.
 * - Subtle central atmospheric blue glow + faint digital grid / particles.
 * - Original futuristic geometric shield centerpiece with Ashoka Chakra 24-spoke inspired core,
 *   hexagonal circuit traces, and scanning light pulse.
 * - "BHARATSHIELD" typography: Deep navy "BHARAT" + sophisticated Saffron→Gold→Green gradient "SHIELD".
 * - Tagline: "PROTECTING INDIA'S DIGITAL FUTURE"
 * - Abstract Indian digital infrastructure & urban skyline silhouette along lower horizon.
 * - Bottom Message: "India Focused. Safety First." with an elegant animated progress indicator.
 * - Smooth fade out transition to main application upon completion (or via quick skip).
 */

const CinematicSplash = ({ onComplete, isLanding = false }) => {
  const [phase, setPhase] = useState(0);
  const [progress, setProgress] = useState(0);
  const [isExiting, setIsExiting] = useState(false);

  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Stage 1: Initial load
    const t1 = setTimeout(() => setPhase(1), 100); // BG + faint grid
    const t2 = setTimeout(() => setPhase(2), 600); // Particles & soft blue atmosphere
    const t3 = setTimeout(() => setPhase(3), 1200); // Shield emblem materializes
    const t4 = setTimeout(() => setPhase(4), 1900); // Scanline across shield
    const t5 = setTimeout(() => setPhase(5), 2400); // Brand "BHARATSHIELD" fades/slides in
    const t6 = setTimeout(() => setPhase(6), 2900); // Tagline appears
    const t7 = setTimeout(() => setPhase(7), 3300); // Horizon digital silhouette
    const t8 = setTimeout(() => setPhase(8), 3700); // Bottom message & progress start

    return () => {
      [t1, t2, t3, t4, t5, t6, t7, t8].forEach(clearTimeout);
    };
  }, []);

  // Smooth progress bar counter from 3.7s to 6.2s
  useEffect(() => {
    if (phase >= 8) {
      const startTime = Date.now();
      const duration = 2500; // 2.5 seconds progress fill

      const interval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const pct = Math.min(100, Math.round((elapsed / duration) * 100));
        setProgress(pct);

        if (pct >= 100) {
          clearInterval(interval);
          if (!isLanding) {
            setTimeout(() => {
              handleExit();
            }, 400);
          }
        }
      }, 25);

      return () => clearInterval(interval);
    }
  }, [phase, isLanding]);

  const handleExit = () => {
    setIsExiting(true);
    setTimeout(() => {
      if (onComplete) {
        onComplete();
      } else {
        navigate(isAuthenticated ? '/dashboard' : '/login');
      }
    }, 600);
  };

  return (
    <div
      className={`fixed inset-0 z-50 overflow-hidden select-none flex flex-col justify-between items-center transition-opacity duration-700 ease-out ${
        isExiting ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
      style={{
        backgroundColor: '#f8fafc',
        backgroundImage: 'radial-gradient(ellipse 70% 60% at 50% 42%, rgba(224, 242, 254, 0.45), rgba(248, 250, 252, 0.95))'
      }}
    >
      {/* 1. Subtle Digital Background Grid */}
      <div
        className={`absolute inset-0 pointer-events-none transition-opacity duration-1000 ${
          phase >= 1 ? 'opacity-100' : 'opacity-0'
        }`}
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(148, 163, 184, 0.08) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(148, 163, 184, 0.08) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px',
          maskImage: 'radial-gradient(circle at center, black 30%, transparent 80%)',
          WebkitMaskImage: 'radial-gradient(circle at center, black 30%, transparent 80%)'
        }}
      />

      {/* 2. Soft Atmospheric Radial Glow */}
      <div
        className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full pointer-events-none transition-opacity duration-1500 blur-3xl ${
          phase >= 2 ? 'opacity-70' : 'opacity-0'
        }`}
        style={{
          background: 'radial-gradient(circle, rgba(186, 230, 253, 0.5) 0%, rgba(224, 242, 254, 0.2) 50%, transparent 75%)'
        }}
      />

      {/* 3. Tiny Ambient Digital Particle Nodes */}
      <div
        className={`absolute inset-0 pointer-events-none transition-opacity duration-1000 ${
          phase >= 2 ? 'opacity-100' : 'opacity-0'
        }`}
      >
        {[
          { x: 18, y: 22, s: 3, delay: '0s' },
          { x: 82, y: 19, s: 2.5, delay: '1s' },
          { x: 26, y: 68, s: 3, delay: '0.5s' },
          { x: 74, y: 72, s: 2, delay: '1.5s' },
          { x: 50, y: 14, s: 3, delay: '0.8s' },
          { x: 12, y: 48, s: 2.5, delay: '1.2s' },
          { x: 88, y: 44, s: 3, delay: '0.3s' },
        ].map((pt, i) => (
          <span
            key={i}
            className="absolute rounded-full bg-sky-400/40 animate-pulse"
            style={{
              left: `${pt.x}%`,
              top: `${pt.y}%`,
              width: `${pt.s}px`,
              height: `${pt.s}px`,
              animationDelay: pt.delay,
              boxShadow: '0 0 6px rgba(56, 189, 248, 0.4)'
            }}
          />
        ))}
      </div>

      {/* Top Bar: Discreet Security Seal & Action Options */}
      <header className="w-full max-w-6xl mx-auto px-6 sm:px-8 pt-6 sm:pt-8 flex items-center justify-between z-20">
        <div
          className={`flex items-center gap-2.5 transition-all duration-700 ${
            phase >= 1 ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'
          }`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
          <span className="text-[10px] sm:text-[11px] font-mono tracking-widest text-slate-500 uppercase font-semibold">
            NATIONAL CYBER DEFENSE INITIATIVE
          </span>
        </div>

        {isLanding ? (
          <div
            className={`flex items-center gap-2 sm:gap-3 transition-all duration-700 ${
              phase >= 1 ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'
            }`}
          >
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="text-xs font-mono tracking-wider text-white px-4 py-1.5 rounded-full bg-emerald-600 hover:bg-emerald-500 shadow-md shadow-emerald-950/30 font-bold transition-all flex items-center gap-1.5"
              >
                <span>Enter Console</span>
                <ArrowRight size={13} />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-xs font-mono tracking-wider text-slate-700 hover:text-slate-950 transition-colors uppercase px-3 py-1.5 rounded-full border border-slate-300 hover:border-slate-400 bg-white/80 backdrop-blur font-semibold"
                >
                  Sign In
                </Link>
                <Link
                  to="/signup"
                  className="text-xs font-mono tracking-wider text-white px-3.5 py-1.5 rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 shadow-sm font-bold transition-all"
                >
                  Get Started
                </Link>
                <Link
                  to="/dashboard"
                  className="text-xs font-mono tracking-wider text-slate-900 hover:text-black uppercase px-3.5 py-1.5 rounded-full border border-slate-400/80 hover:border-slate-600 bg-white font-bold transition-all hidden sm:inline-flex items-center gap-1 shadow-sm"
                >
                  <span>Launch Console</span>
                  <ArrowRight size={13} />
                </Link>
              </>
            )}
          </div>
        ) : (
          <button
            onClick={handleExit}
            className="text-[11px] font-mono tracking-wider text-slate-600 hover:text-slate-900 transition-colors uppercase px-3 py-1 rounded-full border border-slate-300/80 hover:border-slate-400 bg-white/70 backdrop-blur"
          >
            Enter Platform ➔
          </button>
        )}
      </header>

      {/* Centerpiece: Emblem + Brand Title + Tagline */}
      <main className="flex-1 flex flex-col items-center justify-center -mt-8 z-10 text-center px-4">
        {/* Shield Emblem Container */}
        <div
          className={`relative w-48 h-56 md:w-56 md:h-64 flex items-center justify-center transition-all duration-1000 ease-out transform ${
            phase >= 3 ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-90 translate-y-4'
          }`}
        >
          {/* Subtle Outer Pulse Ring */}
          <div className="absolute inset-0 rounded-[38%] border border-sky-300/30 scale-110 pointer-events-none animate-pulse" />

          {/* SVG Futuristic Shield Graphic */}
          <svg
            className="w-full h-full drop-shadow-[0_12px_32px_rgba(14,116,144,0.14)]"
            viewBox="0 0 200 240"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              {/* Outer Plate Gradient: Refined metallic white-silver with icy blue rim */}
              <linearGradient id="shieldPlate" x1="20" y1="10" x2="180" y2="230" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#ffffff" />
                <stop offset="45%" stopColor="#f1f5f9" />
                <stop offset="100%" stopColor="#e2e8f0" />
              </linearGradient>

              {/* Navy / Indigo inner field gradient */}
              <linearGradient id="innerField" x1="50" y1="40" x2="150" y2="200" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#0f172a" />
                <stop offset="50%" stopColor="#0a192f" />
                <stop offset="100%" stopColor="#020617" />
              </linearGradient>

              {/* Tricolor delicate circuit trace gradient */}
              <linearGradient id="tricolorAccent" x1="0" y1="0" x2="200" y2="0" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#f97316" />
                <stop offset="50%" stopColor="#fbbf24" />
                <stop offset="100%" stopColor="#10b981" />
              </linearGradient>

              {/* Cyan security trace */}
              <linearGradient id="cyanLine" x1="0" y1="0" x2="0" y2="240" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#38bdf8" />
                <stop offset="100%" stopColor="#0284c7" />
              </linearGradient>

              {/* Scanning light gradient */}
              <linearGradient id="scanGlow" x1="0" y1="0" x2="0" y2="100%">
                <stop offset="0%" stopColor="transparent" />
                <stop offset="50%" stopColor="rgba(56, 189, 248, 0.45)" />
                <stop offset="100%" stopColor="transparent" />
              </linearGradient>

              {/* Mask for scanning light */}
              <clipPath id="shieldClip">
                <path d="M100 12 L180 44 C180 144 148 200 100 230 C52 200 20 144 20 44 Z" />
              </clipPath>
            </defs>

            {/* Layer 1: Outer Hex Shield Frame */}
            <path
              d="M100 10 L184 44 C184 148 150 206 100 238 C50 206 16 148 16 44 Z"
              fill="url(#shieldPlate)"
              stroke="#cbd5e1"
              strokeWidth="1.5"
            />

            {/* Layer 2: Subtle Tricolor Pin-Stripe Rim */}
            <path
              d="M100 16 L178 47 C178 143 146 198 100 228 C54 198 22 143 22 47 Z"
              fill="none"
              stroke="url(#tricolorAccent)"
              strokeWidth="1.2"
              strokeOpacity="0.85"
            />

            {/* Layer 3: Inner Core Deep Dark Shield with Depth Shadow */}
            <path
              d="M100 24 L170 52 C170 138 142 188 100 216 C58 188 30 138 30 52 Z"
              fill="url(#innerField)"
              stroke="#1e293b"
              strokeWidth="1.5"
            />

            {/* Layer 4: Minimal Geometric Circuit Traces */}
            <g opacity="0.65" stroke="#38bdf8" strokeWidth="1" fill="none">
              {/* Top angled traces */}
              <path d="M54 62 L74 62 L84 72" />
              <path d="M146 62 L126 62 L116 72" />
              <circle cx="54" cy="62" r="1.5" fill="#38bdf8" />
              <circle cx="146" cy="62" r="1.5" fill="#38bdf8" />

              {/* Lower node convergences */}
              <path d="M60 140 L80 160 L100 160" />
              <path d="M140 140 L120 160 L100 160" />
              <circle cx="60" cy="140" r="1.5" fill="#38bdf8" />
              <circle cx="140" cy="140" r="1.5" fill="#38bdf8" />
            </g>

            {/* Layer 5: Ashoka-Inspired 24-Spoke Radial Core Centerpiece */}
            <g transform="translate(100, 112)">
              {/* Outer Chakra Ring */}
              <circle r="26" fill="none" stroke="#0284c7" strokeWidth="1.2" opacity="0.8" />
              <circle r="29" fill="none" stroke="#38bdf8" strokeWidth="0.75" strokeDasharray="3,3" opacity="0.6" />
              <circle r="12" fill="none" stroke="#38bdf8" strokeWidth="1" opacity="0.9" />
              <circle r="4" fill="#38bdf8" />

              {/* 24 Radial Spokes (Clean Geometric Lines) */}
              {[...Array(24)].map((_, idx) => {
                const angle = (idx * 360) / 24;
                return (
                  <line
                    key={idx}
                    x1="0"
                    y1="6"
                    x2="0"
                    y2="24"
                    stroke="#7dd3fc"
                    strokeWidth="0.8"
                    opacity="0.8"
                    transform={`rotate(${angle})`}
                  />
                );
              })}
            </g>

            {/* Layer 6: Scanning Light Beam (Materializes in phase 4) */}
            {phase >= 4 && (
              <g clipPath="url(#shieldClip)">
                <rect
                  x="0"
                  y="0"
                  width="200"
                  height="36"
                  fill="url(#scanGlow)"
                  className="animate-scan"
                  style={{
                    animation: 'scanMove 2.8s ease-in-out infinite'
                  }}
                />
              </g>
            )}
          </svg>
        </div>

        {/* Brand Name Typography */}
        <div
          className={`mt-8 transition-all duration-700 ease-out transform ${
            phase >= 5 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'
          }`}
        >
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-black tracking-tight font-sans flex items-center justify-center">
            {/* "BHARAT" in Deep Royal Navy */}
            <span
              style={{
                color: '#0a192f',
                letterSpacing: '-0.02em',
                textShadow: '0 2px 10px rgba(10, 25, 47, 0.08)'
              }}
            >
              BHARAT
            </span>

            {/* "SHIELD" with Sophisticated Saffron→Gold→Emerald Gradient */}
            <span
              className="bg-clip-text text-transparent ml-1"
              style={{
                backgroundImage: 'linear-gradient(135deg, #ea580c 0%, #d97706 45%, #059669 100%)',
                letterSpacing: '-0.02em'
              }}
            >
              SHIELD
            </span>
          </h1>
        </div>

        {/* Tagline Typography */}
        <div
          className={`mt-3 transition-all duration-700 ease-out delay-100 transform ${
            phase >= 6 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
          }`}
        >
          <p
            className="text-[11px] md:text-[13px] font-semibold tracking-[0.38em] uppercase"
            style={{
              color: '#475569',
              wordSpacing: '0.15em'
            }}
          >
            PROTECTING INDIA'S DIGITAL FUTURE
          </p>
        </div>
      </main>

      {/* Lower Section: Abstract Digital Infrastructure Silhouette + Bottom Message + Progress */}
      <footer className="w-full relative flex flex-col items-center z-10 pb-10 px-4">
        {/* Abstract Indian Digital Landscape & Connected Infrastructure Silhouette */}
        <div
          className={`w-full max-w-4xl h-20 md:h-24 pointer-events-none transition-opacity duration-1000 mb-4 ${
            phase >= 7 ? 'opacity-70' : 'opacity-0'
          }`}
        >
          <svg
            className="w-full h-full"
            viewBox="0 0 1000 120"
            fill="none"
            preserveAspectRatio="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <linearGradient id="silhouetteGrad" x1="0" y1="0" x2="0" y2="120" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#0284c7" stopOpacity="0.18" />
                <stop offset="60%" stopColor="#38bdf8" stopOpacity="0.08" />
                <stop offset="100%" stopColor="#f8fafc" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Abstract geometric cityscape: Stepped blocks, transmission towers, fiber arcs */}
            <path
              d="
                M0 120 L0 105
                L80 105 L80 92 L120 92 L120 100
                L180 100 L200 70 L220 100 L260 100
                L290 85 L320 85 L320 65 L330 65 L330 50 L335 40 L340 50 L340 65 L350 65 L350 100
                L420 100 L440 80 L480 80 L500 95
                L540 95 L550 55 L560 55 L565 30 L570 55 L580 55 L590 95
                L650 95 L680 75 L720 75 L740 98
                L800 98 L810 60 L830 60 L840 98
                L910 98 L940 88 L1000 88 L1000 120 Z
              "
              fill="url(#silhouetteGrad)"
            />

            {/* Subtle fiber optic connectivity arcs */}
            <path
              d="M180 100 Q 260 40 335 40"
              stroke="#0284c7"
              strokeWidth="0.8"
              strokeDasharray="4 4"
              opacity="0.35"
            />
            <path
              d="M340 40 Q 450 20 565 30"
              stroke="#0284c7"
              strokeWidth="0.8"
              strokeDasharray="4 4"
              opacity="0.35"
            />
            <path
              d="M570 30 Q 700 35 820 60"
              stroke="#0284c7"
              strokeWidth="0.8"
              strokeDasharray="4 4"
              opacity="0.35"
            />

            {/* Pulse dots on network nodes */}
            <circle cx="335" cy="40" r="2" fill="#0284c7" opacity="0.6" />
            <circle cx="565" cy="30" r="2.5" fill="#059669" opacity="0.6" />
            <circle cx="820" cy="60" r="2" fill="#ea580c" opacity="0.6" />
          </svg>
        </div>

        {/* Bottom Status Message */}
        <div
          className={`flex items-center gap-2 mb-3 transition-all duration-700 ease-out ${
            phase >= 8 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
          }`}
        >
          <span className="text-[12px] font-medium tracking-wide text-slate-500 font-sans">
            India Focused.
          </span>
          <span className="text-slate-300">•</span>
          <span className="text-[12px] font-semibold tracking-wide text-slate-700 font-sans">
            Safety First.
          </span>
        </div>

        {/* Action CTAs when on Landing Page */}
        {isLanding && (
          <div
            className={`flex items-center justify-center gap-3 mb-3.5 transition-all duration-700 z-20 ${
              phase >= 8 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
            }`}
          >
            <Link
              to={isAuthenticated ? '/dashboard' : '/login'}
              className="px-5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-mono font-bold tracking-wider shadow-lg shadow-slate-950/20 transition active:scale-95 flex items-center gap-2 border border-slate-800"
            >
              <span>{isAuthenticated ? 'Enter Console' : 'Launch Console'}</span>
              <ArrowRight size={13} />
            </Link>
            {!isAuthenticated && (
              <Link
                to="/signup"
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-mono font-bold tracking-wider shadow-lg shadow-emerald-950/20 transition active:scale-95"
              >
                Create Account
              </Link>
            )}
          </div>
        )}

        {/* Thin Elegant Progress Indicator */}
        <div
          className={`w-64 md:w-80 h-[2.5px] rounded-full bg-slate-200/80 overflow-hidden transition-all duration-700 ${
            phase >= 8 ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <div
            className="h-full rounded-full transition-all duration-75 ease-linear"
            style={{
              width: `${progress}%`,
              backgroundImage: 'linear-gradient(90deg, #0284c7 0%, #38bdf8 70%, #10b981 100%)',
              boxShadow: '0 0 8px rgba(56, 189, 248, 0.6)'
            }}
          />
        </div>

        {/* System Initializing Status Subtitle */}
        <div
          className={`mt-2 text-[10px] font-mono text-slate-400 tracking-wider transition-opacity duration-500 ${
            phase >= 8 ? 'opacity-80' : 'opacity-0'
          }`}
        >
          {progress >= 100
            ? 'SYSTEM ACTIVE • NATIONAL DEFENSE ONLINE (100%)'
            : `SYSTEM INITIALIZING • SECURE PROTOCOLS ACTIVE (${progress}%)`}
        </div>
      </footer>

      {/* Global CSS for Keyframe Animations */}
      <style>{`
        @keyframes scanMove {
          0% {
            transform: translateY(10px);
            opacity: 0.1;
          }
          35% {
            opacity: 0.9;
          }
          65% {
            opacity: 0.9;
          }
          100% {
            transform: translateY(210px);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
};

export default CinematicSplash;
