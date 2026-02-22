import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, Sparkles, BookOpen, Shuffle } from "lucide-react";

// 
// 一句话阅读 Demo（纯前端可预览）
// - 入口是一句话（高亮放大）
// - 上下文半透明保留
// - 纵向刷：从任何一句话开始读
// 

const MOCK_BOOKS = [
  {
    id: "b1",
    title: "The Unnamed Book",
    author: "Anonymous",
    passages: [
      {
        id: "b1-p1",
        lines: [
          "I used to think a beginning had to be polite.",
          "But the mind begins where it trembles.",
          "A sentence can be a door you didn't know you needed.",
          "So I stopped looking for chapter one.",
          "I started looking for the line that looked back at me."
        ],
        focus: 2
      },
      {
        id: "b1-p2",
        lines: [
          "You don't lack discipline.",
          "You lack a place to return to yourself.",
          "Read slowly until your body agrees.",
          "The page is not a task list.",
          "It is a climate." 
        ],
        focus: 1
      },
      {
        id: "b1-p3",
        lines: [
          "If a book feels far, don't chase it.",
          "Let one line come close.",
          "Hold it like a warm coin.",
          "Walk around with it in your pocket.",
          "Then open the rest when you're ready." 
        ],
        focus: 2
      },
      {
        id: "b1-p4",
        lines: [
          "Sometimes the truth arrives as a small irritation.",
          "A sentence you can't swipe away.",
          "Not because it's correct.",
          "Because it's precise.",
          "Because it names what you didn't dare to name." 
        ],
        focus: 1
      }
    ]
  },
  {
    id: "b2",
    title: "Notes on Becoming",
    author: "K.M.",
    passages: [
      {
        id: "b2-p1",
        lines: [
          "There are days you are functional but not present.",
          "Your calendar is full, your self is missing.",
          "The remedy is not more effort.",
          "It's a quieter kind of honesty.",
          "One sentence at a time." 
        ],
        focus: 4
      },
      {
        id: "b2-p2",
        lines: [
          "A useful question is not: What should I do?",
          "But: What is asking to be felt?",
          "Language is a handle on the unsaid.",
          "When the handle appears, take it.",
          "That is how reading becomes life." 
        ],
        focus: 2
      },
      {
        id: "b2-p3",
        lines: [
          "Do not worship clarity.",
          "Clarity is sometimes a defence.",
          "Let the page remain slightly foggy.",
          "Move inside the fog with care.",
          "Meaning will condense when you're kind." 
        ],
        focus: 3
      }
    ]
  }
];

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    if (!mq) return;
    const onChange = () => setReduced(!!mq.matches);
    onChange();
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);
  return reduced;
}

function GlassButton({ icon: Icon, children, onClick, title }) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="group inline-flex items-center gap-2 rounded-2xl border border-white/15 bg-white/10 px-3 py-2 text-sm text-white/90 shadow-[0_12px_40px_rgba(0,0,0,0.25)] backdrop-blur-xl transition hover:bg-white/15 active:scale-[0.99]"
    >
      {Icon ? (
        <Icon className="h-4 w-4 text-white/80 transition group-hover:text-white" />
      ) : null}
      <span className="whitespace-nowrap">{children}</span>
    </button>
  );
}

