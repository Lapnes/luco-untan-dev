import React, { useState, useEffect, useRef } from 'react';
import { fetchVaultDocument, VaultDocumentDetail, API_BASE } from '../api';
import { marked } from 'marked';
import {
  X,
  BookOpen,
  Check,
  Copy,
  MessageSquare,
  ShieldCheck,
  FileText,
  AlertCircle,
  ExternalLink,
  ChevronRight,
  ChevronLeft,
  Info,
  Download,
  Maximize2,
  Minimize2,
} from 'lucide-react';

interface DocumentDrawerProps {
  isOpen: boolean;
  documentPath: string | null;
  onClose: () => void;
  onAskLuco?: (prompt: string) => void;
  onSelectDoc?: (path: string) => void;
}

export const DocumentDrawer: React.FC<DocumentDrawerProps> = ({
  isOpen,
  documentPath,
  onClose,
  onAskLuco,
  onSelectDoc,
}) => {
  const [loading, setLoading] = useState(false);
  const [doc, setDoc] = useState<VaultDocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // History stack for in-drawer navigation (Previous & Next)
  const [history, setHistory] = useState<string[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(-1);
  const scrollRef = useRef<HTMLDivElement>(null);
  const prevPropPathRef = useRef<string | null>(null);

  // Resizable drawer width state (Desktop)
  const [drawerWidth, setDrawerWidth] = useState<number>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('luco_doc_drawer_width');
      if (saved) {
        const val = parseInt(saved, 10);
        if (!isNaN(val) && val >= 380 && val <= window.innerWidth) return val;
      }
      // Default 70% (~3/4 layar)
      const target70 = Math.floor(window.innerWidth * 0.70);
      return Math.min(Math.max(target70, 580), Math.floor(window.innerWidth * 0.85));
    }
    return 840;
  });
  const [isResizing, setIsResizing] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const newWidth = window.innerWidth - e.clientX;
      const minW = 380;
      // Memungkinkan resize sampai 85% layar (lebih dari 3/4 layar)
      const maxW = Math.max(Math.floor(window.innerWidth * 0.85), 1400);
      if (newWidth >= minW && newWidth <= maxW) {
        setDrawerWidth(newWidth);
        localStorage.setItem('luco_doc_drawer_width', String(newWidth));
      }
    };
    const handleMouseUp = () => {
      setIsResizing(false);
    };
    if (isResizing) {
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  // Sync external documentPath prop changes into history
  useEffect(() => {
    if (!isOpen) {
      setHistory([]);
      setCurrentIndex(-1);
      prevPropPathRef.current = null;
      setDoc(null);
      setError(null);
      return;
    }

    if (documentPath && documentPath !== prevPropPathRef.current) {
      prevPropPathRef.current = documentPath;
      setHistory((prev) => {
        // Drawer just opened
        if (prev.length === 0) {
          return [documentPath];
        }
        // If already at this doc, do not duplicate
        if (currentIndex >= 0 && prev[currentIndex] === documentPath) {
          return prev;
        }
        const next = prev.slice(0, currentIndex + 1);
        next.push(documentPath);
        return next;
      });
      setCurrentIndex((prevIdx) => (prevIdx === -1 ? 0 : prevIdx + 1));
    }
  }, [isOpen, documentPath]);

  // Current active path to view
  const currentPath = currentIndex >= 0 && history[currentIndex] ? history[currentIndex] : documentPath;

  // Fetch document whenever currentPath changes
  useEffect(() => {
    if (!isOpen || !currentPath) {
      setDoc(null);
      setError(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    // Reset scroll position to top on document change
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: 0, behavior: 'instant' });
    }

    fetchVaultDocument(currentPath)
      .then((data) => {
        if (isMounted) {
          setDoc(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Gagal memuat dokumen resmi.');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, currentPath]);

  // Navigate to internal link
  const navigateTo = (targetPath: string) => {
    if (!targetPath) return;
    if (currentIndex >= 0 && history[currentIndex] === targetPath) return;

    prevPropPathRef.current = targetPath;
    setHistory((prev) => {
      const next = prev.slice(0, currentIndex + 1);
      next.push(targetPath);
      return next;
    });
    setCurrentIndex((prev) => prev + 1);
    if (onSelectDoc) {
      onSelectDoc(targetPath);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      const targetPath = history[currentIndex - 1];
      prevPropPathRef.current = targetPath;
      setCurrentIndex((prev) => prev - 1);
      if (onSelectDoc) {
        onSelectDoc(targetPath);
      }
    }
  };

  const handleNext = () => {
    if (currentIndex < history.length - 1) {
      const targetPath = history[currentIndex + 1];
      prevPropPathRef.current = targetPath;
      setCurrentIndex((prev) => prev + 1);
      if (onSelectDoc) {
        onSelectDoc(targetPath);
      }
    }
  };

  // Keyboard shortcuts: Esc to close, Alt+Left for Prev, Alt+Right for Next
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        onClose();
        return;
      }

      // Alt + Left or Backspace (when not in input)
      if (
        (e.altKey && e.key === 'ArrowLeft') ||
        (e.key === 'Backspace' && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement))
      ) {
        if (currentIndex > 0) {
          e.preventDefault();
          handlePrev();
        }
      }

      // Alt + Right
      if (e.altKey && e.key === 'ArrowRight') {
        if (currentIndex < history.length - 1) {
          e.preventDefault();
          handleNext();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentIndex, history, onClose]);

  if (!isOpen) return null;

  const handleCopy = () => {
    if (!doc) return;
    navigator.clipboard.writeText(doc.content || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleAsk = () => {
    if (!doc || !onAskLuco) return;
    onAskLuco(`Jelaskan poin-poin penting dan aturan dari dokumen "${doc.title}"`);
    onClose();
  };

  const handleContentClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    const anchor = target.closest('a');
    if (!anchor) return;
    const href = anchor.getAttribute('href');
    if (!href) return;

    // 1. Tautan Web Eksternal (OpenAlex, Jurnal, Portal Luar, dsb): WAJIB Buka di Tab Baru!
    if (href.startsWith('http://') || href.startsWith('https://')) {
      e.preventDefault();
      e.stopPropagation();
      window.open(href, '_blank', 'noopener,noreferrer');
      return;
    }

    // 2. Tautan Internal Knowledge Vault (Markdown / Pedoman / Dosen / Panduan)
    e.preventDefault();
    e.stopPropagation();
    navigateTo(href);
  };

  const renderMarkdown = (content: string) => {
    try {
      const renderer = new marked.Renderer();
      const defaultLink = renderer.link.bind(renderer);
      renderer.link = (tokens) => {
        const { href, title, text } = tokens;
        if (href && (href.startsWith('http://') || href.startsWith('https://'))) {
          const titleAttr = title ? ` title="${title}"` : '';
          return `<a href="${href}"${titleAttr} target="_blank" rel="noopener noreferrer">${text}</a>`;
        }
        return defaultLink(tokens);
      };
      return { __html: marked.parse(content, { renderer }) as string };
    } catch {
      return { __html: content };
    }
  };

  return (
    <>
      {/* Backdrop with blur */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/70 backdrop-blur-md z-40 transition-opacity animate-in fade-in duration-200"
      />

      {/* Slide-over Drawer Panel with Resizable Width & Fullscreen Option */}
      <aside
        style={{
          width: typeof window !== 'undefined' && window.innerWidth < 768
            ? '100%'
            : (isMaximized ? '100vw' : `${drawerWidth}px`),
          maxWidth: '100vw',
        }}
        className={`fixed inset-y-0 right-0 z-50 bg-[#141418] border-l border-zinc-800 shadow-2xl flex flex-col transform transition-[width,transform] duration-200 ease-out animate-in slide-in-from-right ${
          isMaximized ? 'left-0 right-0 border-l-0' : ''
        }`}
      >
        {/* Resize Handle on Left Edge (Desktop) */}
        {!isMaximized && (
          <div
            onMouseDown={handleMouseDown}
            onDoubleClick={() => setDrawerWidth(Math.floor(window.innerWidth * 0.70))}
            title="Tahan dan geser untuk mengubah lebar panel (hingga 85% layar). Klik 2x untuk reset ke 70% (3/4 layar)."
            className="hidden md:flex absolute top-0 bottom-0 -left-1.5 w-3 cursor-col-resize items-center justify-center group z-50 select-none"
          >
            <div
              className={`w-1 h-16 rounded-full transition-all duration-200 ${
                isResizing ? 'bg-blue-500 h-28 w-1.5' : 'bg-zinc-700/60 group-hover:bg-blue-400 group-hover:h-20'
              }`}
            />
          </div>
        )}

        {/* Top Header */}
        <div className="p-3.5 sm:px-6 border-b border-zinc-800 flex items-center justify-between gap-3 bg-[#101014]">
          <div className="flex items-center gap-2.5 min-w-0">
            {/* History Navigation Buttons: Previous & Next */}
            <div className="flex items-center bg-zinc-900 border border-zinc-700/60 rounded-xl p-0.5 shrink-0 shadow-sm">
              <button
                onClick={handlePrev}
                disabled={currentIndex <= 0}
                title="Kembali ke dokumen sebelumnya (Alt + ←)"
                aria-label="Dokumen sebelumnya"
                className="w-7 h-7 rounded-lg hover:bg-zinc-800 disabled:opacity-20 disabled:pointer-events-none text-zinc-300 hover:text-white flex items-center justify-center transition cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <div className="w-[1px] h-3.5 bg-zinc-800" />
              <button
                onClick={handleNext}
                disabled={currentIndex >= history.length - 1}
                title="Maju ke dokumen berikutnya (Alt + →)"
                aria-label="Dokumen berikutnya"
                className="w-7 h-7 rounded-lg hover:bg-zinc-800 disabled:opacity-20 disabled:pointer-events-none text-zinc-300 hover:text-white flex items-center justify-center transition cursor-pointer"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            <div className="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700/60 flex items-center justify-center shrink-0">
              <BookOpen className="w-3.5 h-3.5 text-zinc-300" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold text-zinc-300 uppercase tracking-wider truncate">
                  {doc?.category || 'Rujukan Resmi'}
                </span>
                {history.length > 1 && (
                  <span className="text-[10px] text-zinc-400 font-mono bg-zinc-800/80 px-1.5 py-0.5 rounded border border-zinc-700/50 shrink-0">
                    {currentIndex + 1}/{history.length}
                  </span>
                )}
              </div>
              <div className="text-[11px] text-zinc-500 truncate flex items-center gap-1 mt-0.5 font-mono">
                <span className="text-zinc-400 truncate">{doc?.path || currentPath}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {doc && (
              <>
                <button
                  onClick={handleCopy}
                  title="Salin isi dokumen"
                  className="p-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-zinc-300 hover:text-white border border-white/[0.06] transition flex items-center gap-1.5 text-xs font-medium cursor-pointer"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Tersalin</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span className="hidden sm:inline">Salin</span>
                    </>
                  )}
                </button>

                {onAskLuco && (
                  <button
                    onClick={handleAsk}
                    className="p-2 px-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center gap-1.5 shadow-md shadow-blue-600/20 transition cursor-pointer"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Tanyakan</span>
                  </button>
                )}
              </>
            )}

            {/* Full Screen / Normal Toggle */}
            <button
              type="button"
              onClick={() => setIsMaximized((prev) => !prev)}
              title={isMaximized ? "Kembalikan ukuran normal (Keluar Full Screen)" : "Tampilan Layar Penuh (Full Screen 100%)"}
              className={`flex p-2 rounded-xl border transition items-center gap-1.5 text-xs font-medium cursor-pointer ${
                isMaximized
                  ? 'bg-blue-600/20 text-blue-400 border-blue-500/30 hover:bg-blue-600/30'
                  : 'bg-white/[0.04] hover:bg-white/[0.08] text-zinc-300 hover:text-white border-white/[0.06]'
              }`}
            >
              {isMaximized ? (
                <>
                  <Minimize2 className="w-4 h-4" />
                  <span className="hidden sm:inline">Normal</span>
                </>
              ) : (
                <>
                  <Maximize2 className="w-4 h-4" />
                  <span className="hidden sm:inline">Layar Penuh</span>
                </>
              )}
            </button>

            <button
              onClick={onClose}
              title="Tutup (Esc)"
              className="p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.08] transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Document Content */}
        <div
          ref={scrollRef}
          onClick={handleContentClick}
          className="flex-1 overflow-y-auto p-5 sm:p-8 space-y-6 scrollbar-thin select-text"
        >
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-4 text-center">
              <div className="w-10 h-10 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
              <p className="text-sm text-zinc-400">Membuka dokumen dari knowledge vault...</p>
            </div>
          ) : error ? (
            <div className="py-16 px-4 text-center flex flex-col items-center justify-center max-w-md mx-auto">
              <div className="w-12 h-12 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-3">
                <AlertCircle className="w-6 h-6 text-red-400" />
              </div>
              <h3 className="text-base font-semibold text-zinc-200 mb-1">
                Gagal Memuat Dokumen
              </h3>
              <p className="text-xs text-zinc-400 leading-relaxed mb-6">{error}</p>
              <div className="flex flex-wrap items-center justify-center gap-2">
                <button
                  onClick={() => onSelectDoc ? onSelectDoc('kp-ta/panduan-ta.md') : null}
                  className="px-3.5 py-1.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-zinc-300 hover:text-white transition cursor-pointer"
                >
                  Panduan KP / TA
                </button>
                <button
                  onClick={() => onSelectDoc ? onSelectDoc('akademik/kurikulum/2026/README.md') : null}
                  className="px-3.5 py-1.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-zinc-300 hover:text-white transition cursor-pointer"
                >
                  Kurikulum 2026
                </button>
                <button
                  onClick={onClose}
                  className="px-3.5 py-1.5 rounded-xl bg-zinc-800/60 hover:bg-zinc-800 text-xs font-medium text-zinc-400 hover:text-zinc-200 transition cursor-pointer"
                >
                  Kembali ke Chat
                </button>
              </div>
            </div>
          ) : doc ? (
            <div className="space-y-6">
              {/* Document Title Banner */}
              <div className="pb-4 border-b border-white/[0.08]">
                <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight leading-snug">
                  {doc.title}
                </h1>

                {/* Metadata Pills */}
                {doc.metadata && Object.keys(doc.metadata).length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-4 pt-3 border-t border-white/[0.06]">
                    {doc.metadata.nip && (
                      <span className="text-xs bg-zinc-800/80 text-zinc-300 border border-zinc-700/60 px-2.5 py-1 rounded-lg font-mono">
                        NIP: {doc.metadata.nip}
                      </span>
                    )}
                    {doc.metadata.email && (
                      <span className="text-xs bg-zinc-800/80 text-zinc-300 border border-zinc-700/60 px-2.5 py-1 rounded-lg">
                        ✉️ {doc.metadata.email}
                      </span>
                    )}
                    {doc.metadata.kelompok_keahlian && (
                      <span className="text-xs bg-blue-950/40 text-blue-300 border border-blue-500/30 px-2.5 py-1 rounded-lg font-medium">
                        🔬 KBK: {doc.metadata.kelompok_keahlian}
                      </span>
                    )}
                    {doc.metadata.jabatan && (
                      <span className="text-xs bg-purple-950/40 text-purple-300 border border-purple-500/30 px-2.5 py-1 rounded-lg">
                        👔 {doc.metadata.jabatan}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Dual Option: Berkas Asli (Raw) vs Naskah Markdown */}
              {(doc.metadata?.berkas_asli || doc.path.startsWith('dokumen/')) && (
                <div className="p-4 rounded-2xl bg-gradient-to-r from-blue-950/40 via-zinc-900 to-indigo-950/30 border border-blue-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0">
                      <FileText className="w-4 h-4 text-blue-400" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-zinc-100 flex items-center gap-1.5">
                        <span>Berkas Master Asli</span>
                        <span className="text-[10px] font-mono uppercase bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded border border-blue-500/30">
                          {doc.metadata?.format || 'PDF/DOCX'}
                        </span>
                      </div>
                      <div className="text-[11px] text-zinc-400 mt-0.5">
                        Tersedia berkas asli bertanda tangan/stempel atau ekspor teks Markdown.
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <a
                      href={`${API_BASE}/v1/dokumen/${doc.path.replace('dokumen/', '').replace('.md', '')}/raw`}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                      className="px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium flex items-center gap-1.5 transition shadow-md shadow-blue-600/20 cursor-pointer"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Unduh {doc.metadata?.format || 'Asli'}</span>
                    </a>
                    <a
                      href={`${API_BASE}/v1/dokumen/${doc.path.replace('dokumen/', '').replace('.md', '')}/export.md`}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                      className="px-3 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-zinc-200 text-xs font-medium flex items-center gap-1.5 border border-white/[0.08] transition cursor-pointer"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Ekspor .md</span>
                    </a>
                  </div>
                </div>
              )}

              {/* Rendered Markdown Body */}
              <article
                className="prose-luco text-zinc-200 text-[15px] leading-relaxed"
                dangerouslySetInnerHTML={renderMarkdown(doc.content)}
              />

              {/* Academic Source Disclaimer */}
              <div className="mt-8 p-4 rounded-2xl bg-blue-950/20 border border-blue-500/20 text-xs text-blue-200/80 leading-relaxed flex items-start gap-3">
                <ShieldCheck className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-blue-300 block mb-0.5">
                    Rujukan Resmi Fakultas Teknik Universitas Tanjungpura
                  </span>
                  Dokumen ini merupakan sumber kebenaran resmi (*single source of truth*) yang
                  diindeks ke dalam Luco Knowledge Vault untuk asistensi mahasiswa & dosen.
                </div>
              </div>
            </div>
          ) : null}
        </div>

        {/* Bottom Drawer Actions */}
        {doc && (
          <div className="p-4 sm:px-6 border-t border-white/[0.08] bg-[#0a0c12]/90 flex items-center justify-between gap-4">
            <span className="text-xs text-zinc-400 truncate flex items-center">
              <Info className="w-3.5 h-3.5 text-zinc-400 shrink-0 mr-1.5 inline" />
              Klik tautan apa pun di dalam teks untuk membuka bab lainnya
            </span>

            {onAskLuco && (
              <button
                onClick={handleAsk}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center gap-2 shadow-lg shadow-blue-600/20 transition cursor-pointer shrink-0"
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>Bahas bersama Luco</span>
              </button>
            )}
          </div>
        )}
      </aside>
    </>
  );
};
