import React, { useState, useEffect, useRef } from 'react';
import {
  UserProfile,
  ChatMessage,
  getToken,
  setTokens,
  getUser,
  setUser,
  clearAuth,
  fetchCurrentUser,
  fetchActiveSession,
  sendChatMessage,
  clearSession,
  listSessions,
  switchSession,
  deleteSession,
  getSharedSession,
} from './api';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatView, QueuedMessageItem } from './components/ChatView';
import { MonitorView } from './components/MonitorView';
import { LoginModal } from './components/LoginModal';
import { DocumentDrawer } from './components/DocumentDrawer';
import { DocumentCatalogModal } from './components/DocumentCatalogModal';

export const App: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isAdminViewOpen, setIsAdminViewOpen] = useState(false);
  const [user, setCurrentUserState] = useState<UserProfile | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isCatalogueOpen, setIsCatalogueOpen] = useState(false);
  const [isSharedView, setIsSharedView] = useState(false);

  // State antrean pesan (Queue) & mutex pengiriman agar tidak bentrok (race condition)
  const [queuedMessages, setQueuedMessages] = useState<QueuedMessageItem[]>([]);
  const queuedMessagesRef = useRef<QueuedMessageItem[]>([]);
  const isSendingRef = useRef<boolean>(false);
  const activeAbortCtrlRef = useRef<AbortController | null>(null);

  // Sinkronkan ref setiap kali antrean berubah untuk akses instan di callback asynchronous
  useEffect(() => {
    queuedMessagesRef.current = queuedMessages;
  }, [queuedMessages]);

  // State untuk Document Drawer (hanya terbuka saat sumber diklik)
  const [selectedDocPath, setSelectedDocPath] = useState<string | null>(null);

  // 1. Tangkap parameter callback OAuth Google saat pertama kali load
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const refreshToken = params.get('refresh_token');
    const email = params.get('email');
    const name = params.get('name');
    const picture = params.get('picture');
    const userId = params.get('user_id');
    const isAdmin = params.get('is_admin') === 'true';

    if (token && email) {
      setTokens(token, refreshToken || undefined);
      const profile: UserProfile = {
        id: userId || 'google-user',
        email,
        full_name: name || email.split('@')[0],
        picture: picture || undefined,
        is_admin: isAdmin,
      };
      setUser(profile);
      setCurrentUserState(profile);

      // Bersihkan query string auth di address bar browser
      window.history.replaceState({}, document.title, window.location.pathname);
    } else {
      const stored = getUser();
      if (stored && getToken()) {
        setCurrentUserState(stored);
      }
    }

    // Dukungan shareable link: jika URL memuat ?session=<id>, buka sesi tersebut
    const sessionParam = params.get('session');
    if (sessionParam) {
      getSharedSession(sessionParam)
        .then((data) => {
          if (data && data.messages) {
            setMessages(data.messages);
            setActiveSessionId(data.session?.id || sessionParam);
            setIsSharedView(true);
          }
        })
        .catch(() => { });
    }

    // Refresh profil dari backend /v1/auth/me untuk sinkronisasi role admin
    if (getToken()) {
      fetchCurrentUser()
        .then((fresh) => {
          if (fresh) setCurrentUserState(fresh);
        })
        .catch(() => { });
    }
  }, []);

  // 2. Ambil sesi aktif & riwayat saat user terotentikasi
  const loadChatData = async () => {
    if (!getToken()) return;
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const isViewingShared = !!urlParams.get('session');

      const [activeData, sessionList] = await Promise.all([
        isViewingShared ? Promise.resolve(null) : fetchActiveSession().catch(() => null),
        listSessions().catch(() => []),
      ]);
      if (activeData && !isViewingShared) {
        setMessages(activeData.messages || []);
        setActiveSessionId(activeData.session?.id);
      }
      setSessions(sessionList);
    } catch {
      // Abaikan jika token kedaluwarsa
    }
  };

  useEffect(() => {
    loadChatData();
  }, [user]);

  // Responsive sidebar: otomatis collapse hanya di ponsel sempit (< 640px)
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 640) {
        setIsSidebarOpen(false);
      } else {
        setIsSidebarOpen(true);
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 3. Eksekusi Pengiriman Pesan (Atomic & Berurutan FIFO dengan AbortController)
  const executeSendMessage = async (text: string, mode?: string) => {
    if (!user) {
      setIsLoginModalOpen(true);
      return;
    }

    // Jika sedang dalam tampilan shared link, keluar dari mode shared ke sesi aktif sendiri
    if (isSharedView) {
      setIsSharedView(false);
      if (window.location.search) {
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }

    // Kunci proses pengiriman agar pesan berikutnya mengantre rapi
    isSendingRef.current = true;
    setLoading(true);

    const abortCtrl = new AbortController();
    activeAbortCtrlRef.current = abortCtrl;

    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
      user_name: user.full_name,
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await sendChatMessage(text, mode, abortCtrl.signal);
      if (res.session_id) {
        setActiveSessionId(res.session_id);
      }
      const answer =
        res.choices?.[0]?.message?.content ||
        res.answer ||
        res.content ||
        '';
      const lucoMeta = res.luco || {};
      const usage = res.usage || {};
      const clarification =
        res.clarification ||
        res.choices?.[0]?.message?.clarification ||
        lucoMeta.clarification ||
        null;

      const assistantMsg: ChatMessage = {
        id: res.id || `bot-${Date.now()}`,
        role: 'assistant',
        content: answer,
        created_at: new Date().toISOString(),
        citations: lucoMeta.citations?.verified || lucoMeta.citations || [],
        trajectory: lucoMeta.trajectory || [],
        steps: lucoMeta.steps || 0,
        latency_s: usage.latency_s || res.usage?.latency_s || 0,
        prompt_tokens: usage.prompt_tokens,
        completion_tokens: usage.completion_tokens,
        total_tokens: usage.total_tokens,
        cost_idr: usage.estimated_cost_idr,
        rejected: lucoMeta.rejected || false,
        clarification: clarification,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Perbarui daftar sesi (judul sesi diperbarui otomatis di background)
      setTimeout(() => {
        listSessions().then(setSessions).catch(() => {});
      }, 1000);
    } catch (err: any) {
      // Jika dibatalkan karena diintersep oleh user
      if (err?.name === 'AbortError' || abortCtrl.signal.aborted) {
        console.log('Permintaan chat diintersep/dibatalkan oleh pengguna.');
        const interruptedNotice: ChatMessage = {
          id: `interrupted-${Date.now()}`,
          role: 'assistant',
          content: '_[Respons dihentikan karena pesan berikutnya dikirim]_',
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, interruptedNotice]);
        return;
      }

      const errMsgText = err?.message || '';
      // Jika token kedaluwarsa atau sesi login habis, buka modal login tanpa merusak percakapan
      if (
        errMsgText.includes('Sesi telah berakhir') ||
        errMsgText.includes('UNAUTHORIZED') ||
        errMsgText.includes('401')
      ) {
        clearAuth();
        setCurrentUserState(null);
        setIsLoginModalOpen(true);
        return;
      }
      const errMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Maaf, Luco mengalami kendala: ${errMsgText || 'Koneksi terputus'}. Silakan coba lagi 🙏`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      activeAbortCtrlRef.current = null;
      isSendingRef.current = false;
      setLoading(false);

      // Setelah giliran pesan ini selesai seutuhnya, proses pesan berikutnya di antrean secara strictly FIFO
      setTimeout(() => {
        if (!isSendingRef.current && queuedMessagesRef.current.length > 0) {
          const nextItem = queuedMessagesRef.current[0];
          setQueuedMessages((prev) => prev.slice(1));
          executeSendMessage(nextItem.content, nextItem.mode);
        }
      }, 100);
    }
  };

  // Handler Kirim Pesan: Jika sedang loading atau in-flight, masukkan ke Queue
  const handleSendMessage = (text: string, mode?: string) => {
    if (!user) {
      setIsLoginModalOpen(true);
      return;
    }
    const cleanText = text.trim();
    if (!cleanText) return;

    if (isSendingRef.current || loading) {
      const newItem: QueuedMessageItem = {
        id: `q-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        content: cleanText,
        mode: mode || 'viking_indobert',
        createdAt: Date.now(),
      };
      setQueuedMessages((prev) => [...prev, newItem]);
      return;
    }

    executeSendMessage(cleanText, mode);
  };

  // Intersep Pesan Antrean (Kirim Sekarang): Batalkan in-flight aktif dan langsung kirim pesan ini
  const handleSendQueueNow = (id: string) => {
    const item = queuedMessagesRef.current.find((q) => q.id === id);
    if (!item) return;

    // Hapus dari antrean
    setQueuedMessages((prev) => prev.filter((q) => q.id !== id));

    // Jika sedang ada respons AI yang sedang berjalan (in-flight), batalkan seketika!
    if (activeAbortCtrlRef.current) {
      activeAbortCtrlRef.current.abort();
      activeAbortCtrlRef.current = null;
    }
    isSendingRef.current = false;
    setLoading(false);

    // Jalankan segera pesan yang dipilih
    setTimeout(() => {
      executeSendMessage(item.content, item.mode);
    }, 50);
  };

  const handleRemoveQueuedMessage = (id: string) => {
    setQueuedMessages((prev) => prev.filter((q) => q.id !== id));
  };

  // 4. Handler Percakapan Baru (Mulai sesi baru, sesi lama diarsipkan ke riwayat)
  const handleNewChat = async () => {
    if (activeAbortCtrlRef.current) {
      activeAbortCtrlRef.current.abort();
      activeAbortCtrlRef.current = null;
    }
    isSendingRef.current = false;
    setLoading(false);
    setQueuedMessages([]);

    setIsSharedView(false);
    if (window.location.search) {
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    if (!user) {
      setMessages([]);
      return;
    }
    try {
      const newSess = await clearSession();
      setMessages([]);
      if (newSess?.session?.id) {
        setActiveSessionId(newSess.session.id);
      }
      const updatedList = await listSessions();
      setSessions(updatedList);
    } catch {
      setMessages([]);
    }
  };

  // 5. Handler Beralih Sesi (Buka riwayat percakapan lama beserta pesan-pesannya)
  const handleSelectSession = async (sessionId: string) => {
    if (activeAbortCtrlRef.current) {
      activeAbortCtrlRef.current.abort();
      activeAbortCtrlRef.current = null;
    }
    isSendingRef.current = false;
    setLoading(false);
    setQueuedMessages([]);

    setIsSharedView(false);
    try {
      const data = await switchSession(sessionId);
      if (data && data.messages) {
        setMessages(data.messages);
        setActiveSessionId(data.session?.id || sessionId);
        if (window.location.search) {
          window.history.replaceState({}, document.title, window.location.pathname);
        }
      }
      const updatedList = await listSessions();
      setSessions(updatedList);
    } catch (err) {
      console.error('Gagal beralih sesi:', err);
    }
  };

  // 6. Handler Hapus Sesi
  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteSession(sessionId);
      if (sessionId === activeSessionId) {
        await handleNewChat();
      } else {
        const updatedList = await listSessions();
        setSessions(updatedList);
      }
    } catch (err) {
      console.error('Gagal menghapus sesi:', err);
    }
  };

  const handleLogout = () => {
    clearAuth();
    setCurrentUserState(null);
    setMessages([]);
    setSessions([]);
    setIsAdminViewOpen(false);
  };

  // Handler Buka Dokumen Rujukan Spesifik
  const handleOpenDocument = (path: string) => {
    setSelectedDocPath(path);
  };

  return (
    <div className="h-screen h-[100dvh] w-screen bg-[#121214] text-zinc-100 flex flex-col overflow-hidden font-sans select-text">
      {/* Header */}
      <Header
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        onNewChat={handleNewChat}
        user={user}
        isAdminViewOpen={isAdminViewOpen}
        onToggleAdminView={user?.is_admin ? (open) => setIsAdminViewOpen(open) : undefined}
        onLogout={handleLogout}
        onOpenLogin={() => setIsLoginModalOpen(true)}
      />

      {/* Main Container */}
      <div className="flex-1 flex overflow-hidden relative">
        {isAdminViewOpen && user?.is_admin ? (
          /* Separate Admin Monitoring Dashboard */
          <MonitorView onClose={() => setIsAdminViewOpen(false)} />
        ) : (
          /* Standard Production Chatbot Interface */
          <>
            <Sidebar
              isOpen={isSidebarOpen}
              sessions={sessions}
              activeSessionId={activeSessionId}
              user={user}
              onNewChat={handleNewChat}
              onSelectSession={handleSelectSession}
              onDeleteSession={handleDeleteSession}
              onOpenCatalogue={() => setIsCatalogueOpen(true)}
              onOpenAdmin={user?.is_admin ? () => setIsAdminViewOpen(true) : undefined}
              onOpenLogin={() => setIsLoginModalOpen(true)}
              onLogout={handleLogout}
              onCloseMobile={() => setIsSidebarOpen(false)}
            />
            <ChatView
              messages={messages}
              loading={loading}
              onSendMessage={handleSendMessage}
              onSelectSuggestion={handleSendMessage}
              onOpenDocument={handleOpenDocument}
              onOpenCatalogue={() => setIsCatalogueOpen(true)}
              userEmail={user?.email}
              userName={user?.full_name}
              activeSessionId={activeSessionId}
              isSharedView={isSharedView}
              onNewChat={handleNewChat}
              queuedMessages={queuedMessages}
              onSendQueueNow={handleSendQueueNow}
              onRemoveQueuedMessage={handleRemoveQueuedMessage}
            />
          </>
        )}
      </div>

      {/* Full Document Catalogue Modal (Opened on-demand from sidebar or hero link) */}
      <DocumentCatalogModal
        isOpen={isCatalogueOpen}
        onClose={() => setIsCatalogueOpen(false)}
        onSelectDocument={(path) => {
          setIsCatalogueOpen(false);
          setSelectedDocPath(path);
        }}
      />

      {/* Specific Slide-over Document Drawer (only opened when user clicks a citation link) */}
      <DocumentDrawer
        isOpen={!!selectedDocPath}
        documentPath={selectedDocPath}
        onClose={() => setSelectedDocPath(null)}
        onAskLuco={(prompt) => handleSendMessage(prompt)}
        onSelectDoc={(path) => setSelectedDocPath(path)}
      />

      {/* Login Modal */}
      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onSuccess={(profile) => {
          setCurrentUserState(profile);
          loadChatData();
        }}
      />
    </div>
  );
};

export default App;
