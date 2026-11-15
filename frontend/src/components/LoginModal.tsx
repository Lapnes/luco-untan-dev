import React, { useState } from 'react';
import { getGoogleLoginUrl, guestLogin, UserProfile } from '../api';
import { X, ShieldCheck, UserCheck } from 'lucide-react';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: UserProfile) => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [guestName, setGuestName] = useState('');
  const [loadingGuest, setLoadingGuest] = useState(false);

  if (!isOpen) return null;

  const handleGoogleLogin = () => {
    window.location.href = getGoogleLoginUrl();
  };

  const handleGuestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingGuest(true);
    try {
      const name = guestName.trim() || 'Mahasiswa Penguji';
      const profile = await guestLogin(name);
      onSuccess(profile);
      onClose();
    } catch {
      alert('Gagal inisiasi sesi tamu. Silakan coba lagi.');
    } finally {
      setLoadingGuest(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      {/* Modal Container Card (Exact Match to User Reference Image) */}
      <div className="bg-[#141417] border border-zinc-800 rounded-3xl p-6 sm:p-8 w-full max-w-[420px] shadow-2xl relative text-center flex flex-col items-center gap-5 z-50">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer"
          title="Tutup"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Mascot App Icon with Glow */}
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-600/20 to-indigo-700/20 border border-blue-500/30 flex items-center justify-center shadow-lg shadow-blue-500/20 p-2.5">
          <img
            src="/luco-logo.png"
            alt="Luco Mascot"
            className="w-full h-full object-contain drop-shadow"
          />
        </div>

        {/* Header Text */}
        <div className="flex flex-col gap-1.5">
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Masuk ke Luco
          </h2>
          <p className="text-xs text-zinc-400 max-w-xs leading-relaxed">
            Asisten Informasi Akademik & Regulasi Program Studi Informatika UNTAN
          </p>
        </div>

        {/* Main Action: Google SSO Button */}
        <button
          onClick={handleGoogleLogin}
          className="w-full py-3 px-4 bg-white hover:bg-zinc-100 text-zinc-950 font-bold text-sm rounded-xl shadow-md transition active:scale-[0.99] flex items-center justify-center gap-3 cursor-pointer"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" className="shrink-0">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          <span>Lanjutkan dengan Google SSO</span>
        </button>

        {/* Info Banner */}
        <div className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-blue-950/40 border border-blue-800/40 text-blue-300 text-[11px] font-medium">
          <ShieldCheck className="w-4 h-4 text-blue-400 shrink-0" />
          <span>Gunakan akun <strong>@student.untan.ac.id</strong> untuk akses penuh</span>
        </div>

        {/* Divider */}
        <div className="w-full relative flex items-center justify-center my-1">
          <div className="border-t border-zinc-800 w-full" />
          <span className="bg-[#141417] px-3 text-[10px] text-zinc-500 uppercase tracking-wider font-semibold absolute">
            Atau coba tanpa login
          </span>
        </div>

        {/* Guest Access Form */}
        <form onSubmit={handleGuestSubmit} className="w-full flex flex-col gap-3">
          <input
            type="text"
            value={guestName}
            onChange={(e) => setGuestName(e.target.value)}
            placeholder="Nama Anda (misal: Budi - Penguji)..."
            className="w-full bg-zinc-900 border border-zinc-800 focus:border-zinc-600 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-500 outline-none transition text-left"
          />

          <button
            type="submit"
            disabled={loadingGuest}
            className="w-full py-2.5 px-4 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700/60 text-white rounded-xl text-xs font-semibold shadow-sm transition active:scale-[0.99] flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <UserCheck className="w-4 h-4 text-zinc-400" />
            <span>{loadingGuest ? 'Membuat sesi tamu...' : 'Mulai Coba Sebagai Tamu'}</span>
          </button>
        </form>
      </div>
    </div>
  );
};
