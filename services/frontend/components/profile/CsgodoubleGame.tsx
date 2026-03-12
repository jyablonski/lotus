"use client";

import { useState, useEffect, useCallback, useRef } from "react";

const ROLL_INTERVAL_MS = 45_000;
const SPIN_DURATION_MS = 10_000;
const WIN_REVEAL_MS = 2_000;
const INITIAL_BALANCE = 100;

// Original CSGODouble: 0–14 (15 numbers), one green (0), red 1–7, black 8–14
const BASE_SEQUENCE = [
  1, 14, 2, 13, 3, 12, 4, 0, 11, 5, 10, 6, 9, 7, 8,
] as const;
const NUMBERS = [...BASE_SEQUENCE] as const;

// Rotation offsets per copy — varied green placement across the strip
const COPY_OFFSETS = [0, 4, 9, 2, 11, 6, 1, 13, 3, 8, 12, 5] as const;

// Virtual infinite strip: any position p maps to a cell value deterministically.
// No STRIP_ARR — the strip is unbounded so we never run out of cells.
function virtualCell(p: number): number {
  const i = Math.floor(p);
  const copy = Math.floor(i / NUMBERS.length);
  const offset = COPY_OFFSETS[copy % COPY_OFFSETS.length];
  return NUMBERS[((i % NUMBERS.length) + offset) % NUMBERS.length];
}

// Search forward from fromPos for the next occurrence of result (≥ minAdvance cells away).
function findVirtualLanding(
  result: number,
  fromPos: number,
  minAdvance = 150,
): number {
  const start = Math.ceil(fromPos) + minAdvance;
  for (let i = start; i < start + NUMBERS.length * 5; i++) {
    if (virtualCell(i) === result) return i;
  }
  return start; // fallback (shouldn't hit)
}

// Virtual position used on first load — arbitrary, just somewhere in the middle.
const VIRTUAL_INITIAL = 1000;
// How many cells to render on each side of the center pointer.
const VISIBLE_HALF = 15;

const CELL_STEP_REM = 2.95;
const GREEN_NUMBER = 0;
const HISTORY_LENGTH = 10;
const STATE_API = "/api/v1/csgodouble";

const BET_BUTTON_CLASS =
  "rounded-lg border border-dark-600 bg-dark-700 px-3 py-2 text-sm text-dark-200 hover:bg-dark-600";

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

type Zone = "1-7" | "0" | "8-14";

const PAYOUT: Record<Zone, number> = {
  "1-7": 2,
  "0": 14,
  "8-14": 2,
};

function getZone(n: number): Zone | null {
  if (n === 0) return "0";
  if (n >= 1 && n <= 7) return "1-7";
  if (n >= 8 && n <= 14) return "8-14";
  return null;
}

function cellColor(n: number): string {
  if (n === GREEN_NUMBER) return "bg-emerald-600 text-white";
  if (n >= 1 && n <= 7) return "bg-red-600 text-white";
  return "bg-zinc-900 text-zinc-100";
}

function zoneRevealClass(n: number): string {
  if (n === GREEN_NUMBER)
    return "border-emerald-500/60 bg-emerald-900/40 text-emerald-300";
  if (n >= 1 && n <= 7) return "border-red-500/60 bg-red-900/40 text-red-300";
  return "border-zinc-600/60 bg-zinc-900/60 text-zinc-200";
}

