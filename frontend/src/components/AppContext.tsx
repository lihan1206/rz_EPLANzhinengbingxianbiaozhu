import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import { getStoredProjectId, setStoredProjectId } from '../utils/storage';

interface AppContextValue {
  selectedProjectId?: number;
  setSelectedProjectId: (projectId?: number) => void;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

export const AppContextProvider = ({ children }: { children: ReactNode }) => {
  const [selectedProjectId, setSelectedProjectIdState] = useState<number | undefined>(getStoredProjectId());

  const setSelectedProjectId = (projectId?: number) => {
    setStoredProjectId(projectId);
    setSelectedProjectIdState(projectId);
  };

  const value = useMemo(
    () => ({
      selectedProjectId,
      setSelectedProjectId,
    }),
    [selectedProjectId],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('应用上下文未初始化');
  }
  return context;
};
