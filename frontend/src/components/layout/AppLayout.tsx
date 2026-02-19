import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import { SidebarProvider } from '../../context/SidebarContext';

export default function AppLayout() {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 p-6 overflow-auto bg-[var(--bg-secondary)]">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
