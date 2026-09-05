import React from 'react';

/**
 * EmblemLogo — CIVIX institutional identity mark.
 *
 * NOTE: This is a PLACEHOLDER representing the Ashoka Lions (Government of India emblem).
 * The OFFICIAL Delhi Police emblem asset must be supplied as an approved image file.
 * When available, replace this SVG with <img src="/delhi-police-emblem.png" /> 
 * at the appropriate call sites.
 *
 * This SVG is styled for dark backgrounds (civix-surface-*).
 */
export const EmblemLogo: React.FC<{ className?: string }> = ({ className = 'w-8 h-8' }) => {
  return (
    <svg
      className={className}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Government of India Emblem"
    >
      {/* Outer Circle — white/near-white for visibility on dark */}
      <circle cx="50" cy="50" r="46" stroke="#e8edf5" strokeWidth="2.5" fill="none" />
      {/* Gold institutional ring */}
      <circle cx="50" cy="50" r="41" stroke="#c8a84b" strokeWidth="1.5" strokeDasharray="5 3" />
      
      {/* Stylized Ashoka Lions silhouette */}
      <path
        d="M50 16 L54.5 27 L65 27 L57 33.5 L60 44 L50 37.5 L40 44 L43 33.5 L35 27 L45.5 27 Z"
        fill="#e8edf5"
      />
      {/* Base pedestal */}
      <rect x="34" y="48" width="32" height="5" rx="1" fill="#e8edf5" />
      
      {/* Ashoka Chakra — gold accent */}
      <circle cx="50" cy="67" r="11" stroke="#c8a84b" strokeWidth="1.5" fill="none" />
      <circle cx="50" cy="67" r="2.5" fill="#c8a84b" />
      {/* Chakra spokes — 8 */}
      <path 
        d="M50 56 L50 78 M39 67 L61 67 M42.2 59.2 L57.8 74.8 M42.2 74.8 L57.8 59.2" 
        stroke="#c8a84b" strokeWidth="1" opacity="0.7"
      />
      
      {/* Base gold line — institutional identity accent */}
      <rect x="28" y="81" width="44" height="3" rx="1" fill="#c8a84b" />
    </svg>
  );
};
