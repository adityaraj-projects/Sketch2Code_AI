import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutGrid,
  FolderClock,
  LayoutTemplate,
  Settings,
  PenLine,
  LogOut,
  ShieldAlert,
} from "lucide-react";
import clsx from "clsx";
import { useAuthStore } from "@/store/useAuthStore";

const NAV_ITEMS = [
  { to: "/dashboard", icon: LayoutGrid, label: "Home", end: true },
  { to: "/dashboard/recent", icon: FolderClock, label: "Recent Projects" },
  { to: "/dashboard/templates", icon: LayoutTemplate, label: "Templates" },
  { to: "/dashboard/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-white/[0.06] bg-ink-900/60 p-4">
      <div className="mb-8 flex items-center gap-2 px-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500">
          <PenLine size={16} className="text-white" />
        </div>
        <span className="font-display text-base font-semibold text-paper-100">Sketch2Code</span>
      </div>

      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors",
                isActive
                  ? "bg-violet-500/15 text-violet-300"
                  : "text-paper-300 hover:bg-white/[0.05] hover:text-paper-100"
              )
            }
          >
            <Icon size={17} strokeWidth={1.75} />
            {label}
          </NavLink>
        ))}
        {user?.is_admin && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors",
                isActive
                  ? "bg-violet-500/15 text-violet-300"
                  : "text-paper-300 hover:bg-white/[0.05] hover:text-paper-100"
              )
            }
          >
            <ShieldAlert size={17} strokeWidth={1.75} />
            Admin Panel
          </NavLink>
        )}
      </nav>

      <div className="mt-auto border-t border-white/[0.06] pt-4">
        <div className="flex items-center gap-3 px-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-violet-500/20 font-display text-sm font-medium text-violet-300">
            {user?.full_name?.charAt(0)?.toUpperCase() ?? "?"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm text-paper-100">{user?.full_name}</p>
            <p className="truncate text-xs text-paper-500">{user?.email}</p>
          </div>
          <button
            title="Log out"
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="rounded-lg p-1.5 text-paper-500 hover:bg-white/[0.06] hover:text-paper-100"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}
