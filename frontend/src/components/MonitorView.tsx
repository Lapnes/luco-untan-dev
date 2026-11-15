import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  MonitoringSummary,
  AuditLogItem,
  AuditToolCall,
  fetchMonitoringSummary,
  fetchMonitoringLogs,
  downloadMonitoringCsv,
} from '../api';
import {
  BarChart3,
  RefreshCw,
  Download,
  ArrowLeft,
  Search,
  CheckCircle,
  XCircle,
  Clock,
  Layers,
  Coins,
  Cpu,
  ChevronDown,
  Filter,
  X,
  FileText,
  Terminal,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Check,
  Activity,
  Timer,
  ChevronRight,
  ChevronLeft,
  Calendar,
  Info,
  ExternalLink,
} from 'lucide-react';
import { TelemetryTimeSeriesChart } from './TelemetryTimeSeriesChart';

interface MonitorViewProps {
  onClose: () => void;
}

const toDateInputValue = (d: Date): string => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
};

const MONTH_NAMES = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
];

const WEEKDAY_NAMES = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab'];

export const MonitorView: React.FC<MonitorViewProps> = ({ onClose }) => {
  const [summary, setSummary] = useState<MonitoringSummary | null>(null);
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [totalRecords, setTotalRecords] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [search, setSearch] = useState('');
  const [modelFilter, setModelFilter] = useState<string>('all');
  const [selectedLog, setSelectedLog] = useState<AuditLogItem | null>(null);

  // DateTime Range Picker State
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const [selectedRange, setSelectedRange] = useState<{
    startIso?: string;
    endIso?: string;
    label: string;
    preset: string;
  }>({
    startIso: undefined,
    endIso: undefined,
    label: 'Semua Waktu',
    preset: 'all',
  });

  // Draft state di dalam Popover (sebelum di-apply)
  const [draftPreset, setDraftPreset] = useState<string>('all');
  const [draftStartDate, setDraftStartDate] = useState<string>(toDateInputValue(new Date()));
  const [draftStartTime, setDraftStartTime] = useState<string>('00:00');
  const [draftEndDate, setDraftEndDate] = useState<string>(toDateInputValue(new Date()));
  const [draftEndTime, setDraftEndTime] = useState<string>('23:59');
  const [calendarYear, setCalendarYear] = useState<number>(new Date().getFullYear());
  const [calendarMonth, setCalendarMonth] = useState<number>(new Date().getMonth());
  const pickerRef = useRef<HTMLDivElement>(null);

  const loadData = async (
    modelToFetch: string = modelFilter,
    startIso?: string,
    endIso?: string
  ) => {
    setLoading(true);
    try {
      const effectiveStart = startIso !== undefined ? startIso : selectedRange.startIso;
      const effectiveEnd = endIso !== undefined ? endIso : selectedRange.endIso;
      const [sumData, logsResp] = await Promise.all([
        fetchMonitoringSummary(
          modelToFetch === 'all' ? undefined : modelToFetch,
          effectiveStart,
          effectiveEnd
        ).catch(() => null),
        fetchMonitoringLogs(
          1000,
          0,
          modelToFetch === 'all' ? undefined : modelToFetch,
          effectiveStart,
          effectiveEnd
        ).catch(() => ({ total: 0, offset: 0, limit: 1000, logs: [] })),
      ]);
      if (sumData) setSummary(sumData);
      setLogs(logsResp.logs || []);
      setTotalRecords(logsResp.total ?? (logsResp.logs ? logsResp.logs.length : 0));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(modelFilter, selectedRange.startIso, selectedRange.endIso);
  }, [modelFilter]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(
      () => loadData(modelFilter, selectedRange.startIso, selectedRange.endIso),
      4000
    );
    return () => clearInterval(interval);
  }, [autoRefresh, modelFilter, selectedRange]);

  // Click outside listener untuk menutup Popover
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
        setIsPickerOpen(false);
      }
    };
    if (isPickerOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isPickerOpen]);

  // Navigasi Bulan Kalender
  const handlePrevMonth = () => {
    if (calendarMonth === 0) {
      setCalendarMonth(11);
      setCalendarYear((y) => y - 1);
    } else {
      setCalendarMonth((m) => m - 1);
    }
  };

  const handleNextMonth = () => {
    if (calendarMonth === 11) {
      setCalendarMonth(0);
      setCalendarYear((y) => y + 1);
    } else {
      setCalendarMonth((m) => m + 1);
    }
  };

  const handleCalendarDayClick = (dateStr: string) => {
    setDraftPreset('custom');
    if (!draftStartDate || (draftStartDate && draftEndDate && draftStartDate !== draftEndDate)) {
      setDraftStartDate(dateStr);
      setDraftEndDate(dateStr);
    } else {
      if (dateStr < draftStartDate) {
        setDraftEndDate(draftStartDate);
        setDraftStartDate(dateStr);
      } else {
        setDraftEndDate(dateStr);
      }
    }
  };

  const handleSelectPreset = (presetId: string) => {
    setDraftPreset(presetId);
    const now = new Date();
    const todayStr = toDateInputValue(now);

    if (presetId === 'today') {
      setDraftStartDate(todayStr);
      setDraftStartTime('00:00');
      setDraftEndDate(todayStr);
      setDraftEndTime('23:59');
    } else if (presetId === 'yesterday') {
      const yest = new Date(now.getTime() - 24 * 3600 * 1000);
      const yestStr = toDateInputValue(yest);
      setDraftStartDate(yestStr);
      setDraftStartTime('00:00');
      setDraftEndDate(yestStr);
      setDraftEndTime('23:59');
    } else if (presetId === '24h') {
      const dayAgo = new Date(now.getTime() - 24 * 3600 * 1000);
      setDraftStartDate(toDateInputValue(dayAgo));
      setDraftStartTime(
        `${String(dayAgo.getHours()).padStart(2, '0')}:${String(dayAgo.getMinutes()).padStart(2, '0')}`
      );
      setDraftEndDate(todayStr);
      setDraftEndTime(
        `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
      );
    } else if (presetId === '7d') {
      const weekAgo = new Date(now.getTime() - 7 * 24 * 3600 * 1000);
      setDraftStartDate(toDateInputValue(weekAgo));
      setDraftStartTime('00:00');
      setDraftEndDate(todayStr);
      setDraftEndTime('23:59');
    } else if (presetId === '30d') {
      const monthAgo = new Date(now.getTime() - 30 * 24 * 3600 * 1000);
      setDraftStartDate(toDateInputValue(monthAgo));
      setDraftStartTime('00:00');
      setDraftEndDate(todayStr);
      setDraftEndTime('23:59');
    } else if (presetId === 'all') {
      setDraftStartDate(todayStr);
      setDraftStartTime('00:00');
      setDraftEndDate(todayStr);
      setDraftEndTime('23:59');
    }
  };

  const handleApplyDateRange = () => {
    setIsPickerOpen(false);
    if (draftPreset === 'all') {
      const newRange = {
        startIso: undefined,
        endIso: undefined,
        label: 'Semua Waktu',
        preset: 'all',
      };
      setSelectedRange(newRange);
      loadData(modelFilter, undefined, undefined);
      return;
    }

    const startDateObj = new Date(`${draftStartDate}T${draftStartTime}:00`);
    const endDateObj = new Date(`${draftEndDate}T${draftEndTime}:59`);
    const startIso = isNaN(startDateObj.getTime())
      ? `${draftStartDate}T${draftStartTime}:00Z`
      : startDateObj.toISOString();
    const endIso = isNaN(endDateObj.getTime())
      ? `${draftEndDate}T${draftEndTime}:59Z`
      : endDateObj.toISOString();
    let label = `${draftStartDate} ${draftStartTime} → ${draftEndDate} ${draftEndTime}`;
    if (draftPreset === 'today') label = `Hari Ini (${draftStartTime} - ${draftEndTime})`;
    else if (draftPreset === 'yesterday') label = `Kemarin`;
    else if (draftPreset === '24h') label = `24 Jam Terakhir`;
    else if (draftPreset === '7d') label = `7 Hari Terakhir`;
    else if (draftPreset === '30d') label = `30 Hari Terakhir`;

    const newRange = {
      startIso,
      endIso,
      label,
      preset: draftPreset,
    };
    setSelectedRange(newRange);
    loadData(modelFilter, startIso, endIso);
  };

  const renderCalendarDays = () => {
    const firstDay = new Date(calendarYear, calendarMonth, 1).getDay();
    const daysInMonth = new Date(calendarYear, calendarMonth + 1, 0).getDate();
    const prevMonthDays = new Date(calendarYear, calendarMonth, 0).getDate();

    const cells = [];

    // Hari dari bulan sebelumnya
    for (let i = firstDay - 1; i >= 0; i--) {
      cells.push(
        <div key={`prev-${i}`} className="py-1.5 text-zinc-600 text-xs select-none">
          {prevMonthDays - i}
        </div>
      );
    }

    // Hari dalam bulan aktif
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${calendarYear}-${String(calendarMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const isStart = draftStartDate === dateStr;
      const isEnd = draftEndDate === dateStr;
      const isBetween =
        draftStartDate &&
        draftEndDate &&
        dateStr > draftStartDate &&
        dateStr < draftEndDate;

      let cellStyle = 'hover:bg-zinc-800 text-zinc-300 rounded-lg';
      if (isStart && isEnd) {
        cellStyle = 'bg-sky-500 text-white font-bold rounded-lg shadow-sm';
      } else if (isStart) {
        cellStyle = 'bg-sky-500 text-white font-bold rounded-l-lg shadow-sm';
      } else if (isEnd) {
        cellStyle = 'bg-sky-500 text-white font-bold rounded-r-lg shadow-sm';
      } else if (isBetween) {
        cellStyle = 'bg-sky-500/20 text-sky-200';
      }

      cells.push(
        <button
          key={`day-${day}`}
          type="button"
          onClick={() => handleCalendarDayClick(dateStr)}
          className={`py-1.5 text-xs transition cursor-pointer select-none ${cellStyle}`}
        >
          {day}
        </button>
      );
    }

    return cells;
  };

  const filteredLogs = useMemo(() => {
    return logs.filter((l) => {
      const q = search.toLowerCase();
      const matchesSearch =
        !q ||
        (l.question && l.question.toLowerCase().includes(q)) ||
        (l.model && l.model.toLowerCase().includes(q)) ||
        (l.user_email && l.user_email.toLowerCase().includes(q));
      const matchesModel =
        modelFilter === 'all' || (l.model && l.model.toLowerCase().includes(modelFilter.toLowerCase()));
      return matchesSearch && matchesModel;
    });
  }, [logs, search, modelFilter]);

  // Hitung agregat token & metrics
  const totalInputTokens =
    summary?.total_prompt_tokens || filteredLogs.reduce((acc, l) => acc + (l.prompt_tokens || 0), 0);
  const totalOutputTokens =
    summary?.total_completion_tokens || filteredLogs.reduce((acc, l) => acc + (l.completion_tokens || 0), 0);
  const totalTokens = summary?.total_tokens || totalInputTokens + totalOutputTokens;

  return (
    <div className="flex-1 overflow-y-auto h-full bg-[#0e0e11] text-zinc-100 p-4 sm:p-7 space-y-6 select-text scrollbar-thin">
      {/* Top Header & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div className="flex items-center gap-3.5">
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white transition border border-zinc-800 flex items-center gap-1.5 text-xs font-medium cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">Kembali ke Chat</span>
          </button>

          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              AI Agents Model Details & Audit Telemetry
            </h1>
            <p className="text-xs text-zinc-400 mt-0.5">
              Inspeksi komprehensif: prompt LLM, trajectory skill/tool, file & baris yang diakses, durasi waterfall, dan reaksi feedback
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <label className="flex items-center gap-2 text-xs text-zinc-400 bg-zinc-900 px-3 py-2 rounded-xl border border-zinc-800 cursor-pointer hover:text-white transition">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="accent-blue-500 rounded"
            />
            <span>Auto Refresh (4s)</span>
          </label>

          <button
            onClick={() => loadData(modelFilter, selectedRange.startIso, selectedRange.endIso)}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-xs font-medium text-zinc-300 border border-zinc-800 transition cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Perbarui</span>
          </button>

          <button
            type="button"
            onClick={async () => {
              try {
                await downloadMonitoringCsv(
                  modelFilter === 'all' ? undefined : modelFilter,
                  selectedRange.startIso,
                  selectedRange.endIso
                );
              } catch (err) {
                alert('Gagal mengekspor CSV: ' + err);
              }
            }}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-zinc-200 text-zinc-950 text-xs font-semibold shadow-sm transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Ekspor CSV</span>
          </button>
        </div>
      </div>

      {/* Filter Bar with DateTime Range Popover & Dynamic Model Selector */}
      <div className="flex flex-wrap items-center gap-3 text-xs relative z-30">
        {/* Trigger Button DateTime Range Popover */}
        <div className="relative" ref={pickerRef}>
          <button
            type="button"
            onClick={() => setIsPickerOpen(!isPickerOpen)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl border text-xs font-medium transition cursor-pointer shadow-xs ${
              isPickerOpen
                ? 'bg-[#181820] border-sky-500/80 text-white ring-2 ring-sky-500/20'
                : 'bg-[#141419] hover:bg-[#191922] border-zinc-800 text-zinc-200'
            }`}
          >
            <Calendar className="w-4 h-4 text-sky-400 shrink-0" />
            <span className="font-semibold text-zinc-200">{selectedRange.label}</span>
            <ChevronDown
              className={`w-3.5 h-3.5 text-zinc-400 transition-transform duration-200 ${
                isPickerOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          {/* DateTime Picker Popover Dropdown (Matching Reference Images) */}
          {isPickerOpen && (
            <div className="absolute left-0 top-full mt-2 w-[340px] sm:w-[580px] bg-[#14141a] border border-zinc-700/80 rounded-2xl shadow-2xl p-4 sm:p-5 flex flex-col gap-4 animate-fade-in backdrop-blur-xl z-50">
              {/* Layout 2 Kolom: Kiri Presets, Kanan Kalender & Waktu */}
              <div className="flex flex-col sm:flex-row gap-4">
                {/* Kolom Kiri: Quick Presets */}
                <div className="sm:w-44 shrink-0 flex flex-col gap-1 border-b sm:border-b-0 sm:border-r border-zinc-800 pb-3 sm:pb-0 sm:pr-3">
                  <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider mb-1 px-2">
                    Rentang Waktu
                  </span>
                  {[
                    { id: '24h', label: '24 Jam Terakhir' },
                    { id: 'today', label: 'Hari Ini (Today)' },
                    { id: 'yesterday', label: 'Kemarin (Yesterday)' },
                    { id: '7d', label: '7 Hari Terakhir' },
                    { id: '30d', label: '30 Hari Terakhir' },
                    { id: 'all', label: 'Semua Waktu' },
                    { id: 'custom', label: 'Kustom Tanggal' },
                  ].map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => handleSelectPreset(p.id)}
                      className={`w-full text-left px-3 py-2 rounded-xl text-xs font-medium transition cursor-pointer flex items-center justify-between ${
                        draftPreset === p.id
                          ? 'bg-sky-500/20 text-sky-300 font-semibold border border-sky-500/30'
                          : 'text-zinc-300 hover:text-white hover:bg-zinc-800/60'
                      }`}
                    >
                      <span>{p.label}</span>
                      {draftPreset === p.id && <Check className="w-3.5 h-3.5 text-sky-400" />}
                    </button>
                  ))}
                </div>

                {/* Kolom Kanan: Interactive Calendar & Time Slots */}
                <div className="flex-1 flex flex-col gap-3 min-w-0">
                  {/* Calendar Month Navigation */}
                  <div className="flex items-center justify-between px-1">
                    <button
                      type="button"
                      onClick={handlePrevMonth}
                      className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <span className="text-xs font-bold text-white tracking-wide">
                      {MONTH_NAMES[calendarMonth]} {calendarYear}
                    </span>
                    <button
                      type="button"
                      onClick={handleNextMonth}
                      className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Calendar Days Grid */}
                  <div className="grid grid-cols-7 gap-1 text-center text-xs">
                    {WEEKDAY_NAMES.map((wd, wIdx) => (
                      <span key={wd} className="text-[10px] font-semibold text-zinc-500 py-1">
                        {wd}
                      </span>
                    ))}
                    {renderCalendarDays()}
                  </div>

                  {/* Time Range Selectors (Dari Jam s/d Jam) */}
                  <div className="pt-2 border-t border-zinc-800/80 grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <label className="text-[10px] text-zinc-400 font-medium flex items-center gap-1 mb-1">
                        <Clock className="w-3 h-3 text-sky-400" />
                        <span>Jam Mulai</span>
                      </label>
                      <input
                        type="time"
                        value={draftStartTime}
                        onChange={(e) => {
                          setDraftStartTime(e.target.value);
                          setDraftPreset('custom');
                        }}
                        className="w-full bg-[#181820] border border-zinc-800 focus:border-sky-500/80 rounded-lg px-2.5 py-1.5 text-xs text-white outline-none font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-zinc-400 font-medium flex items-center gap-1 mb-1">
                        <Clock className="w-3 h-3 text-purple-400" />
                        <span>Jam Selesai</span>
                      </label>
                      <input
                        type="time"
                        value={draftEndTime}
                        onChange={(e) => {
                          setDraftEndTime(e.target.value);
                          setDraftPreset('custom');
                        }}
                        className="w-full bg-[#181820] border border-zinc-800 focus:border-sky-500/80 rounded-lg px-2.5 py-1.5 text-xs text-white outline-none font-mono"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Popover Footer: Summary & Action Buttons */}
              <div className="pt-3 border-t border-zinc-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                <div className="text-[11px] text-zinc-400 font-mono">
                  {draftPreset === 'all'
                    ? 'Rentang: Semua Rekam Jejak (All Time)'
                    : `${draftStartDate} ${draftStartTime} → ${draftEndDate} ${draftEndTime}`}
                </div>
                <div className="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setIsPickerOpen(false)}
                    className="px-3.5 py-1.5 rounded-xl text-xs text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer"
                  >
                    Batal
                  </button>
                  <button
                    type="button"
                    onClick={handleApplyDateRange}
                    className="px-4 py-1.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-zinc-950 font-bold text-xs transition cursor-pointer shadow-md"
                  >
                    Terapkan Filter
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Model Filter */}
        <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#141419] border border-zinc-800 text-zinc-300">
          <Cpu className="w-3.5 h-3.5 text-blue-400 shrink-0" />
          <span className="text-zinc-500 font-medium">Model:</span>
          <select
            value={modelFilter}
            onChange={(e) => setModelFilter(e.target.value)}
            className="bg-transparent outline-none cursor-pointer text-white font-medium ml-1 max-w-[240px] sm:max-w-md truncate"
          >
            <option value="all" className="bg-zinc-900">
              Semua Model (All) — {totalRecords || summary?.total_requests || filteredLogs.length} requests
            </option>
            {summary?.models?.map((m, idx) => (
              <option key={idx} value={m.model} className="bg-zinc-900">
                {m.model} ({m.requests} req • ${m.cost_usd.toFixed(4)})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 3 Core Analytics Cards with REAL EXPLAINED CHARTS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Model Cost Time Series Chart (Candlestick & Moving Average) */}
        <TelemetryTimeSeriesChart
          title="Model Cost (Biaya Inferensi)"
          subtitle={`Grafik fluktuasi biaya (${modelFilter === 'all' ? 'Semua Model' : modelFilter})`}
          icon={<Coins className="w-4 h-4 text-amber-400" />}
          metricType="cost"
          logs={filteredLogs}
          startIso={selectedRange.startIso}
          endIso={selectedRange.endIso}
          totalDisplay={`$${(summary?.total_cost_usd || 0).toFixed(4)}`}
          secondaryDisplay={`≈ Rp ${(summary?.total_cost_idr || 0).toLocaleString('id-ID', { minimumFractionDigits: 2 })}`}
          footerLeft={
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              {modelFilter === 'all' ? 'Semua Model / Proxy' : modelFilter}
            </span>
          }
          footerRight={
            <span className="text-zinc-400 text-[10px]">
              Lilin: <span className="text-emerald-400">🟢 Normal</span> • <span className="text-rose-400">🔴 Lonjakan</span> (Sumbu: Min-Max Req)
            </span>
          }
        />

        {/* Card 2: Tokens Used Time Series Chart (Candlestick & Moving Average) */}
        <TelemetryTimeSeriesChart
          title="Tokens Used (Input vs Output)"
          subtitle="Grafik 2 Kurva Input (Biru) & Output (Merah) dengan Lilin Stacked"
          icon={<Layers className="w-4 h-4 text-sky-400" />}
          metricType="tokens"
          logs={filteredLogs}
          startIso={selectedRange.startIso}
          endIso={selectedRange.endIso}
          totalDisplay={totalTokens.toLocaleString()}
          secondaryDisplay={`${totalTokens > 0 ? Math.round((totalInputTokens / totalTokens) * 100) : 0}% in • ${totalTokens > 0 ? Math.round((totalOutputTokens / totalTokens) * 100) : 0}% out`}
          footerLeft={
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 text-sky-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                Input: {totalInputTokens.toLocaleString()}
              </span>
              <span className="text-zinc-600">|</span>
              <span className="flex items-center gap-1.5 text-rose-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-rose-400"></span>
                Output: {totalOutputTokens.toLocaleString()}
              </span>
            </div>
          }
          footerRight={
            <span className="text-zinc-400 text-[10px]">
              Lilin: <span className="text-rose-400 font-medium">Bawah Output (Merah)</span> • <span className="text-sky-400 font-medium">Atas Input (Biru)</span>
            </span>
          }
        />

        {/* Card 3: Performance & Rejection Rate */}
        <div className="bg-[#141418] border border-zinc-800 rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs text-zinc-400 mb-1">
              <span className="font-semibold text-zinc-300">Performance & Rejection</span>
              <Clock className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">
              {summary?.avg_latency_s ? `${summary.avg_latency_s.toFixed(2)}s` : '0.00s'}
            </div>
            <div className="text-xs text-zinc-400 mt-0.5">
              Rata-rata kecepatan respons inferensi RAG
            </div>
          </div>

          {/* Token Types Stack Ratio Bar */}
          <div className="py-5 space-y-2">
            <div className="h-3 w-full rounded-full bg-zinc-800 flex overflow-hidden">
              <div
                style={{
                  width: `${totalTokens > 0 ? (totalInputTokens / totalTokens) * 100 : 70}%`,
                }}
                className="bg-sky-500 h-full"
                title="Input Tokens"
              />
              <div
                style={{
                  width: `${totalTokens > 0 ? (totalOutputTokens / totalTokens) * 100 : 30}%`,
                }}
                className="bg-rose-500 h-full"
                title="Output Tokens"
              />
            </div>

            <div className="flex items-center justify-between text-[11px] text-zinc-400">
              <span className="flex items-center gap-1 text-sky-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-sky-500"></span>
                Prompt (Input): {totalTokens > 0 ? Math.round((totalInputTokens / totalTokens) * 100) : 0}%
              </span>
              <span className="flex items-center gap-1 text-rose-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                Completion (Output): {totalTokens > 0 ? Math.round((totalOutputTokens / totalTokens) * 100) : 0}%
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between text-[11px] text-zinc-400 pt-2 border-t border-zinc-800/80">
            <span>Rejection Rate:</span>
            <span className="font-mono text-white font-medium">
              {summary?.rejection_rate_percent || 0}% ({summary?.total_rejected || 0} fast-redirect)
            </span>
          </div>
        </div>
      </div>

      {/* Models Telemetry Breakdown Table */}
      <div className="bg-[#141418] border border-zinc-800 rounded-2xl p-5 space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-blue-400" />
          <span>Models Telemetry Summary</span>
        </h3>

        <div className="overflow-x-auto rounded-xl border border-zinc-800/80">
          <table className="w-full text-xs text-left">
            <thead className="bg-[#18181d] text-zinc-400 border-b border-zinc-800">
              <tr>
                <th className="py-3 px-4 font-semibold">MODEL</th>
                <th className="py-3 px-3 font-semibold text-center">REQUESTS</th>
                <th className="py-3 px-3 font-semibold text-center">ERRORS / REJECT</th>
                <th className="py-3 px-3 font-semibold text-center">AVG LATENCY</th>
                <th className="py-3 px-3 font-semibold">COST</th>
                <th className="py-3 px-3 font-semibold">INPUT TOKENS</th>
                <th className="py-3 px-3 font-semibold">OUTPUT TOKENS</th>
                <th className="py-3 px-4 font-semibold">TOTAL TOKENS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 text-zinc-200">
              {summary && summary.models && summary.models.length > 0 ? (
                summary.models.map((m, idx) => (
                  <tr
                    key={idx}
                    onClick={() => setModelFilter(m.model)}
                    className="hover:bg-zinc-800/40 transition cursor-pointer"
                    title="Klik untuk memfilter audit log berdasarkan model ini"
                  >
                    <td className="py-3 px-4 font-mono font-medium text-white flex items-center gap-2">
                      <Cpu className="w-3.5 h-3.5 text-blue-400" />
                      <span>{m.model}</span>
                    </td>
                    <td className="py-3 px-3 text-center font-mono">{m.requests.toLocaleString()}</td>
                    <td className="py-3 px-3 text-center font-mono text-zinc-400">{m.errors || 0}</td>
                    <td className="py-3 px-3 text-center font-mono">
                      {m.avg_latency_s ? `${m.avg_latency_s.toFixed(2)}s` : `${summary.avg_latency_s.toFixed(2)}s`}
                    </td>
                    <td className="py-3 px-3 font-mono text-emerald-400 font-medium">
                      ${m.cost_usd.toFixed(4)}
                    </td>
                    <td className="py-3 px-3 font-mono text-blue-300">
                      {(m.prompt_tokens || Math.round(m.tokens * 0.65)).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 font-mono text-purple-300">
                      {(m.completion_tokens || Math.round(m.tokens * 0.35)).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-white">
                      {m.tokens.toLocaleString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-6 text-center text-zinc-500">
                    Belum ada data inferensi model.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Comprehensive Audit Logs Table (CLICKABLE FOR FULL INSPECTION) */}
      <div className="bg-[#141418] border border-zinc-800 rounded-2xl p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>
                Audit Telemetry Log ({filteredLogs.length} Records
                {totalRecords > filteredLogs.length ? ` • dari total ${totalRecords} di database` : ''})
              </span>
            </h3>
            <p className="text-xs text-zinc-400 mt-0.5">
              💡 <span className="text-zinc-300 font-medium">Klik baris manapun</span> untuk inspeksi detail: System Prompt, User Prompt, Trajectory Tool (File & Baris), Waterfall Latensi, dan Feedback.
            </p>
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cari pertanyaan, user email, model..."
              className="w-full bg-[#18181d] border border-zinc-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-600 transition"
            />
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-zinc-800/80">
          <table className="w-full text-xs text-left">
            <thead className="bg-[#18181d] text-zinc-400 border-b border-zinc-800">
              <tr>
                <th className="py-3 px-3">WAKTU</th>
                <th className="py-3 px-3">USER / EMAIL</th>
                <th className="py-3 px-3">MODEL</th>
                <th className="py-3 px-3 max-w-xs">PERTANYAAN</th>
                <th className="py-3 px-3 font-semibold text-blue-300">INPUT</th>
                <th className="py-3 px-3 font-semibold text-purple-300">OUTPUT</th>
                <th className="py-3 px-3 font-bold text-white">TOTAL</th>
                <th className="py-3 px-3">LATENSI</th>
                <th className="py-3 px-3">BIAYA</th>
                <th className="py-3 px-3 text-center">FEEDBACK</th>
                <th className="py-3 px-3 text-center">STATUS</th>
                <th className="py-3 px-3 text-center">INSPEKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={12} className="py-8 text-center text-zinc-500">
                    Tidak ditemukan rekaman log audit yang sesuai kriteria pencarian.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => {
                  const timeStr = log.created_at
                    ? new Date(log.created_at).toLocaleTimeString('id-ID', {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })
                    : '-';
                  return (
                    <tr
                      key={log.id}
                      onClick={() => setSelectedLog(log)}
                      className="hover:bg-zinc-800/60 transition cursor-pointer group"
                    >
                      <td className="py-2.5 px-3 font-mono text-[11px] text-zinc-400 whitespace-nowrap">
                        {timeStr}
                      </td>
                      <td className="py-2.5 px-3 whitespace-nowrap text-zinc-200">
                        {log.user_email || 'guest@untan'}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-zinc-400 whitespace-nowrap max-w-[140px] truncate" title={log.model}>
                        {log.model}
                      </td>
                      <td className="py-2.5 px-3 max-w-xs truncate text-white font-medium" title={log.question}>
                        {log.question}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-blue-300 font-medium">
                        {log.prompt_tokens?.toLocaleString() || '-'}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-purple-300 font-medium">
                        {log.completion_tokens?.toLocaleString() || '-'}
                      </td>
                      <td className="py-2.5 px-3 font-mono font-bold text-white">
                        {log.total_tokens?.toLocaleString() || '-'}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-zinc-300 whitespace-nowrap">
                        {log.latency_s ? `${log.latency_s.toFixed(2)}s` : '0.00s'}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-emerald-400 whitespace-nowrap">
                        Rp {log.estimated_cost_idr ? log.estimated_cost_idr.toFixed(2) : '0.00'}
                      </td>
                      <td className="py-2.5 px-3 text-center whitespace-nowrap">
                        {log.feedback === 'like' ? (
                          <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                            <ThumbsUp className="w-3 h-3" /> Like
                          </span>
                        ) : log.feedback === 'dislike' ? (
                          <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-medium">
                            <ThumbsDown className="w-3 h-3" /> Dislike
                          </span>
                        ) : (
                          <span className="text-zinc-600 font-mono text-[11px]">-</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-center whitespace-nowrap">
                        {log.rejected ? (
                          <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 font-medium">
                            <XCircle className="w-3 h-3" /> Redirect
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                            <CheckCircle className="w-3 h-3" /> Success
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-center whitespace-nowrap">
                        <span className="inline-flex items-center gap-1 text-xs text-blue-400 group-hover:text-blue-300 font-medium">
                          Detail <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition" />
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* INSPECTION MODAL: Full Detailed Breakdown requested by user */}
      {selectedLog && (
        <AuditDetailModal log={selectedLog} onClose={() => setSelectedLog(null)} />
      )}
    </div>
  );
};

interface AuditDetailModalProps {
  log: AuditLogItem;
  onClose: () => void;
}

const AuditDetailModal: React.FC<AuditDetailModalProps> = ({ log, onClose }) => {
  const [activeTab, setActiveTab] = useState<'trajectory' | 'timing' | 'prompts' | 'qa' | 'tokens'>('trajectory');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const timing = log.timing_breakdown;
  const toolCalls = log.tool_calls || timing?.tool_calls_breakdown || [];

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 animate-fade-in">
      <div className="bg-[#121216] border border-zinc-800 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden text-zinc-100">
        {/* Header */}
        <div className="px-5 py-4 border-b border-zinc-800 flex items-center justify-between bg-[#16161c]">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-bold text-white flex items-center gap-2">
                <Terminal className="w-4 h-4 text-indigo-400" />
                Audit Telemetry Inspector
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                ID: {log.id?.slice(0, 8)}...
              </span>
              {log.rejected ? (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 font-medium">
                  Redirect: {log.reason || 'FAST_REJECT'}
                </span>
              ) : (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  Success
                </span>
              )}
              {log.feedback && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium flex items-center gap-1 ${
                  log.feedback === 'like'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                }`}>
                  {log.feedback === 'like' ? <ThumbsUp className="w-2.5 h-2.5" /> : <ThumbsDown className="w-2.5 h-2.5" />}
                  User Feedback: {log.feedback}
                </span>
              )}
            </div>
            <div className="text-xs text-zinc-400 flex items-center gap-3">
              <span>Model: <span className="text-white font-mono">{log.model}</span></span>
              <span>Waktu: <span className="text-zinc-300 font-mono">{log.created_at ? new Date(log.created_at).toLocaleString('id-ID') : '-'}</span></span>
              <span>User: <span className="text-zinc-300">{log.user_email || 'guest@untan'}</span></span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-zinc-400 hover:text-white rounded-xl hover:bg-zinc-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="px-5 pt-3 pb-1 border-b border-zinc-800/80 bg-[#141418] flex items-center gap-2 overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab('trajectory')}
            className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer flex items-center gap-1.5 shrink-0 ${
              activeTab === 'trajectory'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Trajectory & Tools ({toolCalls.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('timing')}
            className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer flex items-center gap-1.5 shrink-0 ${
              activeTab === 'timing'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
            }`}
          >
            <Timer className="w-3.5 h-3.5" />
            <span>Waterfall Waktu Latensi</span>
          </button>

          <button
            onClick={() => setActiveTab('prompts')}
            className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer flex items-center gap-1.5 shrink-0 ${
              activeTab === 'prompts'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>System & User Prompt</span>
          </button>

          <button
            onClick={() => setActiveTab('qa')}
            className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer flex items-center gap-1.5 shrink-0 ${
              activeTab === 'qa'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Pertanyaan & Jawaban AI</span>
          </button>

          <button
            onClick={() => setActiveTab('tokens')}
            className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer flex items-center gap-1.5 shrink-0 ${
              activeTab === 'tokens'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
            }`}
          >
            <Coins className="w-3.5 h-3.5" />
            <span>Biaya & Token</span>
          </button>
        </div>

        {/* Tab Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 scrollbar-thin text-xs">
          {/* TAB 1: TRAJECTORY & TOOLS EXECUTION */}
          {activeTab === 'trajectory' && (
            <div className="space-y-4">
              <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-white">Rekam Jejak Eksekusi Tool (Agent Trajectory)</h4>
                  <p className="text-zinc-400 text-[11px] mt-0.5">
                    Alat yang dipanggil LLM, parameter yang dikirim, berkas & baris dokumen yang diakses, durasi eksekusi, dan cuplikan data mentah.
                  </p>
                </div>
                <div className="text-right font-mono">
                  <div className="text-sm font-bold text-indigo-400">{toolCalls.length} Langkah</div>
                  <div className="text-[10px] text-zinc-500">Total Tool Steps</div>
                </div>
              </div>

              {toolCalls.length === 0 ? (
                <div className="p-8 text-center bg-zinc-900/40 border border-zinc-800/80 rounded-xl text-zinc-400 space-y-1">
                  <Info className="w-6 h-6 mx-auto text-zinc-500" />
                  <p className="font-medium text-zinc-300">Tidak ada pemanggilan tool pada request ini.</p>
                  <p className="text-[11px]">Request ditangani lewat Direct LLM atau Fast Router Redirection.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {toolCalls.map((tc: any, idx: number) => {
                    const stepNum = tc.step || tc.call_index || idx + 1;
                    const toolName = tc.tool || 'unknown_tool';
                    const argsStr = JSON.stringify(tc.args || tc.input || {}, null, 2);
                    const files: string[] = tc.files_accessed || [];
                    const lines = tc.lines_accessed || '-';
                    const durationMs = tc.duration_ms !== undefined ? tc.duration_ms : '-';
                    const gapMs = tc.gap_before_ms !== undefined ? tc.gap_before_ms : '-';
                    const outputText = tc.output || tc.output_summary || '';

                    return (
                      <div key={idx} className="bg-[#18181e] border border-zinc-800 rounded-xl p-4 space-y-3">
                        {/* Step Title Header */}
                        <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2.5">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-indigo-600/30 text-indigo-400 border border-indigo-500/40 flex items-center justify-center font-bold text-[10px]">
                              {stepNum}
                            </span>
                            <span className="font-mono font-semibold text-white text-sm">
                              {toolName}
                            </span>
                          </div>

                          <div className="flex items-center gap-3 font-mono text-[11px]">
                            {gapMs !== '-' && (
                              <span className="text-zinc-400">
                                Jeda berpikir AI: <span className="text-amber-400 font-medium">{gapMs} ms</span>
                              </span>
                            )}
                            <span className="text-zinc-400">
                              Durasi eksekusi: <span className="text-emerald-400 font-medium">{durationMs} ms</span>
                            </span>
                          </div>
                        </div>

                        {/* Files & Lines Accessed */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px]">
                          <div className="bg-zinc-900/90 rounded-lg p-2.5 border border-zinc-800">
                            <span className="text-zinc-400 block mb-1 font-semibold flex items-center gap-1.5">
                              <FileText className="w-3.5 h-3.5 text-blue-400" /> Berkas / Sumber yang Diakses:
                            </span>
                            {files.length > 0 ? (
                              <ul className="list-disc list-inside text-zinc-200 font-mono space-y-0.5">
                                {files.map((f, fIdx) => (
                                  <li key={fIdx} className="truncate" title={f}>{f}</li>
                                ))}
                              </ul>
                            ) : (
                              <span className="text-zinc-500 italic">Tidak ada berkas spesifik</span>
                            )}
                          </div>

                          <div className="bg-zinc-900/90 rounded-lg p-2.5 border border-zinc-800">
                            <span className="text-zinc-400 block mb-1 font-semibold flex items-center gap-1.5">
                              <Layers className="w-3.5 h-3.5 text-purple-400" /> Baris / Range Data yang Dibaca:
                            </span>
                            <span className="text-zinc-200 font-mono">{lines}</span>
                          </div>
                        </div>

                        {/* Input Arguments */}
                        <div className="space-y-1">
                          <span className="text-zinc-400 font-semibold block text-[11px]">
                            Input Parameter (Args):
                          </span>
                          <pre className="bg-zinc-950 p-2.5 rounded-lg border border-zinc-800/80 font-mono text-zinc-300 text-[11px] overflow-x-auto scrollbar-thin">
                            {argsStr}
                          </pre>
                        </div>

                        {/* Raw Output Data */}
                        {outputText && (
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-zinc-400 font-semibold block text-[11px]">
                                Data Mentah Hasil Tool (Output):
                              </span>
                              <button
                                type="button"
                                onClick={() => handleCopy(outputText, `tool-out-${idx}`)}
                                className="text-zinc-400 hover:text-white flex items-center gap-1 text-[10px] cursor-pointer"
                              >
                                {copiedKey === `tool-out-${idx}` ? (
                                  <Check className="w-3 h-3 text-emerald-400" />
                                ) : (
                                  <Copy className="w-3 h-3" />
                                )}
                                <span>{copiedKey === `tool-out-${idx}` ? 'Tersalin' : 'Salin Data'}</span>
                              </button>
                            </div>
                            <pre className="bg-zinc-950 p-2.5 rounded-lg border border-zinc-800/80 font-mono text-zinc-300 text-[11px] max-h-48 overflow-y-auto scrollbar-thin whitespace-pre-wrap">
                              {outputText}
                            </pre>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: WATERFALL TIMING BREAKDOWN */}
          {activeTab === 'timing' && (
            <div className="space-y-4">
              <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4">
                <h4 className="font-semibold text-white">Waterfall Durasi Eksekusi Presisi</h4>
                <p className="text-zinc-400 text-[11px] mt-0.5">
                  Dari request masuk ke AI, filter router, waktu antar pemanggilan tool, durasi pengumpulan data, hingga waktu generasi jawaban final.
                </p>
              </div>

              <div className="bg-[#18181e] border border-zinc-800 rounded-xl p-4 space-y-4">
                <div className="space-y-3 font-mono">
                  {/* Step 1: Upfront Router */}
                  <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                    <div>
                      <div className="text-white font-semibold flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                        1. Upfront Router (Heuristik / Filter Cakupan)
                      </div>
                      <div className="text-[11px] text-zinc-400 mt-0.5">
                        Memvalidasi apakah pertanyaan masuk cakupan Prodi Informatika UNTAN
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-blue-400 font-bold text-sm">
                        {timing?.router_latency_ms !== undefined ? `${timing.router_latency_ms} ms` : '-'}
                      </span>
                    </div>
                  </div>

                  {/* Step 2: Tool Execution Phase */}
                  <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                    <div>
                      <div className="text-white font-semibold flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                        2. Eksekusi Tools & Pengambilan Data (RAG Retrieval)
                      </div>
                      <div className="text-[11px] text-zinc-400 mt-0.5">
                        Total durasi pencarian direktori, pembacaan berkas vault, atau lookup profil dosen
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-indigo-400 font-bold text-sm">
                        {timing?.tools_total_ms !== undefined ? `${timing.tools_total_ms} ms` : '-'}
                      </span>
                    </div>
                  </div>

                  {/* Step 3: LLM Final Generation */}
                  <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                    <div>
                      <div className="text-white font-semibold flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                        3. LLM Final Output Synthesis
                      </div>
                      <div className="text-[11px] text-zinc-400 mt-0.5">
                        Waktu yang dibutuhkan AI merangkum dan menghasilkan jawaban final setelah semua data terkumpul
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-purple-400 font-bold text-sm">
                        {timing?.llm_final_generation_ms !== undefined ? `${timing.llm_final_generation_ms} ms` : '-'}
                      </span>
                    </div>
                  </div>

                  {/* Step 4: Total End to End Latency */}
                  <div className="flex items-center justify-between p-3.5 rounded-lg bg-emerald-950/30 border border-emerald-800/50">
                    <div>
                      <div className="text-emerald-300 font-bold flex items-center gap-2 text-sm">
                        <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                        Total Latensi Keseluruhan (End-to-End Latency)
                      </div>
                      <div className="text-[11px] text-emerald-400/80 mt-0.5">
                        Waktu total sejak request masuk hingga respon selesai diterima client
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-emerald-300 font-bold text-base">
                        {timing?.total_latency_ms !== undefined
                          ? `${timing.total_latency_ms} ms (${log.latency_s}s)`
                          : `${(log.latency_s * 1000).toFixed(0)} ms (${log.latency_s}s)`}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: SYSTEM PROMPT & USER PROMPT */}
          {activeTab === 'prompts' && (
            <div className="space-y-4">
              {/* System Prompt */}
              <div className="bg-[#18181e] border border-zinc-800 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-indigo-400" />
                    System Prompt
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(log.system_prompt || '', 'sys-prompt')}
                    className="text-zinc-400 hover:text-white flex items-center gap-1 text-[11px] cursor-pointer"
                  >
                    {copiedKey === 'sys-prompt' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedKey === 'sys-prompt' ? 'Tersalin' : 'Salin System Prompt'}</span>
                  </button>
                </div>
                <pre className="bg-zinc-950 p-3 rounded-lg border border-zinc-800/80 font-mono text-zinc-300 text-[11px] max-h-60 overflow-y-auto scrollbar-thin whitespace-pre-wrap">
                  {log.system_prompt || 'System prompt tidak terekam pada request ini.'}
                </pre>
              </div>

              {/* User Prompt */}
              <div className="bg-[#18181e] border border-zinc-800 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-blue-400" />
                    User Prompt (Prompt Akhir ke LLM)
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(log.user_prompt || log.question || '', 'user-prompt')}
                    className="text-zinc-400 hover:text-white flex items-center gap-1 text-[11px] cursor-pointer"
                  >
                    {copiedKey === 'user-prompt' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedKey === 'user-prompt' ? 'Tersalin' : 'Salin User Prompt'}</span>
                  </button>
                </div>
                <pre className="bg-zinc-950 p-3 rounded-lg border border-zinc-800/80 font-mono text-zinc-300 text-[11px] max-h-40 overflow-y-auto scrollbar-thin whitespace-pre-wrap">
                  {log.user_prompt || log.question || '-'}
                </pre>
              </div>
            </div>
          )}

          {/* TAB 4: PERTANYAAN & JAWABAN AI */}
          {activeTab === 'qa' && (
            <div className="space-y-4">
              <div className="bg-[#18181e] border border-zinc-800 rounded-xl p-4 space-y-2">
                <span className="font-semibold text-zinc-400 block text-[11px] uppercase tracking-wider">
                  Pertanyaan Pengguna (Mahasiswa):
                </span>
                <p className="text-white font-medium text-sm leading-relaxed bg-zinc-950 p-3 rounded-lg border border-zinc-800">
                  {log.question}
                </p>
              </div>

              <div className="bg-[#18181e] border border-zinc-800 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-zinc-400 block text-[11px] uppercase tracking-wider">
                    Jawaban Lengkap Asisten AI (Luco):
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(log.answer || '', 'qa-answer')}
                    className="text-zinc-400 hover:text-white flex items-center gap-1 text-[11px] cursor-pointer"
                  >
                    {copiedKey === 'qa-answer' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedKey === 'qa-answer' ? 'Tersalin' : 'Salin Jawaban'}</span>
                  </button>
                </div>
                <div className="text-zinc-200 text-xs leading-relaxed bg-zinc-950 p-3.5 rounded-lg border border-zinc-800 whitespace-pre-wrap font-sans">
                  {log.answer || 'Tidak ada konten jawaban.'}
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: BIAYA & TOKEN */}
          {activeTab === 'tokens' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-[#18181e] border border-zinc-800 rounded-xl p-4 space-y-3 font-mono">
                <span className="text-xs font-semibold text-white block border-b border-zinc-800 pb-2">
                  Komposisi Token Lengkap (Input Breakdown)
                </span>
                <div className="space-y-1.5 text-[11px]">
                  <div className="flex justify-between py-0.5 text-zinc-300">
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                      1. Pertanyaan User (Plain Query):
                    </span>
                    <span className="text-cyan-300 font-bold">
                      {(log.user_prompt_tokens !== undefined && log.user_prompt_tokens > 0
                        ? log.user_prompt_tokens
                        : Math.min(log.prompt_tokens, Math.max(1, Math.round(log.question.length / 4)))
                      ).toLocaleString()}{' '}
                      tok
                    </span>
                  </div>

                  <div className="flex justify-between py-0.5 text-zinc-300">
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                      2. System Prompt & Aturan Agen:
                    </span>
                    <span className="text-indigo-300 font-bold">
                      {(log.system_prompt_tokens !== undefined && log.system_prompt_tokens > 0
                        ? log.system_prompt_tokens
                        : log.system_prompt
                        ? Math.max(1, Math.round(log.system_prompt.length / 4))
                        : 0
                      ).toLocaleString()}{' '}
                      tok
                    </span>
                  </div>

                  <div className="flex justify-between py-0.5 text-zinc-300">
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                      3. Konteks Dokumen RAG (Hasil Retrieval Vault):
                    </span>
                    <span className="text-amber-300 font-bold">
                      {(log.context_tokens !== undefined && log.context_tokens > 0
                        ? log.context_tokens
                        : Math.max(
                            0,
                            log.prompt_tokens -
                              ((log.user_prompt_tokens || Math.round(log.question.length / 4)) +
                                (log.system_prompt_tokens || (log.system_prompt ? Math.round(log.system_prompt.length / 4) : 0)))
                          )
                      ).toLocaleString()}{' '}
                      tok
                    </span>
                  </div>

                  <div className="flex justify-between py-1.5 border-t border-zinc-800 text-blue-300 font-bold">
                    <span>Total Input Tokens (Prompt Masuk LLM):</span>
                    <span>{log.prompt_tokens?.toLocaleString()} tok</span>
                  </div>

                  <div className="flex justify-between py-1 text-purple-300 font-bold">
                    <span>Output Tokens (Completion Jawaban):</span>
                    <span>{log.completion_tokens?.toLocaleString()} tok</span>
                  </div>

                  <div className="flex justify-between py-1.5 border-t border-zinc-700/80 text-white font-bold text-sm">
                    <span>Total Keseluruhan Tokens:</span>
                    <span>{log.total_tokens?.toLocaleString()} tok</span>
                  </div>
                </div>
              </div>

              <div className="bg-[#18181e] border border-zinc-800 rounded-xl p-4 space-y-3 font-mono">
                <span className="text-xs font-semibold text-white block border-b border-zinc-800 pb-2">
                  Estimasi Biaya Inferensi
                </span>
                <div className="flex justify-between py-1 text-zinc-300">
                  <span>Biaya (USD):</span>
                  <span className="text-emerald-400 font-bold">${log.estimated_cost_usd?.toFixed(6)}</span>
                </div>
                <div className="flex justify-between py-1 text-zinc-300">
                  <span>Biaya (IDR):</span>
                  <span className="text-emerald-400 font-bold">
                    Rp {log.estimated_cost_idr ? log.estimated_cost_idr.toFixed(2) : '0.00'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-t border-zinc-800 text-zinc-400 text-[11px]">
                  <span>Tier Pricing Model:</span>
                  <span>Gemini Flash (~$0.10 in / $0.40 out)</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-zinc-800 bg-[#16161c] flex items-center justify-between text-xs text-zinc-400">
          <span>Tekan ESC atau tombol Tutup untuk kembali ke tabel log</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white font-medium transition cursor-pointer"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
};
