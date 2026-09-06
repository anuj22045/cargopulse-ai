import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  BarChart2,
  Bell,
  User,
  Zap,
} from "lucide-react";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/shipments", label: "Shipments", icon: Package, end: false },
  { to: "/analytics", label: "Analytics", icon: BarChart2, end: false },
];

function MainLayout() {
  const location = useLocation();

  function getPageTitle() {
    if (location.pathname === "/") return "Dashboard";
    if (location.pathname.startsWith("/shipments/")) return "Shipment Details";
    if (location.pathname === "/shipments") return "Shipments";
    if (location.pathname === "/analytics") return "Analytics";
    return "CargoPulse AI";
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <aside className="flex w-64 flex-shrink-0 flex-col bg-slate-800">
        {/* Logo */}
        <div className="flex items-center gap-3 border-b border-slate-700 px-6 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold leading-tight text-white">
              CargoPulse
            </p>
            <p className="text-xs text-slate-400">AI Platform</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
            Main Menu
          </p>
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-150 ${
                  isActive
                    ? "bg-amber-500 text-white"
                    : "text-slate-400 hover:bg-slate-700 hover:text-white"
                }`
              }
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Sidebar footer */}
        <div className="border-t border-slate-700 px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-600 text-xs font-semibold text-slate-200">
              CP
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-medium text-slate-200">
                Operations
              </p>
              <p className="truncate text-xs text-slate-500">Manager</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Topbar */}
        <header className="flex h-16 flex-shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6">
          <h1 className="text-lg font-semibold text-slate-800">
            {getPageTitle()}
          </h1>
          <div className="flex items-center gap-3">
            <button
              id="topbar-notifications"
              className="relative flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
            >
              <Bell className="h-5 w-5" />
              <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-amber-500" />
            </button>
            <button
              id="topbar-profile"
              className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
            >
              <User className="h-5 w-5" />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default MainLayout;
