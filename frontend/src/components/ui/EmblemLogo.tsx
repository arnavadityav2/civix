import React from 'react';

export const EmblemLogo: React.FC<{ className?: string }> = ({ className = 'w-8 h-8' }) => {
  return (
    <svg
      className={className}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Outer Circle */}
      <circle cx="50" cy="50" r="46" stroke="#0f172a" strokeWidth="4" fill="#ffffff" />
      {/* Saffron Accent Ring */}
      <circle cx="50" cy="50" r="41" stroke="#d97706" strokeWidth="2" strokeDasharray="6 3" />
      
      {/* Stylized Ashoka Lions / Emblem Representation */}
      <path
        d="M50 18 L54 28 L64 28 L56 34 L59 44 L50 38 L41 44 L44 34 L36 28 L46 28 Z"
        fill="#0f172a"
      />
      {/* Base Pedestal */}
      <rect x="35" y="48" width="30" height="6" rx="1" fill="#0f172a" />
      {/* Ashoka Chakra Center */}
      <circle cx="50" cy="66" r="10" stroke="#1d4ed8" strokeWidth="2" fill="none" />
      <circle cx="50" cy="66" r="2" fill="#1d4ed8" />
      <path d="M50 56 L50 76 M40 66 L60 66 M43 59 L57 73 M43 73 L57 59" stroke="#1d4ed8" strokeWidth="1" />
      {/* Base Line */}
      <rect x="30" y="80" width="40" height="4" rx="1" fill="#d97706" />
    </svg>
  );
};
