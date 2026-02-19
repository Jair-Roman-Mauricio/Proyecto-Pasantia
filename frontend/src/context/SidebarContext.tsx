import { createContext, useContext, useState, type ReactNode } from 'react';

type ViewMode = 'admin' | 'opersac';

interface SidebarContextType {
  activeOption: string;
  setActiveOption: (option: string) => void;
  viewMode: ViewMode;
  toggleViewMode: () => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [activeOption, setActiveOption] = useState('map');
  const [viewMode, setViewMode] = useState<ViewMode>('admin');
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleViewMode = () => {
    setViewMode((prev) => (prev === 'admin' ? 'opersac' : 'admin'));
  };

  return (
    <SidebarContext.Provider
      value={{ activeOption, setActiveOption, viewMode, toggleViewMode, isCollapsed, setIsCollapsed }}
    >
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context) throw new Error('useSidebar must be used within SidebarProvider');
  return context;
}
