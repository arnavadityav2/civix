import React from 'react';
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

export const AppRouter: React.FC = () => {
  return (
    <CaseSelectionProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<CommandCenterPage />} />
            <Route path="/cases" element={<CasesPage />} />
            <Route path="/cases/:caseId" element={<CaseWorkspacePage />} />
            <Route path="/cases/:caseId/graph" element={<InvestigativeGraphPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/cctv" element={<CCTVCommandCenterPage />} />
            <Route path="/entities/:entityId" element={<EntityDossierPage />} />
            <Route path="*" element={<CommandCenterPage />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </CaseSelectionProvider>
  );
};

