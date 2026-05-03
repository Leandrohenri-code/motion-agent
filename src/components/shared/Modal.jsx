import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

export function Modal({ open, onClose, title, children, width = 480 }) {
  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          style={{
            position: 'fixed', inset: 0,
            background: '#00000080',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 8 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 8 }}
            transition={{ duration: 0.15 }}
            style={{
              width, maxWidth: '90vw',
              background: '#141416',
              border: '1px solid #22222c',
              borderRadius: 16,
              boxShadow: '0 24px 64px #00000080',
              display: 'flex', flexDirection: 'column',
            }}
          >
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '16px 20px',
              borderBottom: '1px solid #22222c',
            }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: '#f0f0f2' }}>{title}</span>
              <button
                onClick={onClose}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: '#8a8a9a', display: 'flex', padding: 4,
                  borderRadius: 6, transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = '#f0f0f2'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#8a8a9a'}
              >
                <X size={16} />
              </button>
            </div>
            <div style={{ padding: 20 }}>
              {children}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