export function CsgodoubleGame() {
  const [balance, setBalance] = useState(INITIAL_BALANCE);
  const [serverNextRollAt, setServerNextRollAt] = useState<number | null>(null);
  const [serverHistory, setServerHistory] = useState<number[]>([]);
  const [stateLoading, setStateLoading] = useState(true);
  const [countdown, setCountdown] = useState(0);
  const [currentRoll, setCurrentRoll] = useState<number | null>(null);
  const [betInput, setBetInput] = useState("");
  const [lastBetAmount, setLastBetAmount] = useState(0);
  const [bets, setBets] = useState<Record<Zone, number>>({
    "1-7": 0,
    "0": 0,
    "8-14": 0,
  });
  const [isSpinning, setIsSpinning] = useState(false);
  // Continuous virtual position — persists between spins for smooth transitions
  const [spinPosition, setSpinPosition] = useState(VIRTUAL_INITIAL);
  const [showWinReveal, setShowWinReveal] = useState(false);
  const [winDelta, setWinDelta] = useState<number | null>(null);

  const spinStartRef = useRef<number>(0);
  const rafRef = useRef<number>(0);
  const winRevealTimeoutRef = useRef<number | null>(null);
  const pendingServerStateRef = useRef<{
    nextRollAt: number;
    history: number[];
  } | null>(null);
  const betsRef = useRef(bets);
  betsRef.current = bets;
  // Always-current spinPosition so startSpin closure reads the live value
  const spinPositionRef = useRef(spinPosition);
  spinPositionRef.current = spinPosition;

  const betAmount = Math.max(0, Math.floor(Number(betInput) || 0));
  const totalPlaced = bets["1-7"] + bets["0"] + bets["8-14"];

  const resolveRoll = useCallback((result: number) => {
    const zone = getZone(result);
    if (!zone) return;
    const b = betsRef.current;
    const totalBet = b["1-7"] + b["0"] + b["8-14"];
    let payout = 0;
    if (zone === "1-7") payout = b["1-7"] * PAYOUT["1-7"];
    if (zone === "0") payout = b["0"] * PAYOUT["0"];
    if (zone === "8-14") payout = b["8-14"] * PAYOUT["8-14"];
    if (totalBet > 0) setWinDelta(payout - totalBet);
    setBalance((prev) => prev + payout);
    setBets({ "1-7": 0, "0": 0, "8-14": 0 });
  }, []);

  // Fetch server state on mount
  useEffect(() => {
    let cancelled = false;
    fetch(`${STATE_API}/state`)
      .then((res) => res.json())
      .then((data: { nextRollAt?: number; history?: number[] }) => {
        if (cancelled) return;
        const next = data.nextRollAt ?? null;
        const hist = Array.isArray(data.history) ? data.history : [];
        setServerNextRollAt(next);
        setServerHistory(hist);
        setCurrentRoll(hist[0] ?? null);
        setCountdown(
          next != null ? Math.max(0, (next - Date.now()) / 1000) : 0,
        );
      })
      .catch(() => {
        if (!cancelled) setServerNextRollAt(Date.now() + ROLL_INTERVAL_MS);
      })
      .finally(() => {
        if (!cancelled) setStateLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const startSpin = useCallback(
    (result: number) => {
      // Start from wherever the strip currently is — no mode-switch jump
      const startPos = spinPositionRef.current;
      const landingIndex = findVirtualLanding(result, startPos);

      setIsSpinning(true);
      setShowWinReveal(false);
      setWinDelta(null);
      spinStartRef.current = performance.now();

      const tick = (now: number) => {
        const elapsed = now - spinStartRef.current;
        const t = Math.min(elapsed / SPIN_DURATION_MS, 1);
        const position = startPos + easeOutCubic(t) * (landingIndex - startPos);
        setSpinPosition(position);

        if (t < 1) {
          rafRef.current = requestAnimationFrame(tick);
          return;
        }

        cancelAnimationFrame(rafRef.current);
        setSpinPosition(landingIndex);
        setCurrentRoll(result);
        resolveRoll(result);
        setShowWinReveal(true);
        setIsSpinning(false);

        if (winRevealTimeoutRef.current)
          clearTimeout(winRevealTimeoutRef.current);
        winRevealTimeoutRef.current = window.setTimeout(() => {
          winRevealTimeoutRef.current = null;
          setShowWinReveal(false);
          setWinDelta(null);
          const pending = pendingServerStateRef.current;
          if (pending) {
            setServerNextRollAt(pending.nextRollAt);
            setServerHistory(pending.history);
            setCountdown(Math.max(0, (pending.nextRollAt - Date.now()) / 1000));
            pendingServerStateRef.current = null;
          }
        }, WIN_REVEAL_MS);
      };

      rafRef.current = requestAnimationFrame(tick);
    },
    [resolveRoll],
  );

  useEffect(() => {
    return () => {
      cancelAnimationFrame(rafRef.current);
      if (winRevealTimeoutRef.current)
        clearTimeout(winRevealTimeoutRef.current);
    };
  }, []);

  // Countdown + trigger roll when 0
  useEffect(() => {
    if (stateLoading || isSpinning || showWinReveal || serverNextRollAt == null)
      return;

    const interval = setInterval(() => {
      const remaining = (serverNextRollAt - Date.now()) / 1000;
      setCountdown(Math.max(0, remaining));

      if (remaining <= 0) {
        setServerNextRollAt(null);
        fetch(`${STATE_API}/roll`, { method: "POST" })
          .then((res) => {
            if (res.status === 429) {
              return fetch(`${STATE_API}/state`).then((r) => r.json());
            }
            return res.json();
          })
          .then(
            (data: {
              result?: number;
              nextRollAt?: number;
              history?: number[];
            }) => {
              if (
                data.result != null &&
                data.nextRollAt != null &&
                Array.isArray(data.history)
              ) {
                pendingServerStateRef.current = {
                  nextRollAt: data.nextRollAt,
                  history: data.history,
                };
                startSpin(data.result);
              } else if (data.nextRollAt != null) {
                setServerNextRollAt(data.nextRollAt);
                if (Array.isArray(data.history)) setServerHistory(data.history);
              } else {
                setServerNextRollAt(Date.now() + ROLL_INTERVAL_MS);
              }
            },
          )
          .catch(() => {
            setServerNextRollAt(Date.now() + ROLL_INTERVAL_MS);
          });
      }
    }, 100);

    return () => clearInterval(interval);
  }, [stateLoading, isSpinning, showWinReveal, serverNextRollAt, startSpin]);

  const placeBet = (zone: Zone) => {
    if (isSpinning) return;
    const amount = Math.min(betAmount, balance - totalPlaced);
    if (amount <= 0) return;
    setBalance((b) => b - amount);
    setBets((prev) => ({ ...prev, [zone]: prev[zone] + amount }));
    setLastBetAmount(amount);
  };

  const clearBets = () => {
    if (isSpinning) return;
    setBalance((b) => b + totalPlaced);
    setBets({ "1-7": 0, "0": 0, "8-14": 0 });
  };

  // Virtual strip: render a window of VISIBLE_HALF cells on each side of spinPosition
  const centerCell = Math.floor(spinPosition);
  const fracOffset = spinPosition - centerCell; // sub-cell scroll amount (0–1)
  const firstVirtual = centerCell - VISIBLE_HALF;

  const canBet =
    !isSpinning && betAmount > 0 && balance - totalPlaced >= betAmount;
  const countdownPct = serverNextRollAt
    ? Math.min(100, (countdown / (ROLL_INTERVAL_MS / 1000)) * 100)
    : 0;

  return (
    <div className="space-y-4">
      {/* Status bar */}
      <div
        className={`card overflow-hidden transition-colors duration-300 ${
          showWinReveal && currentRoll !== null
            ? zoneRevealClass(currentRoll)
            : "border-dark-700"
        }`}
      >
        <div className="px-4 pb-2 pt-4 text-center">
          {isSpinning && (
            <p className="text-lg font-semibold text-dark-300">
              <span className="mr-2 inline-block animate-spin">⟳</span>
              Spinning…
            </p>
          )}
          {showWinReveal && currentRoll !== null && (
            <p className="text-xl font-bold">
              CSGODouble rolled{" "}
              <span className="text-2xl font-extrabold">{currentRoll}</span>!
            </p>
          )}
          {!isSpinning && !showWinReveal && (
            <p className="text-lg font-semibold text-dark-50">
              {stateLoading ? (
                <span className="text-dark-400">Loading…</span>
              ) : (
                <>
                  Rolling in{" "}
                  <span className="font-mono text-lotus-400">
                    {countdown.toFixed(1)}
                  </span>
                  s
                </>
              )}
            </p>
          )}
        </div>
        <div className="mx-4 mb-3 h-1 overflow-hidden rounded-full bg-dark-700">
          <div
            className={`h-full rounded-full transition-[width] duration-100 ${
              isSpinning
                ? "w-0"
                : showWinReveal
                  ? "w-full bg-amber-500"
                  : "bg-lotus-500"
            }`}
            style={
              !isSpinning && !showWinReveal
                ? { width: `${countdownPct}%` }
                : undefined
            }
          />
        </div>
      </div>

      {/* Roulette track — single virtual strip, no mode switching */}
      <div className="card overflow-hidden p-2">
        <div
          className="relative mx-auto flex w-full max-w-3xl items-center justify-center overflow-hidden py-2"
          style={{
            minHeight: `${CELL_STEP_REM + 0.5}rem`,
            maskImage:
              "linear-gradient(to right, transparent 0%, black 12%, black 88%, transparent 100%)",
            WebkitMaskImage:
              "linear-gradient(to right, transparent 0%, black 12%, black 88%, transparent 100%)",
          }}
        >
          {/* Fixed center pointer */}
          <div
            className="absolute left-1/2 top-0 z-10 w-0.5 -translate-x-1/2 rounded-full bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.9)]"
            style={{ height: `${CELL_STEP_REM - 0.125}rem`, top: "0.25rem" }}
            aria-hidden
          />
          {/*
           * justify-center naturally centers the flex row in the container.
           * Shifting by -fracOffset moves the strip left by the sub-cell fraction
           * so that the exact spinPosition (not just Math.floor) stays under the pointer.
           */}
          <div
            className="flex gap-0.5 will-change-transform"
            style={{
              transform: `translateX(${-fracOffset * CELL_STEP_REM}rem)`,
              transition: "none",
            }}
          >
            {Array.from({ length: VISIBLE_HALF * 2 + 1 }, (_, k) => {
              const virtualIndex = firstVirtual + k;
              const n = virtualCell(virtualIndex);
              return (
                <div
                  key={virtualIndex}
                  className={`flex flex-shrink-0 items-center justify-center rounded text-sm font-bold ${cellColor(n)}`}
                  style={{
                    width: `${CELL_STEP_REM - 0.125}rem`,
                    height: `${CELL_STEP_REM - 0.125}rem`,
                  }}
                >
                  {n}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* History: newest rightmost, slightly larger with ring */}
      <div className="flex flex-wrap justify-center gap-2">
        {Array.from({ length: HISTORY_LENGTH }).map((_, displayIndex) => {
          const value =
            serverHistory[HISTORY_LENGTH - 1 - displayIndex] ?? null;
          const isNewest =
            displayIndex === HISTORY_LENGTH - 1 && value !== null;
          const colorClass =
            value === null
              ? "bg-dark-600 text-dark-500"
              : value === GREEN_NUMBER
                ? "bg-emerald-600 text-white"
                : value <= 7
                  ? "bg-red-600 text-white"
                  : "bg-zinc-900 text-zinc-100";
          return (
            <div
              key={displayIndex}
              className={`flex items-center justify-center rounded-full text-sm font-bold transition-all ${colorClass} ${
                isNewest
                  ? "h-[3rem] w-[3rem] ring-2 ring-amber-400 ring-offset-1 ring-offset-dark-900"
                  : "h-[2.625rem] w-[2.625rem]"
              }`}
            >
              {value ?? "—"}
            </div>
          );
        })}
      </div>

      {/* Balance and bet controls */}
      <div className="card p-6">
        <div className="mb-4 flex items-end justify-between">
          <div>
            <p className="text-sm text-dark-400">Balance</p>
            <p className="text-2xl font-bold text-dark-50">${balance}</p>
          </div>
          {winDelta !== null && (
            <p
              className={`text-lg font-bold ${
                winDelta > 0
                  ? "text-emerald-400"
                  : winDelta < 0
                    ? "text-red-400"
                    : "text-dark-400"
              }`}
            >
              {winDelta > 0
                ? `+$${winDelta}`
                : winDelta < 0
                  ? `-$${Math.abs(winDelta)}`
                  : "Push"}
            </p>
          )}
        </div>

        <div className="mb-4 flex flex-wrap items-center gap-2">
          <input
            type="number"
            min={0}
            max={balance}
            value={betInput}
            onChange={(e) => setBetInput(e.target.value.replace(/[^0-9]/g, ""))}
            className="input-primary w-24"
            placeholder="0"
          />
          {[
            { label: "Clear", getValue: () => "" },
            { label: "Last", getValue: () => String(lastBetAmount) },
            ...[1, 10, 100, 1000].map((n) => ({
              label: `+${n}`,
              getValue: () => String(Math.max(0, betAmount + n)),
            })),
            { label: "1/2", getValue: () => String(Math.floor(betAmount / 2)) },
            { label: "x2", getValue: () => String(betAmount * 2) },
            {
              label: "Max",
              getValue: () => String(Math.max(0, balance - totalPlaced)),
            },
          ].map(({ label, getValue }) => (
            <button
              key={label}
              type="button"
              onClick={() => setBetInput(getValue())}
              className={BET_BUTTON_CLASS}
            >
              {label}
            </button>
          ))}
        </div>

        {totalPlaced > 0 && !isSpinning && (
          <button
            type="button"
            onClick={clearBets}
            className="mb-4 text-sm text-red-400 hover:text-red-300"
          >
            Clear all bets (refund)
          </button>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {(
            [
              {
                zone: "1-7" as Zone,
                label: "1 to 7",
                multiplier: "2x",
                className:
                  "bg-red-600/90 text-white hover:bg-red-500 disabled:hover:bg-red-600/90",
              },
              {
                zone: "0" as Zone,
                label: "0",
                multiplier: "14x",
                className:
                  "bg-emerald-600/90 text-white hover:bg-emerald-500 disabled:hover:bg-emerald-600/90",
              },
              {
                zone: "8-14" as Zone,
                label: "8 to 14",
                multiplier: "2x",
                className:
                  "bg-zinc-900 text-zinc-100 hover:bg-zinc-800 disabled:hover:bg-zinc-900 border border-zinc-700",
              },
            ] as const
          ).map(({ zone, label, multiplier, className }) => (
            <button
              key={zone}
              type="button"
              onClick={() => placeBet(zone)}
              disabled={!canBet}
              className={`flex flex-col items-center justify-center rounded-xl p-6 font-bold transition disabled:opacity-50 ${className}`}
            >
              <span>{label}</span>
              <span className="mt-1 text-sm opacity-90">{multiplier}</span>
              <span className="mt-2 text-sm">Your bet: ${bets[zone]}</span>
            </button>
          ))}
        </div>

        <p className="mt-4 text-center text-sm text-dark-500">
          Total placed this round: ${totalPlaced}
        </p>
      </div>
    </div>
  );
}
