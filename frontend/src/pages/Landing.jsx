import React from 'react';
import CinematicSplash from '../components/CinematicSplash';

/**
 * Public Landing Page for BharatSHIELD
 * Serves at root path '/' for all visitors (unauthenticated & authenticated).
 * Showcases national cybersecurity defense, real-time threat intelligence posture,
 * and direct CTAs to 'Launch Console' or 'Create Account'.
 */
const Landing = () => {
  return <CinematicSplash isLanding={true} />;
};

export default Landing;
