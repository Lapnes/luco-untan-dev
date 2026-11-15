import React, { useState, useRef, useEffect, useMemo } from 'react';
import { ChatMessage, sendFeedback } from '../api';
import { marked } from 'marked';
import hljs from 'highlight.js';
import 'highlight.js/styles/atom-one-dark.css';
import {
  ArrowUp,
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
  Sparkles,
  GraduationCap,
  Briefcase,
  Users,
  Compass,
  BookOpen,
  Cpu,
  Layers,
  Zap,
  MessageSquare,
  X,
  PenLine,
  FileDown,
  Link,
  Share2,
  ThumbsUp,
  ThumbsDown,
  Eye,
  Code2,
  FileText,
  ArrowRight,
  Pencil,
  Trash2,
  CornerDownLeft,
  Maximize2,
  Minimize2,
} from 'lucide-react';

export interface QueuedMessageItem {
  id: string;
  content: string;
  mode: string;
  createdAt: number;
}

export interface ParsedMarkdownDoc {
  hasDocument: boolean;
  introText?: string;
  docContent: string;
  rawDocSource: string;
}

export const parseMarkdownDocument = (raw: string): ParsedMarkdownDoc => {
  if (!raw) return { hasDocument: false, docContent: '', rawDocSource: '' };
  const trimmed = raw.trim();

  // Pola 1: Jika terdapat 4-backtick fence sampai akhir pesan
  const fence4Regex = /(?:^|\n)````(?:markdown|md)?\s*[\r\n]+([\s\S]*?)[\r\n]+````(?:\s*)$/i;
  const match4 = trimmed.match(fence4Regex);
  if (match4) {
    const intro = trimmed.slice(0, match4.index).trim();
    return {
      hasDocument: true,
      introText: intro || undefined,
      docContent: match4[1].trim(),
      rawDocSource: match4[1].trim(),
    };
  }

  // Pola 2: 3-backtick fence sampai akhir pesan
  const fence3Regex = /(?:^|\n)```(?:markdown|md)?\s*[\r\n]+([\s\S]*?)[\r\n]+```(?:\s*)$/i;
  const match3 = trimmed.match(fence3Regex);
  if (match3) {
    const intro = trimmed.slice(0, match3.index).trim();
    return {
      hasDocument: true,
      introText: intro || undefined,
      docContent: match3[1].trim(),
      rawDocSource: match3[1].trim(),
    };
  }

  // Pola 3: Blok ```markdown / ````markdown di mana saja dalam pesan
  const anyMdRegex = /(?:^|\n)(`{3,4})(?:markdown|md)\s*[\r\n]+([\s\S]*?)[\r\n]+\1(?:\n|$)/i;
  const matchAny = trimmed.match(anyMdRegex);
  if (matchAny) {
    const intro = trimmed.slice(0, matchAny.index).trim();
    return {
      hasDocument: true,
      introText: intro || undefined,
      docContent: matchAny[2].trim(),
      rawDocSource: matchAny[2].trim(),
    };
  }

  // Pola 4: Seluruh teks adalah dokumen terstruktur (# Judul dan ## / | )
  if (
    trimmed.startsWith('# ') &&
    (trimmed.includes('\n## ') || trimmed.includes('\n| ') || trimmed.includes('\n- ')) &&
    trimmed.length > 200
  ) {
    return {
      hasDocument: true,
      introText: undefined,
      docContent: trimmed,
      rawDocSource: trimmed,
    };
  }

  return {
    hasDocument: false,
    introText: undefined,
    docContent: trimmed,
    rawDocSource: trimmed,
  };
};

interface ChatViewProps {
  messages: ChatMessage[];
  loading: boolean;
  onSendMessage: (content: string, mode?: string) => void;
  onSelectSuggestion: (text: string) => void;
  onOpenDocument: (path: string, title?: string) => void;
  onOpenCatalogue?: () => void;
  userEmail?: string;
  userName?: string;
  activeSessionId?: string | null;
  isSharedView?: boolean;
  onNewChat?: () => void;
  queuedMessages?: QueuedMessageItem[];
  onSendQueueNow?: (id: string) => void;
  onRemoveQueuedMessage?: (id: string) => void;
}

const INFERENCE_MODES: {
  id: string;
  name: string;
  short: string;
  desc: string;
  badge: string;
  icon: React.ReactNode;
}[] = [
  {
    id: 'viking_indobert',
    name: 'IndoBERT + OpenViking',
    short: 'IndoBERT + Viking',
    desc: 'Hybrid Agentic RAG dengan Re-ranking IndoBERT (Akurasi Maksimal)',
    badge: 'Rekomendasi',
    icon: <Layers className="w-4 h-4 text-sky-400 shrink-0" />,
  },
  {
    id: 'viking_fast',
    name: 'OpenViking Cepat',
    short: 'Viking Cepat',
    desc: 'Pencarian Vektor & Keyword Langsung (Respons Instan)',
    badge: 'Cepat',
    icon: <Zap className="w-4 h-4 text-amber-400 shrink-0" />,
  },
  {
    id: 'direct_llm',
    name: 'Direct LLM Standar',
    short: 'Direct LLM',
    desc: 'Inferensi Model Langsung Tanpa RAG Dokumen',
    badge: 'Umum',
    icon: <MessageSquare className="w-4 h-4 text-zinc-400 shrink-0" />,
  },
];

const STARTER_PROMPTS = [
  {
    icon: <GraduationCap className="w-4 h-4 text-emerald-400" />,
    label: 'Syarat Proposal Skripsi',
    desc: 'Minimal 110 SKS, IPK, MK prasyarat, & SPOTA',
    prompt: 'Apa saja syarat mengajukan proposal TA/skripsi di Informatika UNTAN?',
  },
  {
    icon: <Briefcase className="w-4 h-4 text-blue-400" />,
    label: 'Alur Kerja Praktik (KP)',
    desc: 'Prosedur pendaftaran, bimbingan, dan seminar KP',
    prompt: 'Bagaimana alur dan syarat Kerja Praktik (KP)?',
  },
  {
    icon: <Users className="w-4 h-4 text-purple-400" />,
    label: 'Profil Dosen Informatika',
    desc: 'Bidang riset, KBK, dan NIP dosen prodi',
    prompt: 'Siapa Pak Izuardo Zulkarnain dan apa bidang risetnya?',
  },
  {
    icon: <Compass className="w-4 h-4 text-amber-400" />,
    label: 'Kurikulum 2026 vs 2016',
    desc: 'Struktur kurikulum OBE dan sebaran mata kuliah',
    prompt: 'Apa perbedaan Kurikulum 2026 dan 2016 di Informatika UNTAN?',
  },
];

export const ChatView: React.FC<ChatViewProps> = ({
  messages,
  loading,
  onSendMessage,
  onSelectSuggestion,
  onOpenDocument,
  onOpenCatalogue,
  userEmail,
  userName,
  activeSessionId,
  isSharedView = false,
  onNewChat,
  queuedMessages = [],
  onSendQueueNow,
  onRemoveQueuedMessage,
}) => {
  const [input, setInput] = useState('');
  const [selectedMode, setSelectedMode] = useState<string>('viking_indobert');
  const [isModeMenuOpen, setIsModeMenuOpen] = useState(false);
  const [openThoughts, setOpenThoughts] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [dismissedClarifications, setDismissedClarifications] = useState<Record<string, boolean>>({});
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [isLinkCopied, setIsLinkCopied] = useState<boolean>(false);
  const [isTextCopied, setIsTextCopied] = useState<boolean>(false);
  const [feedbackState, setFeedbackState] = useState<Record<string, 'like' | 'dislike' | 'none'>>({});
  const [rawModeMap, setRawModeMap] = useState<Record<string, boolean>>({});
  const [copiedDocMap, setCopiedDocMap] = useState<Record<string, boolean>>({});
  const [isQueueCollapsed, setIsQueueCollapsed] = useState(false);
  const [promptHistory, setPromptHistory] = useState<string[]>([]);
  const [historyCursor, setHistoryCursor] = useState<number>(-1);
  const [draftInput, setDraftInput] = useState<string>('');
  const [inputViewMode, setInputViewMode] = useState<'write' | 'preview'>('write');
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  const hasMarkdownInInput = useMemo(() => {
    const t = input.trim();
    return (
      t.includes('# ') ||
      t.includes('\n#') ||
      t.includes('- ') ||
      t.includes('* ') ||
      t.includes('```') ||
      t.includes('|') ||
      t.includes('**')
    );
  }, [input]);

  // Inisialisasi riwayat input user dari percakapan yang ada
  useEffect(() => {
    const userPrompts = messages
      .filter((m) => m.role === 'user' && m.content && m.content.trim())
      .map((m) => m.content.trim());
    if (userPrompts.length > 0) {
      setPromptHistory((prev) => {
        const combined = Array.from(new Set([...userPrompts, ...prev]));
        return combined;
      });
    }
  }, [messages]);

  const handleRemoveQueuedItem = (id: string) => {
    onRemoveQueuedMessage?.(id);
    showToast('Pesan dihapus dari antrean.');
  };

  const handleEditQueuedItem = (id: string) => {
    const item = queuedMessages.find((m) => m.id === id);
    if (!item) return;
    onRemoveQueuedMessage?.(id);
    setInput(item.content);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
    showToast('Pesan dikembalikan ke kolom input chat.');
  };

  const handleSendQueueNowItem = (id: string) => {
    onSendQueueNow?.(id);
  };

  const handleFeedback = async (messageId: string, type: 'like' | 'dislike') => {
    const current = feedbackState[messageId];
    const newFeedback = current === type ? 'none' : type;
    setFeedbackState((prev) => ({ ...prev, [messageId]: newFeedback }));
    try {
      await sendFeedback(messageId, newFeedback);
      if (newFeedback === 'like') {
        showToast('Terima kasih atas tanggapan positif Anda! 👍');
      } else if (newFeedback === 'dislike') {
        showToast('Terima kasih atas masukan evaluasi Anda! 👎');
      }
    } catch (e) {
      console.warn('Gagal mencatat feedback reaksi:', e);
    }
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((prev) => (prev === msg ? null : prev));
    }, 2800);
  };

  const generateMarkdownContent = (): string => {
    const dateStr = new Date().toLocaleDateString('id-ID', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

    const lines: string[] = [
      '# Rangkuman Percakapan Luco: Asisten Cerdas Informatika UNTAN',
      '',
      `> **Tanggal Ekspor**: ${dateStr}  `,
      `> **Mahasiswa**: ${userName || 'Mahasiswa Informatika'} ${userEmail ? `(${userEmail})` : ''}  `,
      `> **Sumber Rujukan**: Dokumen Resmi Knowledge Vault Prodi Informatika, Fakultas Teknik UNTAN  `,
      `> **Mode Inferensi**: ${selectedMode}  `,
      '',
      '---',
      '',
    ];

    messages.forEach((msg) => {
      const isUser = msg.role === 'user';
      if (isUser) {
        lines.push(`## 👤 Pertanyaan Mahasiswa:`);
        lines.push(msg.content);
        lines.push('');
      } else {
        lines.push(`## 🐦 Jawaban Luco:`);
        lines.push(msg.content);
        lines.push('');

        if (msg.citations && msg.citations.length > 0) {
          lines.push('### 📚 Rujukan Dokumen Resmi:');
          msg.citations.forEach((c: any) => {
            const rawTarget =
              typeof c === 'object'
                ? c.target || c.url || c.file || c.path || ''
                : typeof c === 'string'
                  ? c
                  : '';
            const rawText =
              typeof c === 'object'
                ? c.text || c.title || c.name || ''
                : typeof c === 'string'
                  ? c
                  : '';
            const title = rawText || rawTarget || 'Dokumen Resmi';
            const target = rawTarget || title;
            lines.push(`- [${title}](${target})`);
          });
          lines.push('');
        }

        if (msg.clarification?.options?.length) {
          lines.push('### Opsi Klarifikasi Topik:');
          msg.clarification.options.forEach((opt: string, i: number) => {
            lines.push(`${i + 1}. ${opt}`);
          });
          lines.push('');
        }

        lines.push('---');
        lines.push('');
      }
    });

    lines.push('*Dokumen ini dihasilkan secara otomatis oleh Luco — Chatbot Informasi Prodi Informatika UNTAN.*');
    return lines.join('\n');
  };

  const handleExportMarkdown = () => {
    if (messages.length === 0) return;
    const content = generateMarkdownContent();
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const safeTitle = (messages[0]?.content.slice(0, 30) || 'percakapan')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
    a.href = url;
    a.download = `luco-${safeTitle || 'catatan'}-${Date.now().toString().slice(-4)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Dokumen Markdown (.md) berhasil diunduh!');
  };

  const copyTextToClipboard = async (text: string): Promise<boolean> => {
    // 1. Coba document.execCommand('copy') secara sinkron terlebih dahulu
    // Ini krusial untuk Chrome Incognito / Safari di mana user gesture token hilang jika didahului async/await
    try {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      // Posisikan di luar viewport tanpa display:none agar seleksi teks valid
      textArea.style.position = 'fixed';
      textArea.style.top = '-9999px';
      textArea.style.left = '-9999px';
      textArea.style.opacity = '0';
      textArea.setAttribute('tabindex', '-1');
      textArea.setAttribute('aria-hidden', 'true');
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      textArea.setSelectionRange(0, text.length);
      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);
      if (successful) return true;
    } catch (err) {
      console.warn('execCommand copy sinkron gagal, mencoba Clipboard API:', err);
    }

    // 2. Fallback: Clipboard API modern
    if (navigator?.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch (err) {
        console.warn('navigator.clipboard.writeText gagal:', err);
      }
    }

    // 3. Fallback terakhir: prompt manual agar pengguna tetap bisa menyalin link
    try {
      window.prompt('Salin tautan percakapan berikut (Ctrl+C / Cmd+C lalu Enter):', text);
      return true;
    } catch {
      return false;
    }
  };

  const handleCopyShareLink = async (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    try {
      const origin = window.location.origin;
      const pathname = window.location.pathname;
      const searchParams = new URLSearchParams(window.location.search);
      const targetSessionId = activeSessionId || searchParams.get('session');

      let shareUrl = `${origin}${pathname}`;
      if (targetSessionId) {
        shareUrl += `?session=${encodeURIComponent(targetSessionId)}`;
      }

      const success = await copyTextToClipboard(shareUrl);
      if (success) {
        setIsLinkCopied(true);
        showToast('Tautan obrolan berhasil disalin ke clipboard!');
        setTimeout(() => setIsLinkCopied(false), 2500);
      } else {
        showToast('Gagal menyalin tautan.');
      }
    } catch (err) {
      console.error('Error saat menyalin tautan:', err);
      showToast('Gagal menyalin tautan.');
    }
  };

  const handleCopyFullText = async (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (messages.length === 0) return;
    const content = generateMarkdownContent();
    const success = await copyTextToClipboard(content);
    if (success) {
      setIsTextCopied(true);
      showToast('Seluruh teks obrolan berhasil disalin!');
      setTimeout(() => setIsTextCopied(false), 2500);
    } else {
      showToast('Gagal menyalin teks.');
    }
  };

  const handleSelectClarification = (optionText: string) => {
    onSendMessage(optionText, selectedMode);
  };

  const handleDismissClarification = (msgId: string) => {
    setDismissedClarifications((prev) => ({ ...prev, [msgId]: true }));
  };

  const handleCustomAnswer = () => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const modeMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (textareaRef.current) {
      if (!isExpanded) {
        textareaRef.current.style.height = 'auto';
        const newH = Math.max(60, Math.min(textareaRef.current.scrollHeight, 340));
        textareaRef.current.style.height = `${newH}px`;
      } else {
        textareaRef.current.style.height = '380px';
      }
    }
  }, [input, isExpanded]);

  // Click outside to close mode switcher dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (modeMenuRef.current && !modeMenuRef.current.contains(e.target as Node)) {
        setIsModeMenuOpen(false);
      }
    };
    if (isModeMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isModeMenuOpen]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const text = input.trim();
    if (!text) return;

    setPromptHistory((prev) => {
      const filtered = prev.filter((p) => p !== text);
      return [...filtered, text];
    });
    setHistoryCursor(-1);
    setDraftInput('');
    onSendMessage(text, selectedMode);
    setInput('');
    setInputViewMode('write');

    if (loading) {
      showToast('Pesan masuk ke antrean! Akan diproses otomatis setelah agen selesai.');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Pintasan keyboard Ctrl+P / Cmd+P untuk toggle pratinjau Markdown
    if ((e.metaKey || e.ctrlKey) && (e.key === 'p' || e.key === 'P')) {
      e.preventDefault();
      setInputViewMode((prev) => (prev === 'write' ? 'preview' : 'write'));
      return;
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
      return;
    }

    // Auto-continuation untuk list saat Shift + Enter (misal "- item" -> otomatis baris baru ada "- ")
    if (e.key === 'Enter' && e.shiftKey) {
      const textarea = e.currentTarget;
      const { selectionStart, selectionEnd, value } = textarea;
      const textBeforeCursor = value.substring(0, selectionStart);
      const lines = textBeforeCursor.split('\n');
      const currentLine = lines[lines.length - 1];

      // Cek apakah baris diawali bullet list: "- ", "* ", "+ " atau nomor: "1. "
      const match = currentLine.match(/^(\s*)([-*+]|\d+\.)\s+/);
      if (match) {
        const [, indent, bullet] = match;
        // Jika baris saat ini hanya berisi bullet kosong (misal cuma "- "), hapus bulletnya
        if (currentLine.trim() === bullet.trim()) {
          e.preventDefault();
          const lineStartIndex = selectionStart - currentLine.length;
          const nextVal = value.substring(0, lineStartIndex) + value.substring(selectionStart);
          setInput(nextVal);
          setTimeout(() => {
            textarea.selectionStart = textarea.selectionEnd = lineStartIndex;
          }, 0);
          return;
        }

        e.preventDefault();
        let nextMarker = `${indent}${bullet} `;
        if (/^\d+\./.test(bullet)) {
          const num = parseInt(bullet, 10);
          nextMarker = `${indent}${num + 1}. `;
        }
        const nextVal =
          value.substring(0, selectionStart) + '\n' + nextMarker + value.substring(selectionEnd);
        setInput(nextVal);
        setTimeout(() => {
          textarea.selectionStart = textarea.selectionEnd = selectionStart + 1 + nextMarker.length;
        }, 0);
        return;
      }
    }

    // Navigasi Riwayat Prompt dengan Arrow Up / Down (Terminal & AI Standard)
    if (e.key === 'ArrowUp') {
      const target = e.currentTarget;
      const isAtStart = target.selectionStart === 0 && target.selectionEnd === 0;
      if (isAtStart || !input.trim()) {
        if (promptHistory.length === 0) return;
        e.preventDefault();
        let nextCursor = historyCursor + 1;
        if (historyCursor === -1) {
          setDraftInput(input);
          nextCursor = 0;
        }
        if (nextCursor < promptHistory.length) {
          setHistoryCursor(nextCursor);
          const historyText = promptHistory[promptHistory.length - 1 - nextCursor];
          setInput(historyText);
        }
      }
    } else if (e.key === 'ArrowDown') {
      if (historyCursor !== -1) {
        e.preventDefault();
        const nextCursor = historyCursor - 1;
        if (nextCursor >= 0) {
          setHistoryCursor(nextCursor);
          const historyText = promptHistory[promptHistory.length - 1 - nextCursor];
          setInput(historyText);
        } else {
          setHistoryCursor(-1);
          setInput(draftInput);
        }
      }
    } else {
      if (historyCursor !== -1 && e.key.length === 1) {
        setHistoryCursor(-1);
      }
    }
  };

  const toggleThought = (id: string) => {
    setOpenThoughts((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCopy = (content: string, id: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Intercept click tautan di dalam markdown & tombol salin kode
  const handleContentClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;

    // 1. Cek apakah pengguna mengklik tombol salin pada blok kode
    const copyCodeBtn = target.closest('.copy-code-btn') as HTMLButtonElement | null;
    if (copyCodeBtn) {
      e.preventDefault();
      e.stopPropagation();
      const encoded = copyCodeBtn.getAttribute('data-code');
      if (encoded) {
        const rawCode = decodeURIComponent(encoded);
        copyTextToClipboard(rawCode).then((ok) => {
          if (ok) {
            const label = copyCodeBtn.querySelector('.copy-label');
            if (label) {
              const orig = label.textContent;
              label.textContent = 'Tersalin ✓';
              copyCodeBtn.classList.add('text-emerald-400');
              setTimeout(() => {
                label.textContent = orig;
                copyCodeBtn.classList.remove('text-emerald-400');
              }, 2000);
            }
            showToast('Kode berhasil disalin ke clipboard!');
          }
        });
      }
      return;
    }

    const anchor = target.closest('a');
    if (!anchor) return;
    const href = anchor.getAttribute('href');
    if (!href) return;

    const isExternal = href.startsWith('http://') || href.startsWith('https://');
    const isVaultDocument =
      !isExternal ||
      href.includes('uas-ai.ragilamirzaky.com/v1/vault') ||
      (href.endsWith('.md') && !href.includes('openalex.org') && !href.includes('google.com'));

    // Tautan web eksternal (OpenAlex, Jurnal, link luar): Buka di tab baru
    if (isExternal && !isVaultDocument) {
      e.preventDefault();
      e.stopPropagation();
      window.open(href, '_blank', 'noopener,noreferrer');
      return;
    }

    // Tautan dokumen resmi vault
    if (isVaultDocument) {
      e.preventDefault();
      e.stopPropagation();
      onOpenDocument(href, anchor.innerText);
    }
  };

  const renderMarkdown = (content: string) => {
    try {
      const renderer = new marked.Renderer();
      const defaultLink = renderer.link.bind(renderer);
      renderer.link = (tokens) => {
        const { href, title, text } = tokens;
        if (
          href &&
          (href.startsWith('http://') || href.startsWith('https://')) &&
          !href.includes('uas-ai.ragilamirzaky.com/v1/vault')
        ) {
          const titleAttr = title ? ` title="${title}"` : '';
          return `<a href="${href}"${titleAttr} target="_blank" rel="noopener noreferrer">${text}</a>`;
        }
        return defaultLink(tokens);
      };

      renderer.code = (token: any, langToken?: string) => {
        const codeText = typeof token === 'object' ? (token.text ?? '') : String(token ?? '');
        const lang = typeof token === 'object' ? (token.lang || 'text') : (langToken || 'text');
        const encoded = encodeURIComponent(codeText);
        const safeLang = (lang || 'text').toLowerCase();

        // JIKA BLOK MARKDOWN DI DALAM CHAT (misal ```markdown ... ```):
        // Render sebagai Markdown HTML yang diformat indah seperti Claude, BUKAN kotak kode monospaced!
        if (safeLang === 'markdown' || safeLang === 'md') {
          const renderedInner = marked.parse(codeText);
          return `<div class="embedded-md-doc my-3 p-4 sm:p-5 rounded-2xl bg-[#131318] border border-zinc-800/80 shadow-md prose-luco not-prose">${renderedInner}</div>`;
        }

        // Highlight sintaks warna sesuai bahasa pemformatan (C++, Python, JS, SQL, Bash, JSON, dll)
        let highlightedCode = '';
        if (safeLang && hljs.getLanguage(safeLang)) {
          try {
            highlightedCode = hljs.highlight(codeText, { language: safeLang, ignoreIllegals: true }).value;
          } catch {
            highlightedCode = '';
          }
        }
        if (!highlightedCode) {
          try {
            const autoRes = hljs.highlightAuto(codeText);
            highlightedCode = autoRes.value;
          } catch {
            highlightedCode = codeText
              .replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#39;');
          }
        }

        return `<div class="code-block-container my-3 rounded-xl border border-zinc-800 bg-[#111115] overflow-hidden shadow-sm not-prose">
          <div class="flex items-center justify-between px-3.5 py-1.5 bg-[#18181e] border-b border-zinc-800 text-[11px] font-mono text-zinc-400 select-none">
            <span class="flex items-center gap-1.5 font-medium text-zinc-300">
              <span class="w-1.5 h-1.5 rounded-full bg-sky-400 inline-block"></span>
              ${safeLang || 'code'}
            </span>
            <button type="button" class="copy-code-btn inline-flex items-center gap-1 px-2 py-0.5 rounded text-zinc-400 hover:text-white hover:bg-zinc-700/60 transition cursor-pointer" data-code="${encoded}">
              <svg class="w-3 h-3 copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
              <span class="copy-label font-sans text-xs">Salin</span>
            </button>
          </div>
          <pre class="p-3.5 overflow-x-auto text-xs sm:text-sm font-mono text-zinc-200 leading-relaxed bg-[#111115] m-0 border-0 hljs"><code class="hljs language-${safeLang}">${highlightedCode}</code></pre>
        </div>`;
      };

      return { __html: marked.parse(content, { renderer, breaks: true, gfm: true }) as string };
    } catch {
      return { __html: content };
    }
  };

  const getUserInitials = () => {
    if (userName) {
      const parts = userName.trim().split(' ');
      if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      return userName.slice(0, 2).toUpperCase();
    }
    if (userEmail) {
      return userEmail.slice(0, 2).toUpperCase();
    }
    return 'MP'; // Mahasiswa Penguji
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0d0d10] text-zinc-100 overflow-hidden relative">
      {/* Shared Session Alert Banner */}
      {isSharedView && (
        <div className="shrink-0 mx-4 sm:mx-8 mt-3 mb-1 px-3.5 py-2.5 rounded-xl bg-blue-950/40 border border-blue-500/30 text-blue-200 text-xs flex items-center justify-between gap-3 shadow-md backdrop-blur-sm animate-fade-in">
          <div className="flex items-center gap-2 min-w-0">
            <Link className="w-4 h-4 text-blue-400 shrink-0" />
            <span className="truncate">
              Menampilkan <strong>arsip sesi yang dibagikan</strong> (read-only snapshot).
            </span>
          </div>
          {onNewChat && (
            <button
              onClick={onNewChat}
              className="px-3 py-1 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shrink-0 cursor-pointer transition shadow-sm"
            >
              Obrolan Baru
            </button>
          )}
        </div>
      )}

      {/* Scrollable Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-8 py-6 scrollbar-thin">
        <div className="max-w-3xl mx-auto w-full flex flex-col gap-6">
          {/* Header Bar: Status Indicator + Kimi-style Action Toolbar when messages exist */}
          <div className="flex items-center justify-between my-2 flex-wrap gap-2">
            <span className="text-[11px] font-semibold tracking-wider text-zinc-400 bg-zinc-900 border border-zinc-800 px-3.5 py-1.5 rounded-full uppercase">
              Conversation with Luco Assistant
            </span>

            {messages.length > 0 && (
              <div className="flex items-center gap-1.5 bg-[#141418] border border-zinc-800 rounded-xl p-1 shadow-sm">
                <button
                  type="button"
                  onClick={handleCopyShareLink}
                  title="Salin tautan percakapan"
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs text-zinc-300 hover:text-white hover:bg-zinc-800 transition cursor-pointer font-medium"
                >
                  {isLinkCopied ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <Link className="w-3.5 h-3.5 text-zinc-400" />
                  )}
                  <span>{isLinkCopied ? 'Tersalin' : 'Copy link'}</span>
                </button>

                <button
                  type="button"
                  onClick={handleExportMarkdown}
                  title="Unduh percakapan sebagai dokumen Markdown (.md)"
                  className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs bg-zinc-800 hover:bg-zinc-700 text-sky-300 hover:text-sky-200 border border-zinc-700/80 transition cursor-pointer font-semibold shadow-sm"
                >
                  <FileDown className="w-3.5 h-3.5 text-sky-400" />
                  <span>Export .md</span>
                </button>
              </div>
            )}
          </div>

          {messages.length === 0 ? (
            /* Spacious Modern Hero (Matching Images 6 & 12) */
            <div className="min-h-[55vh] flex flex-col items-center justify-center text-center px-4 py-8">
              <div className="w-20 h-20 rounded-3xl bg-zinc-800/90 border border-zinc-700/80 flex items-center justify-center shadow-xl mb-5 p-2">
                <img
                  src="/luco-logo.png"
                  alt="Luco Mascot"
                  className="w-full h-full object-contain drop-shadow"
                />
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-2">
                Halo! Saya Luco 👋
              </h1>
              <p className="text-sm text-zinc-400 max-w-lg mb-8 leading-relaxed">
                Asisten resmi seputar regulasi akademik, kurikulum, alur KP/TA, dan profil dosen Informatika Fakultas Teknik UNTAN.
              </p>

              {/* 4 Spacious Starter Prompt Cards (Matching Image 6) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full max-w-xl text-left mb-6">
                {STARTER_PROMPTS.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => onSelectSuggestion(item.prompt)}
                    className="p-4 rounded-2xl border border-zinc-800 bg-[#151518] hover:bg-[#1c1c22] hover:border-zinc-700 transition-all duration-200 cursor-pointer flex items-center gap-3.5 group shadow-sm hover:shadow-md active:scale-98"
                  >
                    <div className="p-2.5 rounded-xl bg-zinc-800/80 border border-zinc-700/60 group-hover:bg-zinc-700 transition shrink-0">
                      {item.icon}
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm font-semibold text-zinc-200 group-hover:text-white transition">
                        {item.label}
                      </div>
                      <div className="text-xs text-zinc-400 truncate mt-0.5">
                        {item.desc}
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {/* Official Knowledge Vault Catalogue Shortcut */}
              {onOpenCatalogue && (
                <button
                  onClick={onOpenCatalogue}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 text-xs font-semibold text-zinc-300 hover:text-white transition shadow-sm cursor-pointer"
                >
                  <BookOpen className="w-3.5 h-3.5 text-sky-400" />
                  <span>Buka Katalog 62 Dokumen Resmi & Regulasi Prodi</span>
                  <ChevronRight className="w-3.5 h-3.5 text-zinc-500" />
                </button>
              )}
            </div>
          ) : (
            messages.map((msg, idx) => {
              const isUser = msg.role === 'user';
              const timeString = msg.created_at
                ? new Date(msg.created_at).toLocaleTimeString('id-ID', {
                  hour: '2-digit',
                  minute: '2-digit',
                })
                : '';

              return isUser ? (
                /* User Message Row (Matching Image 8) */
                <div key={msg.id || idx} className="flex flex-col items-end gap-1.5 w-full">
                  <div className="flex items-start justify-end gap-3 max-w-[85%] sm:max-w-[75%]">
                    <div
                      onClick={handleContentClick}
                      className="bg-[#27272a] text-zinc-100 border border-zinc-700/50 rounded-2xl rounded-tr-sm px-4 py-3 text-sm sm:text-[15px] leading-relaxed shadow-sm break-words select-text prose-luco"
                      dangerouslySetInnerHTML={renderMarkdown(msg.content)}
                    />

                    {/* User Initials Avatar (Matching Image 8 MS) */}
                    <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 text-zinc-200 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 shadow-sm">
                      {getUserInitials()}
                    </div>
                  </div>
                  {timeString && (
                    <span className="text-[11px] text-zinc-500 pr-11 font-mono">
                      {timeString}
                    </span>
                  )}
                </div>
              ) : (
                /* Assistant Message Row (Matching Image 8) */
                <div key={msg.id || idx} className="flex flex-col items-start gap-1.5 w-full">
                  <div className="flex items-start gap-3 w-full">
                    {/* Bot Avatar: Official Luco Mascot */}
                    <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700/80 flex items-center justify-center shrink-0 mt-0.5 shadow-sm overflow-hidden p-0.5">
                      <img
                        src="/luco-logo.png"
                        alt="Luco"
                        className="w-full h-full object-contain"
                      />
                    </div>

                    <div className="flex-1 min-w-0 flex flex-col gap-3">
                      {/* Thought Accordion (Matching Image 8: > Thought for 4s) */}
                      {msg.trajectory && msg.trajectory.length > 0 && (
                        <div>
                          <button
                            onClick={() => toggleThought(msg.id)}
                            className="text-xs text-zinc-400 hover:text-zinc-200 inline-flex items-center gap-1.5 transition cursor-pointer py-1"
                          >
                            <span className="font-mono text-zinc-500">
                              {openThoughts[msg.id] ? '▾' : '▸'}
                            </span>
                            <span>
                              Thought for {msg.latency_s ? `${msg.latency_s.toFixed(1)}s` : `${msg.steps || 1}s`}
                            </span>
                          </button>

                          {openThoughts[msg.id] && (
                            <div className="mt-2 p-3.5 bg-[#141418] border border-zinc-800 rounded-xl flex flex-col gap-2 font-mono text-[11px] text-zinc-300">
                              {/* Step indicator (Matching Image 8: • query_metrics [DONE ⌵]) */}
                              <div className="flex items-center justify-between text-xs text-zinc-400 border-b border-zinc-800/80 pb-2">
                                <span className="flex items-center gap-2 text-zinc-300 font-medium">
                                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                                  openviking_retrieval
                                </span>
                                <span className="text-[10px] bg-zinc-800 px-2 py-0.5 rounded text-zinc-400 font-mono">
                                  DONE
                                </span>
                              </div>

                              {msg.trajectory.map((t: any, tIdx: number) => (
                                <div key={tIdx} className="p-2 rounded bg-zinc-900/60 border border-zinc-800/60">
                                  <div className="text-zinc-300 font-medium">
                                    Langkah {tIdx + 1}: [{t.tool || 'tool'}]
                                  </div>
                                  {t.input && (
                                    <div className="text-zinc-400 truncate mt-0.5">
                                      input: {JSON.stringify(t.input)}
                                    </div>
                                  )}
                                  {t.output && (
                                    <div className="text-emerald-400/90 truncate mt-0.5">
                                      output:{' '}
                                      {typeof t.output === 'string'
                                        ? t.output.slice(0, 160)
                                        : JSON.stringify(t.output).slice(0, 160)}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Markdown Response Text / Document Inspector */}
                      {(() => {
                        const parsedDoc = parseMarkdownDocument(msg.content);
                        const isRawMode = !!rawModeMap[msg.id];

                        if (parsedDoc.hasDocument) {
                          return (
                            <div className="flex flex-col gap-3 w-full">
                              {/* Intro text (jika bot menulis kalimat pengantar sebelum blok dokumen .md) */}
                              {parsedDoc.introText && (
                                <div
                                  onClick={handleContentClick}
                                  className="prose-luco text-zinc-200 text-sm sm:text-[15px] leading-relaxed select-text"
                                  dangerouslySetInnerHTML={renderMarkdown(parsedDoc.introText)}
                                />
                              )}

                              {/* Container Kartu Dokumen Markdown */}
                              <div className="rounded-2xl border border-zinc-800 bg-[#131318] overflow-hidden shadow-lg">
                                {/* Document Top Bar: Badge, Toggle Preview/Raw, & Copy Button */}
                                <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-[#181820] border-b border-zinc-800/80 text-xs select-none">
                                  <div className="flex items-center gap-2 text-zinc-300 font-medium">
                                    <FileText className="w-4 h-4 text-sky-400 shrink-0" />
                                    <span className="font-semibold text-zinc-200 text-xs">
                                      Dokumen Markdown (.md)
                                    </span>
                                  </div>

                                  <div className="flex items-center gap-2">
                                    {/* Toggle Mode: Render Preview vs Raw .md */}
                                    <div className="flex items-center bg-zinc-900/90 p-0.5 rounded-lg border border-zinc-700/60">
                                      <button
                                        type="button"
                                        onClick={() => setRawModeMap((prev) => ({ ...prev, [msg.id]: false }))}
                                        className={`px-3 py-1 rounded-md text-[11px] font-medium transition cursor-pointer flex items-center gap-1.5 ${
                                          !isRawMode
                                            ? 'bg-sky-500/20 text-sky-300 font-semibold shadow-xs'
                                            : 'text-zinc-400 hover:text-zinc-200'
                                        }`}
                                      >
                                        <Eye className="w-3.5 h-3.5" />
                                        <span>Render Preview</span>
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => setRawModeMap((prev) => ({ ...prev, [msg.id]: true }))}
                                        className={`px-3 py-1 rounded-md text-[11px] font-medium transition cursor-pointer flex items-center gap-1.5 ${
                                          isRawMode
                                            ? 'bg-zinc-800 text-white font-semibold shadow-xs'
                                            : 'text-zinc-400 hover:text-zinc-200'
                                        }`}
                                      >
                                        <Code2 className="w-3.5 h-3.5" />
                                        <span>Raw .md</span>
                                      </button>
                                    </div>

                                    {/* Salin Dokumen .md Button */}
                                    <button
                                      type="button"
                                      onClick={async () => {
                                        const ok = await copyTextToClipboard(parsedDoc.rawDocSource);
                                        if (ok) {
                                          setCopiedDocMap((prev) => ({ ...prev, [msg.id]: true }));
                                          showToast('Dokumen Markdown berhasil disalin ke clipboard!');
                                          setTimeout(
                                            () => setCopiedDocMap((prev) => ({ ...prev, [msg.id]: false })),
                                            2000
                                          );
                                        }
                                      }}
                                      className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white border border-zinc-700/60 text-[11px] font-medium transition cursor-pointer"
                                      title="Salin isi dokumen markdown mentah"
                                    >
                                      {copiedDocMap[msg.id] ? (
                                        <>
                                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                                          <span className="text-emerald-400 font-semibold">Tersalin</span>
                                        </>
                                      ) : (
                                        <>
                                          <Copy className="w-3.5 h-3.5 text-zinc-400" />
                                          <span>Salin .md</span>
                                        </>
                                      )}
                                    </button>
                                  </div>
                                </div>

                                {/* Document Body: Rendered HTML or Raw Preformatted Text */}
                                <div className="p-4 sm:p-6">
                                  {isRawMode ? (
                                    <pre className="p-4 rounded-xl bg-[#0b0b0e] border border-zinc-800/80 font-mono text-xs sm:text-sm text-zinc-300 overflow-x-auto whitespace-pre-wrap leading-relaxed select-text">
                                      {parsedDoc.rawDocSource}
                                    </pre>
                                  ) : (
                                    <div
                                      onClick={handleContentClick}
                                      className="prose-luco text-zinc-200 text-sm sm:text-[15px] leading-relaxed select-text"
                                      dangerouslySetInnerHTML={renderMarkdown(parsedDoc.docContent)}
                                    />
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        }

                        // Pesan asisten standar (bukan dokumen markdown khusus)
                        return (
                          <div
                            onClick={handleContentClick}
                            className="prose-luco text-zinc-200 text-sm sm:text-[15px] leading-relaxed select-text"
                            dangerouslySetInnerHTML={renderMarkdown(msg.content)}
                          />
                        );
                      })()}

                      {/* Active Clarification / Grill-me Interactive Card (Matching User Reference Image) */}
                      {msg.clarification && !dismissedClarifications[msg.id] && (
                        <div className="mt-3 bg-[#1e1e24] border border-zinc-800 rounded-2xl overflow-hidden shadow-2xl max-w-xl w-full animate-fade-in">
                          {/* Card Header with Title and Close 'X' */}
                          <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800/80 bg-zinc-900/70">
                            <span className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                              {msg.clarification.title || 'Kamu mau bimbingan soal apa?'}
                            </span>
                            <button
                              onClick={() => handleDismissClarification(msg.id)}
                              title="Tutup opsi"
                              className="text-zinc-400 hover:text-white p-1 rounded-md hover:bg-zinc-800 transition cursor-pointer"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>

                          {/* List of Numbered Clickable Options */}
                          <div className="flex flex-col divide-y divide-zinc-800/60">
                            {msg.clarification.options.map((opt: string, optIdx: number) => (
                              <button
                                key={optIdx}
                                onClick={() => handleSelectClarification(opt)}
                                className="w-full px-4 py-3 text-left hover:bg-zinc-800/60 active:bg-zinc-800 transition flex items-center gap-3.5 group cursor-pointer"
                              >
                                <span className="w-6 h-6 rounded-md bg-zinc-800 group-hover:bg-zinc-700 text-zinc-400 group-hover:text-white flex items-center justify-center text-xs font-mono font-semibold shrink-0 transition">
                                  {optIdx + 1}
                                </span>
                                <span className="text-sm text-zinc-300 group-hover:text-white font-medium transition leading-snug">
                                  {opt}
                                </span>
                              </button>
                            ))}
                          </div>

                          {/* Card Footer with 'Something else' and 'Skip' */}
                          <div className="flex items-center justify-between px-4 py-2.5 bg-zinc-900/50 border-t border-zinc-800/80 text-xs text-zinc-400">
                            <button
                              onClick={() => handleCustomAnswer()}
                              className="flex items-center gap-1.5 text-zinc-400 hover:text-zinc-200 transition cursor-pointer font-medium"
                            >
                              <PenLine className="w-3.5 h-3.5" />
                              <span>Something else</span>
                            </button>
                            <button
                              onClick={() => handleDismissClarification(msg.id)}
                              className="px-3.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white font-medium transition cursor-pointer"
                            >
                              Skip
                            </button>
                          </div>
                        </div>
                      )}

                      {/* SOURCES Pill Bar (Matching Image 8) */}
                      {msg.citations && msg.citations.length > 0 && (() => {
                        // Deduplikasi citations agar dokumen yang sama tidak muncul berulang
                        const seenTargets = new Set<string>();
                        const uniqueCitations = msg.citations.filter((c: any) => {
                          const rawTarget = typeof c === 'object' ? (c.target || c.url || c.file || c.path || '') : (typeof c === 'string' ? c : '');
                          const rawText = typeof c === 'object' ? (c.text || c.title || c.name || '') : '';
                          const key = (rawTarget || rawText).trim().toLowerCase();
                          if (!key || seenTargets.has(key)) return false;
                          seenTargets.add(key);
                          return true;
                        });

                        if (uniqueCitations.length === 0) return null;

                        return (
                          <div className="pt-2 flex flex-wrap items-center gap-2 text-xs">
                            <span className="font-bold text-[11px] text-zinc-400 uppercase tracking-wider mr-1">
                              SOURCES
                            </span>
                            {uniqueCitations.map((c: any, cIdx: number) => {
                              const rawTarget =
                                typeof c === 'object'
                                  ? c.target || c.url || c.file || c.path || ''
                                  : typeof c === 'string'
                                    ? c
                                    : '';
                              const rawText =
                                typeof c === 'object'
                                  ? c.text || c.title || c.name || ''
                                  : typeof c === 'string'
                                    ? c
                                    : '';

                              // Bersihkan path untuk display title jika text tidak spesifik
                              const fallbackTitle = rawTarget
                                ? rawTarget
                                  .split('/')
                                  .pop()
                                  ?.replace(/\.md$/i, '')
                                  .replace(/[-_]/g, ' ')
                                  .replace(/\b\w/g, (l: string) => l.toUpperCase())
                                : `Dokumen Resmi ${cIdx + 1}`;

                              const isGeneric = (t: string) => {
                                const low = t.trim().toLowerCase();
                                return !low || low === 'url' || low === 'target' || low === 'pedoman resmi' || low === 'dokumen resmi';
                              };

                              const title = !isGeneric(rawText)
                                ? rawText
                                : (fallbackTitle && !isGeneric(fallbackTitle) ? fallbackTitle : `Dokumen Resmi ${cIdx + 1}`);

                              const path = rawTarget || (title !== 'Dokumen Resmi' ? title : 'kp-ta/panduan-ta.md');

                              const handlePillClick = () => {
                                if (path.startsWith('http://') || path.startsWith('https://')) {
                                  if (!path.includes('uas-ai.ragilamirzaky.com') && !path.includes('.md')) {
                                    window.open(path, '_blank', 'noopener,noreferrer');
                                    return;
                                  }
                                }
                                onOpenDocument(path, title);
                              };

                              return (
                                <button
                                  key={cIdx}
                                  onClick={handlePillClick}
                                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white border border-zinc-700/60 text-xs transition cursor-pointer shadow-xs active:scale-98"
                                >
                                  <span className="w-4 h-4 rounded-full bg-zinc-700 text-zinc-200 flex items-center justify-center text-[10px] font-bold">
                                    {cIdx + 1}
                                  </span>
                                  <span className="truncate max-w-[200px] sm:max-w-[240px]">
                                    {title}
                                  </span>
                                </button>
                              );
                            })}
                          </div>
                        );
                      })()}

                      {/* Meta Footer (Time, Tokens, Feedback, Copy) */}
                      {(() => {
                        const currentFeedback =
                          feedbackState[msg.id] !== undefined
                            ? feedbackState[msg.id]
                            : msg.feedback || 'none';
                        return (
                          <div className="flex items-center justify-between text-xs text-zinc-400 pt-1">
                            <div className="flex items-center gap-2.5">
                              {timeString && <span>{timeString}</span>}
                              {msg.total_tokens ? (
                                <span>• {msg.total_tokens} tokens ({msg.prompt_tokens || 0} in / {msg.completion_tokens || 0} out)</span>
                              ) : null}
                            </div>

                            <div className="flex items-center gap-1">
                              {/* Like Button */}
                              <button
                                type="button"
                                onClick={() => handleFeedback(msg.id, 'like')}
                                title={currentFeedback === 'like' ? 'Batal like' : 'Suka respon ini (Data Riset)'}
                                className={`p-1.5 rounded-lg transition cursor-pointer flex items-center gap-1 ${
                                  currentFeedback === 'like'
                                    ? 'text-emerald-400 bg-emerald-500/15'
                                    : 'text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800'
                                }`}
                              >
                                <ThumbsUp className="w-3.5 h-3.5" />
                              </button>

                              {/* Dislike Button */}
                              <button
                                type="button"
                                onClick={() => handleFeedback(msg.id, 'dislike')}
                                title={currentFeedback === 'dislike' ? 'Batal dislike' : 'Tidak suka respon ini (Data Riset)'}
                                className={`p-1.5 rounded-lg transition cursor-pointer flex items-center gap-1 ${
                                  currentFeedback === 'dislike'
                                    ? 'text-rose-400 bg-rose-500/15'
                                    : 'text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800'
                                }`}
                              >
                                <ThumbsDown className="w-3.5 h-3.5" />
                              </button>

                              {/* Copy Button */}
                              <button
                                type="button"
                                onClick={() => handleCopy(msg.content, msg.id)}
                                title="Salin jawaban"
                                className="p-1.5 text-zinc-500 hover:text-zinc-200 rounded-lg hover:bg-zinc-800 transition cursor-pointer"
                              >
                                {copiedId === msg.id ? (
                                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                                ) : (
                                  <Copy className="w-3.5 h-3.5" />
                                )}
                              </button>
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                </div>
              );
            })
          )}

          {/* Loading Indicator */}
          {loading && (
            <div className="flex items-start gap-3 w-full animate-fade-in">
              <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700/80 flex items-center justify-center text-xs text-white shrink-0 mt-0.5 animate-pulse">
                <Sparkles className="w-4 h-4 text-zinc-300" />
              </div>
              <div className="py-1 text-xs text-zinc-400 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-zinc-400 animate-pulse"></span>
                <span className="w-2 h-2 rounded-full bg-zinc-400 animate-pulse [animation-delay:200ms]"></span>
                <span className="w-2 h-2 rounded-full bg-zinc-400 animate-pulse [animation-delay:400ms]"></span>
                <span className="text-zinc-400 font-mono text-xs pl-1">
                  Menelusuri vault OpenViking & data prodi...
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Floating Bottom Prompt Box (Matching Images 4, 5, 6, 7) */}
      <div className="p-4 sm:p-6 pt-2 pb-6 relative z-20 w-full bg-gradient-to-t from-[#0d0d10] via-[#0d0d10] to-transparent">
        <div className="max-w-3xl mx-auto w-full flex flex-col gap-2">
          {/* Kimi-style Action Toolbar when messages exist (Matching Reference Image) */}
          {messages.length > 0 && (
            <div className="flex items-center justify-between px-2.5 sm:px-3.5 py-1.5 rounded-xl bg-[#141418]/90 border border-zinc-800/80 text-xs text-zinc-300 shadow-md animate-fade-in backdrop-blur-sm gap-1 overflow-x-auto no-scrollbar">
              <div className="flex items-center gap-1.5 shrink-0">
                <span className="flex items-center gap-1.5 text-zinc-400 font-medium text-[11px] sm:text-xs whitespace-nowrap">
                  <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-emerald-400 shrink-0"></span>
                  {messages.length} pesan
                </span>
              </div>

              <div className="flex items-center gap-1 sm:gap-2 shrink-0">
                {/* Copy text */}
                <button
                  type="button"
                  onClick={handleCopyFullText}
                  title="Salin seluruh teks percakapan"
                  className="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-1 rounded-lg text-[11px] sm:text-xs text-zinc-300 hover:text-white hover:bg-zinc-800 transition cursor-pointer font-medium whitespace-nowrap shrink-0"
                >
                  {isTextCopied ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  ) : (
                    <Copy className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
                  )}
                  <span className="hidden sm:inline">{isTextCopied ? 'Tersalin' : 'Copy text'}</span>
                  <span className="sm:hidden">{isTextCopied ? 'Tersalin' : 'Salin'}</span>
                </button>

                {/* Copy link */}
                <button
                  type="button"
                  onClick={handleCopyShareLink}
                  title="Salin tautan obrolan"
                  className="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-1 rounded-lg text-[11px] sm:text-xs text-zinc-300 hover:text-white hover:bg-zinc-800 transition cursor-pointer font-medium whitespace-nowrap shrink-0"
                >
                  {isLinkCopied ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  ) : (
                    <Link className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
                  )}
                  <span className="hidden sm:inline">{isLinkCopied ? 'Tersalin' : 'Copy link'}</span>
                  <span className="sm:hidden">{isLinkCopied ? 'Tersalin' : 'Tautan'}</span>
                </button>

                {/* Generate document (.md) */}
                <button
                  type="button"
                  onClick={handleExportMarkdown}
                  title="Unduh percakapan sebagai dokumen Markdown (.md)"
                  className="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 rounded-lg text-[11px] sm:text-xs bg-zinc-800 hover:bg-zinc-700 text-sky-300 hover:text-sky-200 border border-zinc-700/80 transition cursor-pointer font-semibold shadow-sm whitespace-nowrap shrink-0"
                >
                  <FileDown className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                  <span className="hidden sm:inline">Generate document (.md)</span>
                  <span className="sm:hidden">Ekspor .md</span>
                </button>
              </div>
            </div>
          )}

          {/* Queued Messages Box (Matching User Image Reference) */}
          {queuedMessages.length > 0 && (
            <div className="w-full rounded-2xl bg-[#16161d] border border-zinc-800 shadow-xl overflow-hidden transition-all duration-200 animate-fade-in">
              {/* Header Queued Messages */}
              <div className="flex items-center justify-between px-3.5 py-2 bg-zinc-900/90 border-b border-zinc-800/80 text-xs">
                <div className="flex items-center gap-2 text-zinc-200 font-semibold">
                  <span>Queued Messages</span>
                  <span className="w-5 h-5 rounded-full bg-sky-500/20 text-sky-400 font-mono text-[11px] font-bold flex items-center justify-center">
                    {queuedMessages.length}
                  </span>
                  <span className="text-zinc-500 font-normal text-[11px] hidden sm:inline">
                    • Sends after agent finishes working
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setIsQueueCollapsed(!isQueueCollapsed)}
                  title={isQueueCollapsed ? 'Buka rincian antrean' : 'Tutup rincian antrean'}
                  className="text-zinc-400 hover:text-white p-1 rounded-md hover:bg-zinc-800 transition cursor-pointer"
                >
                  <ChevronDown
                    className={`w-3.5 h-3.5 transition-transform duration-200 ${
                      isQueueCollapsed ? 'rotate-180' : ''
                    }`}
                  />
                </button>
              </div>

              {/* List Item Antrean */}
              {!isQueueCollapsed && (
                <div className="divide-y divide-zinc-800/60 max-h-48 overflow-y-auto scrollbar-thin">
                  {queuedMessages.map((item, qIdx) => (
                    <div
                      key={item.id}
                      className="p-3 flex items-start justify-between gap-3 text-xs bg-zinc-900/40 hover:bg-zinc-800/40 transition"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-zinc-200 line-clamp-2 text-xs leading-relaxed font-normal">
                          {item.content}
                        </p>
                        <div className="flex items-center gap-2 mt-1.5 text-[10px] text-zinc-500 font-mono">
                          <span>Antrean #{qIdx + 1}</span>
                          <span>• Mode: {item.mode}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-1 shrink-0 pt-0.5">
                        {/* Kirim Sekarang (Intersep) */}
                        <button
                          type="button"
                          onClick={() => handleSendQueueNowItem(item.id)}
                          title="Kirim pesan ini sekarang (intersep respons saat ini)"
                          className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer"
                        >
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>

                        {/* Edit Pesan */}
                        <button
                          type="button"
                          onClick={() => handleEditQueuedItem(item.id)}
                          title="Edit pesan (masukkan kembali ke kolom chat)"
                          className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>

                        {/* Hapus dari Antrean */}
                        <button
                          type="button"
                          onClick={() => handleRemoveQueuedItem(item.id)}
                          title="Hapus dari antrean"
                          className="p-1.5 rounded-lg text-zinc-400 hover:text-rose-400 hover:bg-zinc-800 transition cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <form
            onSubmit={handleSubmit}
            className="rounded-2xl bg-[#18181c] border border-zinc-800 focus-within:border-zinc-600 p-3.5 sm:p-4 shadow-2xl transition duration-200 flex flex-col gap-3 relative"
          >
            {/* Header Mode Toggle saat input berisi teks (Tulis vs Render Preview) */}
            {input.trim() && (
              <div className="flex items-center justify-between pb-1.5 border-b border-zinc-800/80 text-[11px] animate-fade-in select-none">
                <span className="text-zinc-400 font-medium flex items-center gap-1.5">
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      inputViewMode === 'write' ? 'bg-sky-400' : 'bg-emerald-400'
                    }`}
                  />
                  <span>
                    {inputViewMode === 'write'
                      ? hasMarkdownInInput
                        ? 'Markdown terdeteksi • Tekan "Render" untuk pratinjau'
                        : 'Mode Penulisan'
                      : 'Pratinjau Markdown Ter-render (Klik untuk edit)'}
                  </span>
                </span>

                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => setIsExpanded((prev) => !prev)}
                    title={isExpanded ? 'Perkecil kolom chat' : 'Perbesar / Resize kolom chat'}
                    className="p-1 rounded-md text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer flex items-center gap-1 text-[11px]"
                  >
                    {isExpanded ? (
                      <>
                        <Minimize2 className="w-3 h-3 text-sky-400" />
                        <span className="text-[10px] hidden sm:inline text-sky-300">Kecilkan</span>
                      </>
                    ) : (
                      <>
                        <Maximize2 className="w-3 h-3" />
                        <span className="text-[10px] hidden sm:inline">Perbesar</span>
                      </>
                    )}
                  </button>

                  <div className="flex items-center bg-zinc-900/90 p-0.5 rounded-lg border border-zinc-700/60 shadow-xs">
                    <button
                      type="button"
                      onClick={() => {
                        setInputViewMode('write');
                        setTimeout(() => textareaRef.current?.focus(), 50);
                      }}
                      className={`px-2.5 py-0.5 rounded-md text-[11px] font-medium transition cursor-pointer flex items-center gap-1 ${
                        inputViewMode === 'write'
                          ? 'bg-zinc-800 text-white font-semibold shadow-xs'
                          : 'text-zinc-400 hover:text-zinc-200'
                      }`}
                    >
                      <Pencil className="w-3 h-3" />
                      <span>Tulis</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setInputViewMode('preview')}
                      className={`px-2.5 py-0.5 rounded-md text-[11px] font-medium transition cursor-pointer flex items-center gap-1 ${
                        inputViewMode === 'preview'
                          ? 'bg-sky-500/20 text-sky-300 font-semibold shadow-xs'
                          : 'text-zinc-400 hover:text-zinc-200'
                      }`}
                    >
                      <Eye className="w-3 h-3" />
                      <span>Render Preview</span>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Area Input: Textarea (Tulis) vs Rendered HTML (Pratinjau) */}
            {inputViewMode === 'write' ? (
              <textarea
                ref={textareaRef}
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything seputar Informatika UNTAN..."
                className={`w-full bg-transparent border-0 outline-none resize-y text-sm sm:text-base text-zinc-100 placeholder-zinc-500 leading-relaxed font-sans scrollbar-thin transition-[height] duration-150 ${
                  isExpanded ? 'min-h-[340px] max-h-[600px]' : 'min-h-[64px] max-h-[500px]'
                }`}
              />
            ) : (
              <div
                onClick={() => {
                  setInputViewMode('write');
                  setTimeout(() => textareaRef.current?.focus(), 50);
                }}
                title="Klik untuk kembali mengedit pesan"
                className={`w-full overflow-y-auto p-3.5 rounded-xl bg-[#121216] border border-zinc-700/50 prose-luco text-sm sm:text-[15px] leading-relaxed cursor-text select-text hover:border-zinc-600 transition ${
                  isExpanded ? 'min-h-[340px] max-h-[500px]' : 'min-h-[90px] max-h-[360px]'
                }`}
                dangerouslySetInnerHTML={renderMarkdown(input)}
              />
            )}

            {/* Bottom Toolbar Row inside Box (Matching Images 4, 7) */}
            <div className="flex items-center justify-between pt-1">
              {/* Left: Interactive Model / Mode Switcher */}
              <div className="flex items-center gap-2" ref={modeMenuRef}>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setIsModeMenuOpen(!isModeMenuOpen)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-zinc-800/90 hover:bg-zinc-700/80 border border-zinc-700/60 text-xs text-zinc-200 font-medium transition cursor-pointer select-none"
                  >
                    <span className="flex items-center justify-center shrink-0">
                      {INFERENCE_MODES.find((m) => m.id === selectedMode)?.icon || (
                        <Layers className="w-4 h-4 text-sky-400 shrink-0" />
                      )}
                    </span>
                    <span>
                      {INFERENCE_MODES.find((m) => m.id === selectedMode)?.short || 'IndoBERT + Viking'}
                    </span>
                    <ChevronDown
                      className={`w-3.5 h-3.5 text-zinc-400 transition-transform duration-200 ${isModeMenuOpen ? 'rotate-180' : ''
                        }`}
                    />
                  </button>

                  {/* Mode Switcher Dropdown Menu */}
                  {isModeMenuOpen && (
                    <div className="absolute bottom-full left-0 mb-2 w-72 sm:w-80 rounded-2xl bg-[#18181c] border border-zinc-700/80 shadow-2xl p-2 z-50 flex flex-col gap-1.5">
                      <div className="px-2.5 pt-1.5 pb-1 text-[10px] font-bold text-zinc-500 uppercase tracking-wider flex items-center justify-between">
                        <span>Pilih Mode Inferensi</span>
                        <span className="text-[10px] text-zinc-500 font-normal">Luco Engine</span>
                      </div>

                      {INFERENCE_MODES.map((m) => {
                        const isActive = selectedMode === m.id;
                        return (
                          <button
                            key={m.id}
                            type="button"
                            onClick={() => {
                              setSelectedMode(m.id);
                              setIsModeMenuOpen(false);
                            }}
                            className={`w-full text-left p-2.5 rounded-xl text-xs transition flex items-start gap-2.5 cursor-pointer ${isActive
                                ? 'bg-zinc-800 text-white font-medium border border-zinc-600/80 shadow-sm'
                                : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200 border border-transparent'
                              }`}
                          >
                            <span className="mt-0.5 flex items-center justify-center shrink-0">{m.icon}</span>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between gap-1">
                                <span className="text-xs font-semibold text-zinc-100">{m.name}</span>
                                {m.badge && (
                                  <span
                                    className={`text-[9px] px-1.5 py-0.5 rounded-full font-semibold shrink-0 ${m.id === 'viking_indobert'
                                        ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                                        : 'bg-zinc-700/50 text-zinc-300 border border-zinc-600/50'
                                      }`}
                                  >
                                    {m.badge}
                                  </span>
                                )}
                              </div>
                              <p className="text-[11px] text-zinc-400 mt-0.5 leading-snug">
                                {m.desc}
                              </p>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Right: Expand Button, Counter & Submit Button */}
              <div className="flex items-center gap-2 sm:gap-3">
                <button
                  type="button"
                  onClick={() => setIsExpanded((prev) => !prev)}
                  title={isExpanded ? 'Perkecil area chat' : 'Perbesar area chat (Resize)'}
                  className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer"
                >
                  {isExpanded ? (
                    <Minimize2 className="w-3.5 h-3.5 text-sky-400" />
                  ) : (
                    <Maximize2 className="w-3.5 h-3.5" />
                  )}
                </button>

                <span className="text-xs text-zinc-500 font-mono">
                  {input.length}/2000
                </span>

                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="w-8 h-8 rounded-full bg-white hover:bg-zinc-200 text-zinc-950 flex items-center justify-center font-bold disabled:opacity-20 transition shadow-sm cursor-pointer active:scale-95"
                  title={loading ? 'Masukkan ke antrean pesan' : 'Kirim pesan'}
                >
                  <ArrowUp className="w-4 h-4 stroke-[2.5]" />
                </button>
              </div>
            </div>
          </form>

          <p className="text-center text-xs text-zinc-500">
            Luco Asisten Informatika UNTAN • Rujukan Resmi dari Dokumen Akademik Jurusan
          </p>
        </div>
      </div>

      {/* Toast Notification for Copy / Export confirmation */}
      {toastMessage && (
        <div className="fixed bottom-28 left-1/2 -translate-x-1/2 z-50 px-4 py-2.5 rounded-2xl bg-zinc-900/95 border border-zinc-700/80 text-zinc-100 text-xs font-semibold shadow-2xl flex items-center gap-2.5 animate-fade-in backdrop-blur-md">
          <Check className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
};
