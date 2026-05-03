import React, { useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Sidebar } from './components/layout/Sidebar';
import { TabBar } from './components/layout/TabBar';
import { StatusBar } from './components/layout/StatusBar';
import { LogTerminal } from './components/shared/LogTerminal';
import { ProjectTab } from './components/tabs/ProjectTab';
import { FramesTab } from './components/tabs/FramesTab';
import { ScriptTab } from './components/tabs/ScriptTab';
import { ReferenceTab } from './components/tabs/ReferenceTab';
import { ApiTab } from './components/tabs/ApiTab';
import { useAppStore } from './store/useAppStore';

const TABS = {
  project:   ProjectTab,
  frames:    FramesTab,
  script:    ScriptTab,
  reference: ReferenceTab,
  api:       ApiTab,
};

export default function App() {
  const { activeTab, loadFromConfig, toConfig, handleAgentMessage, updateApi } = useAppStore();
  const TabComponent = TABS[activeTab] || ProjectTab;

  // Load persisted config on startup
  useEffect(() => {
    const api = window.electronAPI;
    if (!api) return;

    api.loadConfig().then((config) => {
      if (config) loadFromConfig(config);
    });

    // Listen for agent messages
    const unsub = api.onAgentMessage((msg) => {
      handleAgentMessage(msg);
    });

    return () => unsub?.();
  }, []);

  // Auto-save config on changes
  useEffect(() => {
    const timer = setTimeout(() => {
      window.electronAPI?.saveConfig(toConfig());
    }, 1500);
    return () => clearTimeout(timer);
  });

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      overflow: 'hidden',
      background: '#0d0d0f',
    }}>
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <TabBar />
          <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.15, ease: 'easeOut' }}
                style={{ height: '100%', overflow: 'hidden' }}
              >
                <TabComponent />
              </motion.div>
            </AnimatePresence>
          </div>
          <LogTerminal />
        </div>
      </div>
      <StatusBar />
    </div>
  );
}
