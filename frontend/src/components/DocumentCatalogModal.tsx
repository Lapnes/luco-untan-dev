import React, { useState, useEffect, useMemo } from 'react';
import { fetchVaultDocuments, VaultDocumentSummary } from '../api';
import {
  X,
  Search,
  BookOpen,
  FileText,
  ChevronRight,
  ShieldCheck,
  Folder,
  GraduationCap,
  Briefcase,
  Users,
  Building,
  Sparkles,
} from 'lucide-react';

interface DocumentCatalogModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectDocument: (path: string) => void;
}

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  'kp-ta': <GraduationCap className="w-4 h-4 text-emerald-400" />,
  'akademik': <BookOpen className="w-4 h-4 text-blue-400" />,
  'dosen': <Users className="w-4 h-4 text-purple-400" />,
  'kemahasiswaan': <Briefcase className="w-4 h-4 text-amber-400" />,
  'fasilitas-lab': <Building className="w-4 h-4 text-cyan-400" />,
  'profil': <ShieldCheck className="w-4 h-4 text-rose-400" />,
  'dokumen': <FileText className="w-4 h-4 text-teal-400" />,
};

export const DocumentCatalogModal: React.FC<DocumentCatalogModalProps> = ({
  isOpen,
  onClose,
  onSelectDocument,
}) => {
  const [documents, setDocuments] = useState<VaultDocumentSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    fetchVaultDocuments()
      .then((docs) => {
        setDocuments(docs);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const categories = useMemo(() => {
    const map = new Map<string, { id: string; label: string; count: number }>();
    documents.forEach((d) => {
      const existing = map.get(d.category_id);
      if (existing) {
        existing.count += 1;
      } else {
        map.set(d.category_id, {
          id: d.category_id,
          label: d.category,
          count: 1,
        });
      }
    });
    return Array.from(map.values());
  }, [documents]);

  const filteredDocs = useMemo(() => {
    return documents.filter((d) => {
      const matchesCat = selectedCategory === 'all' || d.category_id === selectedCategory;
      const q = search.toLowerCase();
      const matchesSearch =
        !q ||
        d.title.toLowerCase().includes(q) ||
        d.path.toLowerCase().includes(q) ||
        d.summary.toLowerCase().includes(q) ||
        d.category.toLowerCase().includes(q);
      return matchesCat && matchesSearch;
    });
  }, [documents, selectedCategory, search]);

  if (!isOpen) return null;

  return (
    <>
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/75 backdrop-blur-md z-50 animate-in fade-in duration-200"
      />

      <div className="fixed inset-4 sm:inset-10 md:inset-16 z-50 flex items-center justify-center p-2 sm:p-4 pointer-events-none">
        <div
          className="w-full max-w-4xl h-full max-h-[85vh] bg-[#0d0f17]/95 border border-white/[0.1] rounded-3xl shadow-2xl flex flex-col overflow-hidden pointer-events-auto backdrop-blur-2xl animate-in zoom-in-95 duration-200"
        >
          {/* Header */}
          <div className="p-4 sm:p-6 border-b border-white/[0.08] flex items-center justify-between gap-4 bg-[#0a0c12]/80">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                  Katalog Dokumen & Regulasi Resmi
                  <span className="text-xs font-normal text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-full">
                    {documents.length} Dokumen
                  </span>
                </h2>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Basis pengetahuan resmi Informatika UNTAN yang dapat dibaca dan ditanyakan ke Luco
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.08] transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Search & Category Filter Bar */}
          <div className="p-4 border-b border-white/[0.06] bg-[#0c0e15]/60 flex flex-col gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-zinc-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Cari panduan skripsi, alur KP, kurikulum 2026, nama dosen, atau lab..."
                className="w-full bg-[#131622] border border-white/[0.08] focus:border-blue-500/60 rounded-xl pl-10 pr-4 py-2.5 text-xs text-zinc-200 placeholder-zinc-500 outline-none transition"
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 text-xs"
                >
                  ✕
                </button>
              )}
            </div>

            {/* Category Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              <button
                onClick={() => setSelectedCategory('all')}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium shrink-0 transition cursor-pointer ${
                  selectedCategory === 'all'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-white/[0.04] text-zinc-400 hover:bg-white/[0.08] hover:text-zinc-200 border border-white/[0.05]'
                }`}
              >
                Semua ({documents.length})
              </button>
              {categories.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setSelectedCategory(c.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium shrink-0 transition flex items-center gap-1.5 cursor-pointer ${
                    selectedCategory === c.id
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-white/[0.04] text-zinc-400 hover:bg-white/[0.08] hover:text-zinc-200 border border-white/[0.05]'
                  }`}
                >
                  {CATEGORY_ICONS[c.id] || <Folder className="w-3.5 h-3.5" />}
                  <span>{c.label}</span>
                  <span className="opacity-60 text-[10px]">({c.count})</span>
                </button>
              ))}
            </div>
          </div>

          {/* Document Grid */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 scrollbar-thin">
            {loading ? (
              <div className="py-20 flex flex-col items-center justify-center gap-3">
                <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
                <p className="text-xs text-zinc-400">Memuat katalog dokumen...</p>
              </div>
            ) : filteredDocs.length === 0 ? (
              <div className="py-16 text-center text-zinc-500 text-xs">
                Tidak ada dokumen yang cocok dengan kata kunci "{search}".
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {filteredDocs.map((d) => (
                  <div
                    key={d.path}
                    onClick={() => {
                      onSelectDocument(d.path);
                      onClose();
                    }}
                    className="p-4 rounded-2xl bg-[#131520]/80 hover:bg-[#181a28] border border-white/[0.06] hover:border-blue-500/40 transition-all duration-200 cursor-pointer group flex flex-col justify-between gap-3 shadow-sm hover:shadow-md hover:-translate-y-0.5"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-md">
                          {CATEGORY_ICONS[d.category_id]}
                          <span className="truncate">{d.category}</span>
                        </span>
                        <ChevronRight className="w-4 h-4 text-zinc-600 group-hover:text-blue-400 transition-transform group-hover:translate-x-0.5" />
                      </div>

                      <h3 className="text-sm font-semibold text-zinc-100 group-hover:text-white transition leading-snug">
                        {d.title}
                      </h3>

                      {d.summary && (
                        <p className="text-xs text-zinc-400 line-clamp-2 mt-1 leading-relaxed">
                          {d.summary}
                        </p>
                      )}
                    </div>

                    <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between text-[11px] text-zinc-500">
                      <span className="font-mono truncate">{d.path}</span>
                      <span className="text-blue-400 group-hover:underline flex items-center gap-0.5 shrink-0">
                        Buka Dokumen
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};
