import { useSidebar } from '../context/SidebarContext';
import StationMap from '../components/station-map/StationMap';
import NotificationList from '../components/notifications/NotificationList';
import RequestTable from '../components/requests/RequestTable';
import ReportsView from '../components/reports/ReportsView';
import PermissionsManager from '../components/permissions/PermissionsManager';
import UserTable from '../components/users/UserTable';
import BackupHistory from '../components/backup/BackupHistory';
import AuditTable from '../components/audit/AuditTable';

export default function DashboardPage() {
  const { activeOption } = useSidebar();

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
      default:
        return <StationMap />;
    }
  };

  return <>{renderContent()}</>;
}
