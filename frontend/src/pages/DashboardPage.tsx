import { useCallback } from 'react';
import { useSidebar } from '../context/SidebarContext';
import { useAuth } from '../context/AuthContext';
import { useLoginNotifications } from '../hooks/useLoginNotifications';
import StationMap from '../components/station-map/StationMap';
import NotificationList from '../components/notifications/NotificationList';
import RequestTable from '../components/requests/RequestTable';
import ReportsView from '../components/reports/ReportsView';
import PermissionsManager from '../components/permissions/PermissionsManager';
import UserTable from '../components/users/UserTable';
import BackupHistory from '../components/backup/BackupHistory';
import AuditTable from '../components/audit/AuditTable';
import GuideView from '../components/guide/GuideView';
import LoginToast, { type ToastItem } from '../components/ui/LoginToast';

export default function DashboardPage() {
  const { activeOption, setActiveOption } = useSidebar();
  const { user } = useAuth();
  const { toasts, dismiss } = useLoginNotifications(user?.role as 'admin' | 'opersac' | undefined, user?.id);

  const handleToastClick = useCallback((toast: ToastItem) => {
    setActiveOption(toast.navigateTo);
  }, [setActiveOption]);

  const renderContent = () => {
    switch (activeOption) {
      case 'map':
        return <StationMap />;
      case 'notifications':
        return <NotificationList />;
      case 'requests':
        return <RequestTable />;
      case 'reports':
        return <ReportsView />;
      case 'permissions':
        return <PermissionsManager />;
      case 'users':
        return <UserTable />;
      case 'backup':
        return <BackupHistory />;
      case 'audit':
        return <AuditTable />;
      case 'guide':
        return <GuideView />;
      default:
        return <StationMap />;
    }
  };

  return (
    <>
      {renderContent()}
      <LoginToast toasts={toasts} onClose={dismiss} onClickToast={handleToastClick} />
    </>
  );
}