function ReadingCard({ passage, book, showMeta = true }) {
  const focus = passage.focus;
  const lines = passage.lines;

  return (
    <div className="relative mx-auto w-full max-w-[760px] px-6">
      {/* soft halo */}
      <div className="pointer-events-none absolute -inset-6 rounded-[32px] bg-gradient-to-b from-white/10 via-white/0 to-white/10 blur-2xl" />

      <div className="relative overflow-hidden rounded-[32px] border border-white/15 bg-white/8 p-6 shadow-[0_18px_70px_rgba(0,0,0,0.35)] backdrop-blur-xl">
        {showMeta ? (
          <div className="mb-5 flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-white/70">
                <BookOpen className="h-4 w-4" />
                <span className="truncate text-sm">{book.title}</span>
              </div>
              <div className="mt-1 truncate text-xs text-white/45">{book.author}</div>
            </div>
            <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white/60">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Start anywhere</span>
            </div>
          </div>
        ) : null}

        {/* lines */}
        <div className="space-y-3">
          {lines.map((t, idx) => {
            const dist = Math.abs(idx - focus);
            const isFocus = idx === focus;

            // transparency curve for context
            const opacity = isFocus ? 1 : dist === 1 ? 0.55 : dist === 2 ? 0.25 : 0.14;

            return (
              <div
                key={idx}
                className={
                  "leading-relaxed tracking-[0.01em] " +
                  (isFocus
                    ? "text-[22px] sm:text-[26px] font-semibold text-white"
                    : "text-[15px] sm:text-[16px] font-medium text-white")
                }
                style={{ opacity }}
              >
                {isFocus ? (
                  <span className="relative inline">
                    <span className="absolute -inset-x-2 -inset-y-1 -z-10 rounded-2xl bg-white/10" />
                    {t}
                  </span>
                ) : (
                  t
                )}
              </div>
            );
          })}
        </div>

        {/* bottom hint */}
        <div className="mt-7 flex items-center justify-between">
          <div className="text-xs text-white/40">Scroll ↓ to expand the context</div>
          <div className="text-xs text-white/40">Scroll ↑ to rewind</div>
        </div>
      </div>
    </div>
  );
}

function BookPill({ active, title, onClick }) {
  return (
    <button
      onClick={onClick}
      className={
        "rounded-full px-4 py-2 text-sm transition " +
        (active
          ? "bg-white/16 text-white border border-white/20"
          : "bg-white/6 text-white/70 border border-white/10 hover:bg-white/10")
      }
    >
      <span className="truncate">{title}</span>
    </button>
  );
}

