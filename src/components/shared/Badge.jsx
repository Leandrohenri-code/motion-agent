import React from 'react';

const variantStyles = {
  success: { background: '#00d4aa20', color: '#00d4aa', border: '1px solid #00d4aa30' },
  error:   { background: '#ff4d6d20', color: '#ff4d6d', border: '1px solid #ff4d6d30' },
  warning: { background: '#ffb34020', color: '#ffb340', border: '1px solid #ffb34030' },
  info:    { background: '#4d9fff20', color: '#4d9fff', border: '1px solid #4d9fff30' },
  neutral: { background: '#1f1f26',   color: '#8a8a9a', border: '1px solid #22222c'   },
  accent:  { background: '#6c63ff20', color: '#6c63ff', border: '1px solid #6c63ff30' },
};

export function Badge({ variant = 'neutral', dot = false, pulse = false, children, style }) {
  const vs = variantStyles[variant] || variantStyles.neutral;
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5,
      padding: '2px 8px',
      borderRadius: 999,
      fontSize: 11,
      fontWeight: 500,
      ...vs,
      ...style,
    }}>
      {dot && (
        <span style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: vs.color,
          flexShrink: 0,
          animation: pulse ? 'dotPulse 1.5s ease infinite' : undefined,
        }} />
      )}
      {children}
    </span>
  );
}
