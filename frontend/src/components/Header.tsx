import React from 'react';
import { UserProfile } from '../api';
import { PanelLeft, Plus, LogOut, BarChart3, MessageSquare, LogIn } from 'lucide-react';

interface HeaderProps {
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  onNewChat: () => void;
  user: UserProfile | null;
  isAdminViewOpen?: boolean;
  onToggleAdminView?: (open: boolean) => void;
  onLogout: () => void;
  onOpenLogin: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isSidebarOpen,
  onToggleSidebar,
  onNewChat,
  user,
  isAdminViewOpen = false,
  onToggleAdminView,
  onLogout,
  onOpenLogin,
}) => {
  return (
    <header className="min-h-14 pt-[env(safe-area-inset-top,0px)] pb-1 border-b border-zinc-800 bg-[#141417] px-3 sm:px-4 flex items-center justify-between sticky top-0 z-30 select-none shrink-0">
      {/* Left: Sidebar Toggle & App Brand */}
      <div className="flex items-center gap-2 sm:gap-3">
        <button
          onClick={onToggleSidebar}
          title={isSidebarOpen ? 'Tutup sidebar' : 'Buka sidebar'}
          className="p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer"
        >
          <PanelLeft className="w-5 h-5" />
        </button>

        <button
          onClick={onNewChat}
          title="Percakapan Baru"
          className="sm:hidden p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer"
        >
          <Plus className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5 pl-1">
          <img
            src="/luco-logo.png"
            alt="Luco Logo"
            className="w-7 h-7 object-contain drop-shadow select-none"
          />
          <div className="flex items-center gap-2">
            <span className="font-bold text-base text-white tracking-tight">Luco</span>
            <span className="text-xs text-zinc-400 font-normal hidden md:inline">
              • Informatika UNTAN
            </span>
          </div>
        </div>
      </div>

      {/* Center: Admin Mode Switcher Pill (Strictly for the 3 developer NIMs) */}
      {user?.is_admin && onToggleAdminView && (
        <div className="flex items-center p-1 rounded-xl bg-zinc-900 border border-zinc-800 shadow-inner">
          <button
            onClick={() => onToggleAdminView(false)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition cursor-pointer ${
              !isAdminViewOpen
                ? 'bg-zinc-800 text-white shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Obrolan</span>
          </button>
          <button
            onClick={() => onToggleAdminView(true)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition cursor-pointer ${
              isAdminViewOpen
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 shadow-sm'
                : 'text-zinc-400 hover:text-amber-300'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5 text-amber-400" />
            <span className="hidden sm:inline">Monitor & Audit</span>
            <span className="sm:hidden">Audit</span>
          </button>
        </div>
      )}

      {/* Right: User Profile / Sign In */}
      <div className="flex items-center gap-2 sm:gap-3">
        {user ? (
          <div className="flex items-center gap-2">
            {/* User Profile Pill */}
            <div className="flex items-center gap-2 py-1 px-2.5 rounded-xl bg-zinc-800/80 border border-zinc-700/60">
              {user.picture ? (
                <img
                  src={user.picture}
                  alt={user.full_name}
                  className="w-5 h-5 rounded-full object-cover"
                />
              ) : (
                <div className="w-5 h-5 rounded-full bg-zinc-700 text-zinc-200 flex items-center justify-center text-[10px] font-bold">
                  {user.full_name.charAt(0).toUpperCase()}
                </div>
              )}
              <span className="text-xs font-medium text-zinc-200 max-w-[120px] truncate hidden sm:block">
                {user.full_name}
              </span>
            </div>

            <button
              onClick={onLogout}
              title="Keluar / Logout"
              className="p-2 text-zinc-400 hover:text-red-400 hover:bg-zinc-800 rounded-xl transition cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenLogin}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white hover:bg-zinc-200 text-zinc-950 text-xs font-bold shadow-sm transition active:scale-95 cursor-pointer"
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Masuk</span>
          </button>
        )}
      </div>
    </header>
  );
};