export default function OneLineReaderDemo() {
  const prefersReducedMotion = usePrefersReducedMotion();

  const [bookId, setBookId] = useState(MOCK_BOOKS[0].id);
  const book = useMemo(() => MOCK_BOOKS.find((b) => b.id === bookId) || MOCK_BOOKS[0], [bookId]);

  const [index, setIndex] = useState(0);
  const [seed, setSeed] = useState(0); // for shuffle animation key

  const maxIdx = book.passages.length - 1;

  // Reset reading position on book switch
  useEffect(() => {
    setIndex(0);
    setSeed((s) => s + 1);
  }, [bookId]);

  const go = (delta) => {
    setIndex((i) => clamp(i + delta, 0, maxIdx));
  };

  const shuffleStart = () => {
    const next = Math.floor(Math.random() * (maxIdx + 1));
    setIndex(next);
    setSeed((s) => s + 1);
  };

  // Wheel to navigate (vertical swipe feel)
  const wheelLock = useRef(false);
  const onWheel = (e) => {
    if (wheelLock.current) return;
    const dy = e.deltaY;
    if (Math.abs(dy) < 18) return;
    wheelLock.current = true;
    if (dy > 0) go(1);
    else go(-1);
    window.setTimeout(() => (wheelLock.current = false), 520);
  };

  // Keyboard support
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "ArrowDown" || e.key === "j") go(1);
      if (e.key === "ArrowUp" || e.key === "k") go(-1);
      if (e.key === " ") {
        e.preventDefault();
        shuffleStart();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [maxIdx]);

  const passage = book.passages[index];

  return (
    <div
      className="min-h-screen w-full bg-[#070912] text-white"
      onWheel={onWheel}
    >
      {/* background */}
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute -left-24 -top-24 h-[520px] w-[520px] rounded-full bg-white/10 blur-[90px]" />
        <div className="absolute -right-20 top-24 h-[540px] w-[540px] rounded-full bg-white/8 blur-[110px]" />
        <div className="absolute bottom-[-180px] left-1/2 h-[700px] w-[700px] -translate-x-1/2 rounded-full bg-white/6 blur-[140px]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.08),transparent_45%),radial-gradient(circle_at_80%_30%,rgba(255,255,255,0.06),transparent_50%),radial-gradient(circle_at_50%_90%,rgba(255,255,255,0.05),transparent_55%)]" />
        <div className="absolute inset-0 opacity-[0.05] [background-image:linear-gradient(to_right,rgba(255,255,255,0.2)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.2)_1px,transparent_1px)] [background-size:42px_42px]" />
      </div>

      {/* top bar */}
      <div className="relative mx-auto flex max-w-[980px] items-center justify-between px-6 pt-8">
        <div>
          <div className="text-sm text-white/55">一句话阅读 · Demo</div>
          <div className="mt-1 text-lg font-semibold tracking-tight">从任何一句话开始读一本书</div>
        </div>

        <div className="hidden items-center gap-2 sm:flex">
          <GlassButton icon={Shuffle} onClick={shuffleStart} title="随机从一句话开始（Space）">
            随机开始
          </GlassButton>
          <GlassButton icon={ChevronUp} onClick={() => go(-1)} title="上一段（↑ / k）">
            上一段
          </GlassButton>
          <GlassButton icon={ChevronDown} onClick={() => go(1)} title="下一段（↓ / j）">
            下一段
          </GlassButton>
        </div>
      </div>

      {/* book switch */}
      <div className="relative mx-auto mt-5 max-w-[980px] px-6">
        <div className="flex flex-wrap gap-2">
          {MOCK_BOOKS.map((b) => (
            <BookPill
              key={b.id}
              title={b.title}
              active={b.id === bookId}
              onClick={() => setBookId(b.id)}
            />
          ))}
        </div>
        <div className="mt-2 text-xs text-white/40">提示：滚轮上下刷 / ↑↓ 键 / j k；按 Space 随机从一句话开始。</div>
      </div>

      {/* main */}
      <div className="relative flex min-h-[calc(100vh-220px)] items-center justify-center px-2 py-10">
        <AnimatePresence mode="wait">
          <motion.div
            key={`${book.id}-${passage.id}-${seed}`}
            initial={prefersReducedMotion ? { opacity: 0 } : { opacity: 0, y: 18, filter: "blur(6px)" }}
            animate={prefersReducedMotion ? { opacity: 1 } : { opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={prefersReducedMotion ? { opacity: 0 } : { opacity: 0, y: -12, filter: "blur(6px)" }}
            transition={{ duration: prefersReducedMotion ? 0.12 : 0.42, ease: [0.2, 0.8, 0.2, 1] }}
            className="w-full"
          >
            <ReadingCard passage={passage} book={book} />
          </motion.div>
        </AnimatePresence>

        {/* mobile controls */}
        <div className="fixed bottom-6 left-1/2 z-10 flex -translate-x-1/2 gap-2 sm:hidden">
          <GlassButton icon={ChevronUp} onClick={() => go(-1)} title="上一段">
            上一段
          </GlassButton>
          <GlassButton icon={Shuffle} onClick={shuffleStart} title="随机开始">
            随机
          </GlassButton>
          <GlassButton icon={ChevronDown} onClick={() => go(1)} title="下一段">
            下一段
          </GlassButton>
        </div>
      </div>

      {/* footer */}
      <div className="relative mx-auto max-w-[980px] px-6 pb-10">
        <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-xs text-white/55 backdrop-blur-xl">
          <span>
            当前位置：<span className="text-white/80">{index + 1}</span> / {book.passages.length}
          </span>
          <span className="hidden sm:inline">核心交互：一句话高亮 + 上下文半透明 + 纵向刷动</span>
          <span className="sm:hidden">上下刷动</span>
        </div>
      </div>
    </div>
  );
}
