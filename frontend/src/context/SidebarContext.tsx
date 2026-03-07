import { createContext, useContext, useState, type ReactNode } from 'react';

type ViewMode = 'admin' | 'opersac';

interface SidebarContextType {
  activeOption: string;
  setActiveOption: (option: string) => void;
  viewMode: ViewMode;
  toggleViewMode: () => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  mobileOpen: boolean;
  toggleMobile: () => void;
  closeMobile: () => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [activeOption, setActiveOption] = useState('map');
  const [viewMode, setViewMode] = useState<ViewMode>('admin');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const toggleViewMode = () => {
    setViewMode((prev) => (prev === 'admin' ? 'opersac' : 'admin'));
  };

  const toggleMobile = () => setMobileOpen((prev) => !prev);
  const closeMobile = () => setMobileOpen(false);

  return (
    <SidebarContext.Provider
      value={{ activeOption, setActiveOption, viewMode, toggleViewMode, isCollapsed, setIsCollapsed, mobileOpen, toggleMobile, closeMobile }}
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
