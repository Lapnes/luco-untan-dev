import React, { useMemo, useState, useRef } from 'react';
import { AuditLogItem } from '../api';
import { TrendingUp, CandlestickChart, Activity } from 'lucide-react';

export interface TimeSeriesChartProps {
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  metricType: 'cost' | 'tokens';
  logs: AuditLogItem[];
  startIso?: string;
  endIso?: string;
  totalDisplay: string;
  secondaryDisplay?: string;
  footerLeft?: React.ReactNode;
  footerRight?: React.ReactNode;
}

interface BucketPoint {
  start: number;
  end: number;
  mid: number;
  label: string;
  requests: number;
  val: number;
  promptTokens: number;
  compTokens: number;
  costUsd: number;
  costIdr: number;
  high: number;
  low: number;
  open: number;
  close: number;
  isUp: boolean;
  hasError: boolean;
  maVal: number;
  maPrompt: number;
  maComp: number;
}

// Catmull-Rom Spline to Cubic Bezier Curve SVG Path Generator
const getSmoothCurvePath = (points: { x: number; y: number }[]): string => {
  if (!points || points.length === 0) return '';
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;
  if (points.length === 2) return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;

  let d = `M ${points[0].x.toFixed(1)} ${points[0].y.toFixed(1)}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i === 0 ? 0 : i - 1];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[i + 2 < points.length ? i + 2 : i + 1];

    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;

    d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
  }
  return d;
};

export const TelemetryTimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  title,
  subtitle,
  icon,
  metricType,
  logs,
  startIso,
  endIso,
  totalDisplay,
  secondaryDisplay,
  footerLeft,
  footerRight,
}) => {
  const [chartMode, setChartMode] = useState<'candlestick' | 'line'>('candlestick');
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // 1. Hitung Batas Waktu Min & Max Secara Fleksibel
  const { tMin, tMax, durationMs } = useMemo(() => {
    let minTime = startIso ? new Date(startIso).getTime() : 0;
    let maxTime = endIso ? new Date(endIso).getTime() : 0;

    if (!minTime || !maxTime || isNaN(minTime) || isNaN(maxTime)) {
      if (logs.length > 0) {
        const timestamps = logs
          .map((l) => (l.created_at ? new Date(l.created_at).getTime() : 0))
          .filter((t) => t > 0);
        if (timestamps.length > 0) {
          minTime = Math.min(...timestamps);
          maxTime = Math.max(...timestamps);
          const buffer = Math.max(maxTime - minTime, 3600 * 1000) * 0.03;
          minTime -= buffer;
          maxTime += buffer;
        } else {
          maxTime = Date.now();
          minTime = maxTime - 24 * 3600 * 1000;
        }
      } else {
        maxTime = Date.now();
        minTime = maxTime - 24 * 3600 * 1000;
      }
    }

    if (maxTime <= minTime) maxTime = minTime + 3600 * 1000;
    return { tMin: minTime, tMax: maxTime, durationMs: maxTime - minTime };
  }, [logs, startIso, endIso]);

  // 2. Format Label Waktu Dinamis berdasarkan durasi rentang waktu
  const formatTimeLabel = (ms: number): string => {
    const d = new Date(ms);
    if (durationMs <= 24 * 3600 * 1000) {
      return d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', hour12: false });
    }
    if (durationMs <= 7 * 24 * 3600 * 1000) {
      const day = d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
      const time = d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', hour12: false });
      return `${day} ${time}`;
    }
    return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
  };

  // 3. Bangun N Interval Slices Data (N = 36 untuk kerapatan yang pas seperti TradingView/grafik saham)
  const N = 36;
  const buckets = useMemo<BucketPoint[]>(() => {
    const sliceDur = durationMs / N;
    const rawBuckets: BucketPoint[] = [];

    for (let i = 0; i < N; i++) {
      const bStart = tMin + i * sliceDur;
      const bEnd = bStart + sliceDur;
      const bMid = (bStart + bEnd) / 2;

      const sliceLogs = logs.filter((l) => {
        if (!l.created_at) return false;
        const t = new Date(l.created_at).getTime();
        return t >= bStart && t < bEnd;
      });

      let val = 0;
      let promptTokens = 0;
      let compTokens = 0;
      let costUsd = 0;
      let costIdr = 0;
      let high = 0;
      let low = 0;
      let open = 0;
      let close = 0;
      let hasError = false;

      if (sliceLogs.length > 0) {
        if (metricType === 'cost') {
          const costs = sliceLogs.map((l) => l.estimated_cost_usd || 0);
          val = costs.reduce((a, b) => a + b, 0);
          costUsd = val;
          costIdr = sliceLogs.reduce((a, l) => a + (l.estimated_cost_idr || 0), 0);
          high = Math.max(...costs);
          low = Math.min(...costs);
          open = costs[0];
          close = costs[costs.length - 1];
        } else {
          promptTokens = sliceLogs.reduce((a, l) => a + (l.prompt_tokens || 0), 0);
          compTokens = sliceLogs.reduce((a, l) => a + (l.completion_tokens || 0), 0);
          val = promptTokens + compTokens;
          high = Math.max(...sliceLogs.map((l) => l.total_tokens || 0));
          low = Math.min(...sliceLogs.map((l) => l.total_tokens || 0));
          open = sliceLogs[0].total_tokens || 0;
          close = sliceLogs[sliceLogs.length - 1].total_tokens || 0;
        }

        hasError = sliceLogs.some(
          (l) => l.status === 'error' || l.status === 'redirect' || (l.latency_s && l.latency_s > 6)
        );
      }

      const isUp = close >= open && !hasError;
      const label = `${formatTimeLabel(bStart)} - ${formatTimeLabel(bEnd)}`;

      rawBuckets.push({
        start: bStart,
        end: bEnd,
        mid: bMid,
        label,
        requests: sliceLogs.length,
        val,
        promptTokens,
        compTokens,
        costUsd,
        costIdr,
        high,
        low,
        open,
        close,
        isUp,
        hasError,
        maVal: val,
        maPrompt: promptTokens,
        maComp: compTokens,
      });
    }

    // 4. Hitung Moving Average (Trendline Curve) untuk Total, Input, dan Output
    return rawBuckets.map((b, idx, arr) => {
      const windowStart = Math.max(0, idx - 2);
      const windowEnd = Math.min(arr.length, idx + 3);
      const sliceWindow = arr.slice(windowStart, windowEnd);

      const sumVal = sliceWindow.reduce((acc, curr) => acc + curr.val, 0);
      const sumPrompt = sliceWindow.reduce((acc, curr) => acc + curr.promptTokens, 0);
      const sumComp = sliceWindow.reduce((acc, curr) => acc + curr.compTokens, 0);

      const ma = sumVal / sliceWindow.length;
      const maPrompt = sumPrompt / sliceWindow.length;
      const maComp = sumComp / sliceWindow.length;

      return {
        ...b,
        maVal: Number(ma.toFixed(6)),
        maPrompt: Number(maPrompt.toFixed(6)),
        maComp: Number(maComp.toFixed(6)),
      };
    });
  }, [logs, tMin, durationMs, metricType]);

  // 5. Nilai Maksimal untuk Skala Y
  const maxVal = useMemo(() => {
    if (metricType === 'cost') {
      const peak = Math.max(...buckets.map((b) => Math.max(b.val, b.maVal, b.high)));
      return peak > 0 ? peak * 1.15 : 0.005;
    } else {
      const peak = Math.max(...buckets.map((b) => Math.max(b.val, b.maVal, b.promptTokens)));
      return peak > 0 ? peak * 1.15 : 1000;
    }
  }, [buckets, metricType]);

  // Dimensi SVG
  const svgWidth = 600;
  const svgHeight = 140;
  const padTop = 16;
  const padBottom = 22;
  const padLeft = 8;
  const padRight = 8;
  const plotWidth = svgWidth - padLeft - padRight;
  const plotHeight = svgHeight - padTop - padBottom;
  const baselineY = padTop + plotHeight;

  // Koordinat Titik Kurva Total (Biaya / Total Tokens)
  const totalTrendPoints = useMemo(() => {
    return buckets.map((b, i) => {
      const x = padLeft + (i + 0.5) * (plotWidth / N);
      const ratio = Math.min(1, Math.max(0, b.maVal / maxVal));
      const y = baselineY - ratio * plotHeight;
      return { x, y };
    });
  }, [buckets, maxVal, plotWidth, plotHeight, baselineY, N]);

  // Koordinat Titik Kurva Input Tokens (Prompt)
  const inputTrendPoints = useMemo(() => {
    return buckets.map((b, i) => {
      const x = padLeft + (i + 0.5) * (plotWidth / N);
      const ratio = Math.min(1, Math.max(0, b.maPrompt / maxVal));
      const y = baselineY - ratio * plotHeight;
      return { x, y };
    });
  }, [buckets, maxVal, plotWidth, plotHeight, baselineY, N]);

  // Koordinat Titik Kurva Output Tokens (Completion)
  const outputTrendPoints = useMemo(() => {
    return buckets.map((b, i) => {
      const x = padLeft + (i + 0.5) * (plotWidth / N);
      const ratio = Math.min(1, Math.max(0, b.maComp / maxVal));
      const y = baselineY - ratio * plotHeight;
      return { x, y };
    });
  }, [buckets, maxVal, plotWidth, plotHeight, baselineY, N]);

  const totalCurvePath = useMemo(() => getSmoothCurvePath(totalTrendPoints), [totalTrendPoints]);
  const inputCurvePath = useMemo(() => getSmoothCurvePath(inputTrendPoints), [inputTrendPoints]);
  const outputCurvePath = useMemo(() => getSmoothCurvePath(outputTrendPoints), [outputTrendPoints]);

  const totalAreaPath = useMemo(() => {
    if (!totalTrendPoints.length) return '';
    const last = totalTrendPoints[totalTrendPoints.length - 1];
    const first = totalTrendPoints[0];
    return `${totalCurvePath} L ${last.x.toFixed(1)} ${baselineY} L ${first.x.toFixed(1)} ${baselineY} Z`;
  }, [totalCurvePath, totalTrendPoints, baselineY]);

  const inputAreaPath = useMemo(() => {
    if (!inputTrendPoints.length) return '';
    const last = inputTrendPoints[inputTrendPoints.length - 1];
    const first = inputTrendPoints[0];
    return `${inputCurvePath} L ${last.x.toFixed(1)} ${baselineY} L ${first.x.toFixed(1)} ${baselineY} Z`;
  }, [inputCurvePath, inputTrendPoints, baselineY]);

  const outputAreaPath = useMemo(() => {
    if (!outputTrendPoints.length) return '';
    const last = outputTrendPoints[outputTrendPoints.length - 1];
    const first = outputTrendPoints[0];
    return `${outputCurvePath} L ${last.x.toFixed(1)} ${baselineY} L ${first.x.toFixed(1)} ${baselineY} Z`;
  }, [outputCurvePath, outputTrendPoints, baselineY]);

  // Handler Interaksi Hover pada SVG
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const pct = Math.max(0, Math.min(1, clientX / rect.width));
    const idx = Math.min(N - 1, Math.max(0, Math.floor(pct * N)));
    setHoveredIdx(idx);
  };

  const handleMouseLeave = () => {
    setHoveredIdx(null);
  };

  const activeBucket = hoveredIdx !== null ? buckets[hoveredIdx] : null;
  const activeTotalPoint = hoveredIdx !== null ? totalTrendPoints[hoveredIdx] : null;
  const activeInputPoint = hoveredIdx !== null ? inputTrendPoints[hoveredIdx] : null;
  const activeOutputPoint = hoveredIdx !== null ? outputTrendPoints[hoveredIdx] : null;

  // 5 Penanda Label X-Axis Merata (0%, 25%, 50%, 75%, 100%)
  const xAxisMarkers = useMemo(() => {
    return [0, 0.25, 0.5, 0.75, 1].map((pct) => {
      const timeMs = tMin + pct * durationMs;
      return formatTimeLabel(timeMs);
    });
  }, [tMin, durationMs]);

  return (
    <div className="bg-[#121319] border border-zinc-800/80 hover:border-zinc-700/80 transition-all duration-300 rounded-2xl p-5 flex flex-col justify-between relative group shadow-lg">
      {/* Header Kartu: Judul, Nilai Total, & Mode Toggle */}
      <div>
        <div className="flex items-center justify-between text-xs text-zinc-400 mb-1.5">
          <span className="font-semibold text-zinc-200 flex items-center gap-1.5">
            {icon}
            <span>{title}</span>
          </span>

          {/* Toggle Tampilan: Candlestick + MA vs Area Trendline */}
          <div className="flex items-center bg-zinc-900/90 p-0.5 rounded-lg border border-zinc-800 text-[10px]">
            <button
              type="button"
              onClick={() => setChartMode('candlestick')}
              title="Tampilkan grafik Candlestick dengan kurva tren rata-rata bergerak (Moving Average)"
              className={`px-2 py-0.5 rounded-md transition cursor-pointer flex items-center gap-1 ${
                chartMode === 'candlestick'
                  ? 'bg-zinc-800 text-white font-semibold shadow-xs'
                  : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              <CandlestickChart className="w-3 h-3 text-emerald-400" />
              <span className="hidden sm:inline">Candle</span>
            </button>
            <button
              type="button"
              onClick={() => setChartMode('line')}
              title="Tampilkan grafik garis gelombang / kurva area"
              className={`px-2 py-0.5 rounded-md transition cursor-pointer flex items-center gap-1 ${
                chartMode === 'line'
                  ? 'bg-zinc-800 text-white font-semibold shadow-xs'
                  : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              <TrendingUp className="w-3 h-3 text-sky-400" />
              <span className="hidden sm:inline">Line</span>
            </button>
          </div>
        </div>

        {/* Nilai Metrik Utama */}
        <div className="flex items-baseline justify-between gap-2">
          <div className="text-2xl font-bold text-white tracking-tight font-sans">
            {totalDisplay}
          </div>
          {secondaryDisplay && (
            <div className="text-xs text-emerald-400 font-medium font-mono">
              {secondaryDisplay}
            </div>
          )}
        </div>

        {/* Status Interval Waktu / Hover Detail Live */}
        <div className="text-[11px] text-zinc-400 mt-1 min-h-[20px] flex items-center justify-between">
          {activeBucket ? (
            <div className="flex items-center gap-2 font-mono text-[11px] animate-fade-in flex-wrap">
              <span className="text-zinc-400 font-sans">{activeBucket.label}:</span>
              {metricType === 'cost' ? (
                <>
                  <span className="font-semibold text-white">
                    ${activeBucket.costUsd.toFixed(4)} (~Rp {activeBucket.costIdr.toLocaleString('id-ID')})
                  </span>
                  <span className="text-zinc-500">({activeBucket.requests} req)</span>
                  <span className="text-zinc-500 text-[10px] hidden sm:inline">
                    Min-Max: ${activeBucket.low.toFixed(4)} - ${activeBucket.high.toFixed(4)}
                  </span>
                </>
              ) : (
                <>
                  <span className="font-semibold text-white">
                    {activeBucket.val.toLocaleString()} tok
                  </span>
                  <span className="text-sky-400 font-semibold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-sky-400"></span>
                    In: {activeBucket.promptTokens.toLocaleString()} ({activeBucket.val > 0 ? Math.round((activeBucket.promptTokens / activeBucket.val) * 100) : 0}%)
                  </span>
                  <span className="text-rose-400 font-semibold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
                    Out: {activeBucket.compTokens.toLocaleString()} ({activeBucket.val > 0 ? Math.round((activeBucket.compTokens / activeBucket.val) * 100) : 0}%)
                  </span>
                  <span className="text-zinc-500 text-[10px] hidden sm:inline">
                    (Peak: {activeBucket.high.toLocaleString()} tok)
                  </span>
                </>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-between w-full flex-wrap gap-1">
              <span className="text-zinc-400 text-[11px] truncate">{subtitle}</span>
              {metricType === 'tokens' ? (
                <div className="flex items-center gap-1.5 text-[10px] font-mono">
                  <span className="inline-flex items-center gap-1 text-sky-400 bg-sky-950/60 px-1.5 py-0.5 rounded border border-sky-800/40">
                    <span className="w-1.5 h-1.5 rounded-full bg-sky-400"></span> Input
                  </span>
                  <span className="inline-flex items-center gap-1 text-rose-400 bg-rose-950/60 px-1.5 py-0.5 rounded border border-rose-800/40">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span> Output (Merah)
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 text-[10px] font-mono">
                  <span className="inline-flex items-center gap-1 text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/40">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Normal
                  </span>
                  <span className="inline-flex items-center gap-1 text-rose-400 bg-rose-950/60 px-1.5 py-0.5 rounded border border-rose-800/40">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span> Lonjakan
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* SVG Time Series Graph (Candlestick & Moving Average Curve) */}
      <div className="pt-3 pb-1 relative select-none">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          preserveAspectRatio="none"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          className="w-full h-28 sm:h-32 overflow-visible cursor-crosshair"
        >
          <defs>
            {/* Area Gradient Fills */}
            <linearGradient id="grad-cost" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.0" />
            </linearGradient>

            <linearGradient id="grad-tokens-input" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.22" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.0" />
            </linearGradient>

            <linearGradient id="grad-tokens-output" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.30" />
              <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.0" />
            </linearGradient>

            {/* Glowing Drop Shadows */}
            <filter id="glow-cost" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="2" floodColor="#38bdf8" floodOpacity="0.6" />
            </filter>
            <filter id="glow-tokens-input" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="2" floodColor="#38bdf8" floodOpacity="0.7" />
            </filter>
            <filter id="glow-tokens-output" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="2" floodColor="#f43f5e" floodOpacity="0.8" />
            </filter>
          </defs>

          {/* 1. Background Grid Lines (Subtle Horizontal Dashed Lines) */}
          {[0, 0.33, 0.66, 1].map((pct, gIdx) => {
            const gy = padTop + pct * plotHeight;
            return (
              <line
                key={gIdx}
                x1={padLeft}
                y1={gy}
                x2={svgWidth - padRight}
                y2={gy}
                stroke="#1f2230"
                strokeWidth="1"
                strokeDasharray="3 3"
              />
            );
          })}

          {/* 2. Vertical Grid Lines (Quarter Time Markers) */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, gIdx) => {
            const gx = padLeft + pct * plotWidth;
            return (
              <line
                key={gIdx}
                x1={gx}
                y1={padTop}
                x2={gx}
                y2={baselineY}
                stroke="#1a1d29"
                strokeWidth="1"
                strokeDasharray="2 3"
              />
            );
          })}

          {/* 3. Candlesticks Layer (Active when chartMode === 'candlestick') */}
          {chartMode === 'candlestick' &&
            buckets.map((b, i) => {
              const cx = padLeft + (i + 0.5) * (plotWidth / N);
              const candleW = Math.max(3, Math.min(8, (plotWidth / N) * 0.65));

              if (b.requests === 0 || b.val === 0) {
                return (
                  <circle
                    key={i}
                    cx={cx}
                    cy={baselineY}
                    r="1"
                    fill="#27272a"
                    className="opacity-40"
                  />
                );
              }

              if (metricType === 'tokens') {
                // LILIN STACKED 2 WARNA:
                // Bagian Bawah = Output Tokens (Merah / #f43f5e)
                // Bagian Atas = Input Tokens (Biru / #0284c7)
                // Sumbu Atas (Wick) = Lonjakan Puncak 1 Request
                const totalRatio = Math.min(1, Math.max(0.04, b.val / maxVal));
                const totalBarH = Math.max(4, totalRatio * plotHeight);

                const compRatio = b.val > 0 ? b.compTokens / b.val : 0;
                const compH =
                  b.compTokens > 0
                    ? Math.max(2, Math.min(totalBarH - 2, Math.round(totalBarH * compRatio)))
                    : 0;
                const promptH = Math.max(2, totalBarH - compH);

                const compY = baselineY - compH;
                const promptY = baselineY - totalBarH;

                const peakRatio = Math.min(1, Math.max(totalRatio, b.high / maxVal));
                const peakY = baselineY - peakRatio * plotHeight;

                return (
                  <g key={i} className="transition-opacity hover:opacity-100">
                    {/* Sumbu Lonjakan Puncak (Peak Wick) */}
                    {peakY < promptY && (
                      <line
                        x1={cx}
                        y1={peakY}
                        x2={cx}
                        y2={promptY}
                        stroke="#38bdf8"
                        strokeWidth="1.2"
                        strokeDasharray="2 1"
                        className="opacity-75"
                      />
                    )}

                    {/* Lilin Bagian Atas: Input Tokens (Biru) */}
                    <rect
                      x={cx - candleW / 2}
                      y={promptY}
                      width={candleW}
                      height={promptH}
                      rx={compH > 0 ? 0 : 1.5}
                      fill="#0284c7"
                      stroke="#38bdf8"
                      strokeWidth="0.8"
                      className="transition-transform duration-150 hover:scale-105 opacity-90"
                    >
                      <title>{`${b.label}\nInput Tokens: ${b.promptTokens.toLocaleString()}\nPeak Req: ${b.high.toLocaleString()}`}</title>
                    </rect>

                    {/* Lilin Bagian Bawah: Output Tokens (Merah) */}
                    {compH > 0 && (
                      <rect
                        x={cx - candleW / 2}
                        y={compY}
                        width={candleW}
                        height={compH}
                        rx="1"
                        fill="#f43f5e"
                        stroke="#fb7185"
                        strokeWidth="0.8"
                        className="transition-transform duration-150 hover:scale-105 opacity-95"
                      >
                        <title>{`${b.label}\nOutput Tokens: ${b.compTokens.toLocaleString()}`}</title>
                      </rect>
                    )}
                  </g>
                );
              }

              // Untuk 'cost': Candlestick Finansial (Hijau normal, Merah lonjakan)
              const highRatio = Math.min(1, Math.max(0.04, b.high / maxVal));
              const lowRatio = Math.min(1, Math.max(0.01, b.low / maxVal));
              const openRatio = Math.min(1, Math.max(0.02, b.open / maxVal));
              const closeRatio = Math.min(1, Math.max(0.02, b.close / maxVal));

              const highY = baselineY - highRatio * plotHeight;
              const lowY = baselineY - lowRatio * plotHeight;
              const bodyTopY = baselineY - Math.max(openRatio, closeRatio) * plotHeight;
              const bodyBottomY = baselineY - Math.min(openRatio, closeRatio) * plotHeight;
              const bodyH = Math.max(3, bodyBottomY - bodyTopY);

              const candleColor = b.isUp ? '#10b981' : '#f43f5e';

              return (
                <g key={i} className="transition-opacity hover:opacity-100">
                  {/* Wick (Sumbu Lilin Min ke Max Request Cost) */}
                  <line
                    x1={cx}
                    y1={highY}
                    x2={cx}
                    y2={lowY}
                    stroke={candleColor}
                    strokeWidth="1.2"
                    strokeLinecap="round"
                    className="opacity-75"
                  />

                  {/* Body Lilin */}
                  <rect
                    x={cx - candleW / 2}
                    y={bodyTopY}
                    width={candleW}
                    height={bodyH}
                    rx="1.5"
                    fill={candleColor}
                    stroke={b.hasError ? '#f43f5e' : candleColor}
                    strokeWidth="0.8"
                    className="transition-transform duration-150 hover:scale-105"
                  >
                    <title>{`${b.label}\nBiaya: $${b.costUsd.toFixed(4)}\nMin-Max: $${b.low.toFixed(4)} - $${b.high.toFixed(4)}`}</title>
                  </rect>
                </g>
              );
            })}

          {/* 4. Area Fills & Moving Average Curves */}
          {metricType === 'tokens' ? (
            <>
              {/* Area Shading Input (Biru) & Output (Merah) */}
              {inputAreaPath && (
                <path
                  d={inputAreaPath}
                  fill="url(#grad-tokens-input)"
                  className="transition-opacity duration-300 pointer-events-none"
                />
              )}
              {outputAreaPath && (
                <path
                  d={outputAreaPath}
                  fill="url(#grad-tokens-output)"
                  className="transition-opacity duration-300 pointer-events-none"
                />
              )}

              {/* Garis 1: Kurva Tren Input Tokens (Biru Cerah) */}
              {inputCurvePath && (
                <path
                  d={inputCurvePath}
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  filter="url(#glow-tokens-input)"
                  className="transition-all duration-300"
                />
              )}

              {/* Garis 2: Kurva Tren Output Tokens (Merah Cerah) */}
              {outputCurvePath && (
                <path
                  d={outputCurvePath}
                  fill="none"
                  stroke="#f43f5e"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  filter="url(#glow-tokens-output)"
                  className="transition-all duration-300"
                />
              )}
            </>
          ) : (
            <>
              {/* Cost Area & Curve */}
              {totalAreaPath && (
                <path
                  d={totalAreaPath}
                  fill="url(#grad-cost)"
                  className="transition-opacity duration-300 pointer-events-none"
                />
              )}
              {totalCurvePath && (
                <path
                  d={totalCurvePath}
                  fill="none"
                  stroke="#ffffff"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  filter="url(#glow-cost)"
                  className="transition-all duration-300"
                />
              )}
            </>
          )}

          {/* 5. Active Hover Crosshair Line & Points */}
          {hoveredIdx !== null && activeTotalPoint && (
            <g className="animate-fade-in pointer-events-none">
              {/* Garis Crosshair Vertikal */}
              <line
                x1={activeTotalPoint.x}
                y1={padTop}
                x2={activeTotalPoint.x}
                y2={baselineY}
                stroke="#52525b"
                strokeWidth="1.2"
                strokeDasharray="2 3"
                className="opacity-80"
              />

              {metricType === 'tokens' && activeInputPoint && activeOutputPoint ? (
                <>
                  {/* Titik Input (Biru) pada Kurva */}
                  <circle
                    cx={activeInputPoint.x}
                    cy={activeInputPoint.y}
                    r="4.5"
                    fill="#38bdf8"
                    stroke="#ffffff"
                    strokeWidth="2"
                    className="shadow-lg"
                  />

                  {/* Titik Output (Merah) pada Kurva */}
                  <circle
                    cx={activeOutputPoint.x}
                    cy={activeOutputPoint.y}
                    r="4.5"
                    fill="#f43f5e"
                    stroke="#ffffff"
                    strokeWidth="2"
                    className="shadow-lg"
                  />
                </>
              ) : (
                <circle
                  cx={activeTotalPoint.x}
                  cy={activeTotalPoint.y}
                  r="4.5"
                  fill="#ffffff"
                  stroke="#0284c7"
                  strokeWidth="2"
                  className="shadow-lg"
                />
              )}
            </g>
          )}

          {/* Baseline X-Axis Border */}
          <line
            x1={padLeft}
            y1={baselineY}
            x2={svgWidth - padRight}
            y2={baselineY}
            stroke="#262938"
            strokeWidth="1.2"
          />
        </svg>

        {/* 7. Dynamic X-Axis Time Labels (0%, 25%, 50%, 75%, 100%) */}
        <div className="flex items-center justify-between text-[10px] text-zinc-500 font-mono pt-1.5 px-1 border-t border-zinc-800/80 select-none">
          {xAxisMarkers.map((lbl, idx) => (
            <span key={idx} className={idx === 0 ? 'text-left' : idx === 4 ? 'text-right' : 'text-center'}>
              {lbl}
            </span>
          ))}
        </div>
      </div>

      {/* Footer Kartu: Keterangan Legenda & Model */}
      <div className="flex items-center justify-between text-[11px] text-zinc-400 pt-2.5 border-t border-zinc-800/80">
        <div>{footerLeft}</div>
        <div>{footerRight}</div>
      </div>
    </div>
  );
};
