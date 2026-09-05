import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from '../components/layouts/AppShell';
import { CaseSelectionProvider } from '../context/CaseSelectionContext';
import { CommandCenterPage } from '../pages/CommandCenterPage';
import { CasesPage } from '../pages/CasesPage';
import { CaseWorkspacePage } from '../pages/CaseWorkspacePage';
import { SearchPage } from '../pages/SearchPage';
import { EntityDossierPage } from '../pages/EntityDossierPage';
import { InvestigativeGraphPage } from '../pages/InvestigativeGraphPage';
import { CCTVCommandCenterPage } from '../pages/CCTVCommandCenterPage';
import { VisualAnalysisPage } from '../pages/VisualAnalysisPage';
import { SpatialIntelligencePage } from '../pages/SpatialIntelligencePage';
import { EvidencePage } from '../pages/EvidencePage';
import { TelecomIntelligencePage } from '../pages/TelecomIntelligencePage';
import { CivixSplashScreen } from '../components/splash/CivixSplashScreen';

export const AppRouter: React.FC = () => {
  const [showSplash, setShowSplash] = useState<boolean>(() => {
    // Check URL param ?splash=true or default to showing splash on initial load
    const params = new URLSearchParams(window.location.search);
    if (params.get('splash') === 'true') return true;
    return true; // Show splash by default on fresh session
  });

  useEffect(() => {
    const handleReplay = () => setShowSplash(true);
    window.addEventListener('civix:replay_splash', handleReplay);
    return () => window.removeEventListener('civix:replay_splash', handleReplay);
  }, []);

  return (
    <CaseSelectionProvider>
      <BrowserRouter>
        {showSplash && (
          <CivixSplashScreen onComplete={() => setShowSplash(false)} />
        )}
        <AppShell>
          <Routes>
            <Route path="/" element={<CommandCenterPage />} />
            <Route path="/cases" element={<CasesPage />} />
            <Route path="/cases/:caseId" element={<CaseWorkspacePage />} />
            <Route path="/cases/:caseId/graph" element={<InvestigativeGraphPage />} />
            <Route path="/cases/:caseId/telecom" element={<TelecomIntelligencePage />} />
            <Route path="/telecom" element={<TelecomIntelligencePage />} />
            <Route path="/evidence" element={<EvidencePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/spatial" element={<SpatialIntelligencePage />} />
            <Route path="/cctv" element={<CCTVCommandCenterPage />} />
            <Route path="/cctv/analysis/:cameraId" element={<VisualAnalysisPage />} />
            <Route path="/cctv/analysis" element={<VisualAnalysisPage />} />
            <Route path="/entities/:entityId" element={<EntityDossierPage />} />
            <Route path="*" element={<CommandCenterPage />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </CaseSelectionProvider>
  );
};


