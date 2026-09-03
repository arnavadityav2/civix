import React, { createContext, useContext, useState } from 'react';

interface CaseSelectionContextType {
  selectedCaseId: string | null;
  setSelectedCaseId: (caseId: string | null) => void;
}

const CaseSelectionContext = createContext<CaseSelectionContextType>({
  selectedCaseId: null,
  setSelectedCaseId: () => {},
});

export const CaseSelectionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);

  return (
    <CaseSelectionContext.Provider value={{ selectedCaseId, setSelectedCaseId }}>
      {children}
    </CaseSelectionContext.Provider>
  );
};

export const useCaseSelection = () => useContext(CaseSelectionContext);
