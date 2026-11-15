import React from 'react';
import { UserProfile } from '../api';
import {
  Plus,
  MessageSquare,
  Trash2,
  BarChart3,
  LogOut,
  LogIn,
  X,
  BookOpen,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  sessions: any[];
  activeSessionId?: string;
  user: UserProfile | null;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession?: (id: string) => void;
  onOpenCatalogue?: () => void;
  onOpenAdmin?: () => void;
  onOpenLogin: () => void;
  onLogout: () => void;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  sessions,
  activeSessionId,
  user,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  onOpenCatalogue,
  onOpenAdmin,
  onOpenLogin,
  onLogout,
  onCloseMobile,
}) => {
  if (!isOpen) return null;

  const formatSessionDate = (dateStr?: string) => {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - d.getTime();
      const diffHours = diffMs / (1000 * 60 * 60);

      if (diffHours < 24 && d.getDate() === now.getDate()) {
        return 'Hari ini';
      }
      if (diffHours < 48) {
        return 'Kemarin';
      }
      return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
    } catch {
      return '';
    }
  };

  const sidebarContent = (
    <div className="flex flex-col h-full w-full bg-[#141417] border-r border-zinc-800 select-none">
      {/* Top: New Chat & Action Buttons */}
      <div className="p-3 border-b border-zinc-800/80 flex flex-col gap-2 shrink-0">
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              onNewChat();
              if (window.innerWidth < 640 && onCloseMobile) onCloseMobile();
            }}
            className="flex-1 flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold text-white bg-zinc-800 hover:bg-zinc-700 border border-zinc-700/60 shadow-sm transition cursor-pointer active:scale-[0.98]"
          >
            <div className="flex items-center gap-2">
              <Plus className="w-4 h-4 text-white" />
              <span>Percakapan baru</span>
            </div>
            <span className="text-[10px] text-zinc-400 font-mono bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-700/50">
              ⌘K
            </span>
          </button>

          {/* Close button for mobile */}
          {onCloseMobile && (
            <button
              onClick={onCloseMobile}
              className="sm:hidden p-2 text-zinc-400 hover:text-white rounded-xl hover:bg-zinc-800 transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Official Knowledge Vault Catalogue Button */}
        {onOpenCatalogue && (
          <button
            onClick={() => {
              onOpenCatalogue();
              if (window.innerWidth < 640 && onCloseMobile) onCloseMobile();
            }}
            className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium text-zinc-300 hover:text-white bg-zinc-900/60 hover:bg-zinc-800 border border-zinc-800 transition cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <BookOpen className="w-3.5 h-3.5 text-sky-400" />
              <span>Katalog Dokumen Resmi</span>
            </div>
            <span className="text-[10px] text-zinc-400 font-mono bg-zinc-800 px-1.5 py-0.5 rounded">
              62 Dok
            </span>
          </button>
        )}
      </div>

      {/* Middle: Chat History List */}
      <div className="flex-1 overflow-y-auto px-2.5 py-3 flex flex-col gap-1 scrollbar-thin">
        <div className="px-2 pt-1 pb-1 text-[11px] font-bold text-zinc-500 uppercase tracking-wider flex items-center justify-between">
          <span>Riwayat Percakapan</span>
          {sessions.length > 0 && (
            <span className="text-[10px] font-mono font-normal text-zinc-600">
              {sessions.length}
            </span>
          )}
        </div>

        {sessions.length === 0 ? (
          <div className="px-3 py-10 text-center text-xs text-zinc-500 flex flex-col items-center gap-2.5">
            <MessageSquare className="w-6 h-6 text-zinc-700 opacity-60" />
            <p>Belum ada riwayat percakapan. Mulai obrolan baru bersama Luco.</p>
          </div>
        ) : (
          sessions.map((sess) => {
            const isSelected = sess.id === activeSessionId;
            const dateLabel = formatSessionDate(sess.updated_at || sess.created_at);
            return (
              <div
                key={sess.id}
                onClick={() => {
                  onSelectSession(sess.id);
                  if (window.innerWidth < 640 && onCloseMobile) onCloseMobile();
                }}
                className={`w-full text-left px-3 py-2.5 rounded-xl text-xs transition flex items-center justify-between group cursor-pointer ${
                  isSelected
                    ? 'bg-zinc-800 text-white font-medium border border-zinc-700/80 shadow-sm'
                    : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0 pr-1 flex-1">
                  <div className="relative shrink-0">
                    <MessageSquare
                      className={`w-4 h-4 ${
                        isSelected ? 'text-blue-400' : 'text-zinc-500'
                      }`}
                    />
                    {sess.is_active && (
                      <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-emerald-500 ring-2 ring-[#141417]" />
                    )}
                  </div>
                  <div className="flex flex-col min-w-0 flex-1">
                    <span className="truncate text-xs">
                      {sess.title || 'Percakapan Baru'}
                    </span>
                    {dateLabel && (
                      <span className="text-[10px] text-zinc-500 font-mono">
                        {dateLabel}
                      </span>
                    )}
                  </div>
                </div>

                {onDeleteSession && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm('Hapus percakapan ini?')) {
                        onDeleteSession(sess.id);
                      }
                    }}
                    title="Hapus percakapan"
                    className="opacity-0 group-hover:opacity-100 p-1.5 text-zinc-500 hover:text-red-400 hover:bg-zinc-700/50 rounded-lg transition-opacity cursor-pointer shrink-0 ml-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Bottom: User Card & Admin Link */}
      <div className="p-3 border-t border-zinc-800 bg-[#101013] flex flex-col gap-2 shrink-0">
        {user ? (
          <div className="flex flex-col gap-2">
            {/* Admin Button (Strictly for the 3 developer NIMs) */}
            {user.is_admin && onOpenAdmin && (
              <button
                onClick={() => {
                  onOpenAdmin();
                  if (onCloseMobile) onCloseMobile();
                }}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-amber-300 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 transition text-left cursor-pointer"
              >
                <BarChart3 className="w-4 h-4 text-amber-400 shrink-0" />
                <span className="truncate">Monitoring & Audit (Admin)</span>
              </button>
            )}

            {/* User Info Capsule */}
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs">
              <div className="flex items-center gap-2.5 min-w-0">
                {user.picture ? (
                  <img
                    src={user.picture}
                    alt={user.full_name}
                    className="w-7 h-7 rounded-full object-cover shrink-0 ring-1 ring-white/10"
                  />
                ) : (
                  <div className="w-7 h-7 rounded-full bg-zinc-800 text-zinc-200 border border-zinc-700 flex items-center justify-center text-xs font-bold shrink-0">
                    {user.full_name.charAt(0).toUpperCase()}
                  </div>
                )}
                <div className="min-w-0">
                  <div className="font-semibold text-white truncate text-xs">
                    {user.full_name}
                  </div>
                  <div className="text-[10px] text-zinc-400 truncate">
                    {user.email}
                  </div>
                </div>
              </div>

              <button
                onClick={onLogout}
                title="Keluar / Logout"
                className="p-1.5 text-zinc-400 hover:text-red-400 hover:bg-zinc-800 rounded-lg transition ml-1 cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => {
              onOpenLogin();
              if (onCloseMobile) onCloseMobile();
            }}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-white hover:bg-zinc-200 text-xs font-bold text-zinc-950 transition shadow-sm cursor-pointer"
          >
            <LogIn className="w-4 h-4" />
            <span>Masuk Akun Untan</span>
          </button>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile Backdrop & Drawer (< 640px) */}
      <div className="sm:hidden">
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 transition-opacity"
        />
        <aside className="fixed inset-y-0 left-0 z-50 w-72 h-full shadow-2xl">
          {sidebarContent}
        </aside>
      </div>

      {/* Desktop & Tablet Inline Sidebar (>= 640px) */}
      <aside className="hidden sm:flex w-60 lg:w-64 shrink-0 h-full">
        {sidebarContent}
      </aside>
    </>
  );
};
