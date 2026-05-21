import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

export default function Layout() {
  return (
    <div className="dash-app-shell">
      <Sidebar />
      <div className="dash-app-main">
        <Header />
        <main className="dash-app-content p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
