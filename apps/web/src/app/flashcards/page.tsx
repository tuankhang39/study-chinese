"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { api, Card, Decks, speakZh } from "@/lib/api";
import { flashcardsHref, topicIcon, topicLabel } from "@/lib/topics";

function dismissKey() {
  return `daily-review-dismissed-${new Date().toISOString().slice(0, 10)}`;
}

function StudySession({
  title,
  subtitle,
  cards,
  loading,
  error,
  busy,
  idx,
  flipped,
  onFlip,
  onRate,
  onBack,
  onSpeak,
}: {
  title: string;
  subtitle: string;
  cards: Card[];
  loading: boolean;
  error: string;
  busy: boolean;
  idx: number;
  flipped: boolean;
  onFlip: () => void;
  onRate: (r: "again" | "hard" | "good" | "easy") => void;
  onBack: () => void;
  onSpeak: (hanzi: string) => void;
}) {
  const card = cards[idx];

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <button type="button" className="text-sm text-[var(--muted)] hover:text-[var(--accent)]" onClick={onBack}>
            ← Quay lại bộ thẻ
          </button>
          <h1 className="font-display mt-1 text-3xl">{title}</h1>
          <p className="text-sm text-[var(--muted)]">
            {subtitle}
            {card ? ` · ${idx + 1}/${cards.length}` : ""}
          </p>
        </div>
        {card && (
          <button className="btn btn-ghost" onClick={() => onSpeak(card.vocab.hanzi)}>
            Nghe
          </button>
        )}
      </div>

      {error && <p className="text-[var(--danger)]">{error}</p>}
      {loading && <p className="text-sm text-[var(--muted)]">Đang tải…</p>}

      {!loading && !card && !error && (
        <div className="card-panel p-8 text-center">
          <h2 className="font-display text-2xl">Đã xong bộ này</h2>
          <p className="mt-2 text-[var(--muted)]">Từ đã ôn được lưu vào Từ vựng đã học.</p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            <button type="button" className="btn btn-primary" onClick={onBack}>
              Chọn bộ khác
            </button>
            <Link href="/vocab/learned" className="btn btn-ghost">
              Xem từ đã học
            </Link>
          </div>
        </div>
      )}

      {card && (
        <>
          <button
            type="button"
            className="card-panel w-full min-h-[280px] p-8 text-center transition hover:shadow-lg"
            onClick={onFlip}
          >
            {!flipped ? (
              <>
                <p className="font-zh text-6xl font-medium tracking-wide">{card.vocab.hanzi}</p>
                <p className="mt-4 text-xl text-[var(--muted)]">{card.vocab.pinyin}</p>
                {card.vocab.topic && (
                  <p className="mt-4 text-xs font-medium text-[var(--orange-dark)]">
                    {topicIcon(card.vocab.topic)} {topicLabel(card.vocab.topic)}
                  </p>
                )}
                <p className="mt-8 text-sm text-[var(--muted)]">Chạm để xem nghĩa</p>
              </>
            ) : (
              <>
                <p className="text-2xl font-medium">{card.vocab.meaning_vi}</p>
                {card.vocab.example_zh && (
                  <div className="mt-6 text-left">
                    <p className="font-zh text-lg">{card.vocab.example_zh}</p>
                    <p className="text-sm text-[var(--muted)]">{card.vocab.example_vi}</p>
                  </div>
                )}
              </>
            )}
          </button>

          <div className="grid grid-cols-4 gap-2">
            {(
              [
                ["again", "Again", "bg-red-50 text-red-700"],
                ["hard", "Hard", "bg-amber-50 text-amber-800"],
                ["good", "Good", "bg-emerald-50 text-emerald-800"],
                ["easy", "Easy", "bg-sky-50 text-sky-800"],
              ] as const
            ).map(([key, label, cls]) => (
              <button
                key={key}
                disabled={busy}
                onClick={() => onRate(key)}
                className={`rounded-xl px-2 py-3 text-sm font-semibold ${cls}`}
              >
                {label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function FlashcardsInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const mode = searchParams.get("mode");
  const levelParam = searchParams.get("hsk_level");
  const topicParam = searchParams.get("topic") || undefined;
  const level = levelParam ? Number(levelParam) : undefined;
  const hskLevel = level && [1, 2, 3].includes(level) ? level : undefined;
  const studying = Boolean(topicParam) || mode === "daily";

  const [decks, setDecks] = useState<Decks | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [dismissedDaily, setDismissedDaily] = useState(false);

  useEffect(() => {
    try {
      setDismissedDaily(localStorage.getItem(dismissKey()) === "1");
    } catch {
      setDismissedDaily(false);
    }
  }, []);

  const loadDecks = useCallback(async () => {
    try {
      setDecks(await api.cardDecks());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải bộ thẻ");
    }
  }, []);

  const loadStudy = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data =
        mode === "daily"
          ? await api.dailyReviewCards(5)
          : await api.dueCards({
              hsk_level: hskLevel,
              topic: topicParam,
              limit: 40,
            });
      setCards(data);
      setIdx(0);
      setFlipped(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải thẻ");
    } finally {
      setLoading(false);
    }
  }, [mode, hskLevel, topicParam]);

  useEffect(() => {
    if (studying) {
      loadStudy();
    } else {
      setLoading(true);
      loadDecks().finally(() => setLoading(false));
    }
  }, [studying, loadStudy, loadDecks]);

  async function rate(rating: "again" | "hard" | "good" | "easy") {
    const card = cards[idx];
    if (!card || busy) return;
    setBusy(true);
    try {
      await api.reviewCard(card.id, rating);
      if (idx + 1 >= cards.length) {
        setCards([]);
        setIdx(0);
        if (mode !== "daily") await loadDecks();
      } else {
        setIdx((i) => i + 1);
        setFlipped(false);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi ôn thẻ");
    } finally {
      setBusy(false);
    }
  }

  const selectedHsk = useMemo(
    () => decks?.hsk.find((h) => h.hsk_level === hskLevel) || null,
    [decks, hskLevel]
  );

  const showDailyBanner = Boolean(decks?.daily_review_ready && !dismissedDaily && !studying);

  if (studying) {
    const title = mode === "daily" ? "Ôn 5 từ gần nhất" : topicParam ? topicLabel(topicParam) : "Flashcard";
    const subtitle =
      mode === "daily"
        ? "Random từ đã học ≥ 1 ngày"
        : `HSK ${hskLevel || "?"} · ${topicParam ? topicLabel(topicParam) : ""}`;
    return (
      <StudySession
        title={title}
        subtitle={subtitle}
        cards={cards}
        loading={loading}
        error={error}
        busy={busy}
        idx={idx}
        flipped={flipped}
        onFlip={() => setFlipped((f) => !f)}
        onRate={rate}
        onBack={() =>
          router.push(
            mode === "daily" ? "/flashcards" : flashcardsHref({ hsk_level: hskLevel })
          )
        }
        onSpeak={speakZh}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl">Flashcard</h1>
          <p className="text-[var(--muted)]">
            Chọn cấp HSK → chủ đề → học thẻ. Đã học: {decks?.learned_total ?? 0} từ
          </p>
        </div>
        <Link href="/vocab/learned" className="btn btn-ghost text-sm">
          Từ vựng đã học
        </Link>
      </div>

      {showDailyBanner && (
        <div className="card-panel flex flex-wrap items-center justify-between gap-3 border-[var(--orange)] bg-[var(--accent-soft)] p-4">
          <div>
            <p className="font-semibold text-[var(--navy)]">Đến lúc ôn lại</p>
            <p className="text-sm text-[var(--muted)]">
              Random {decks?.daily_review_count || 5} từ đã học gần nhất (≥ 1 ngày). Bạn có thể bỏ qua
              và ôn sau.
            </p>
          </div>
          <div className="flex gap-2">
            <Link href={flashcardsHref({ mode: "daily" })} className="btn btn-primary">
              Ôn ngay
            </Link>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                try {
                  localStorage.setItem(dismissKey(), "1");
                } catch {
                  /* ignore */
                }
                setDismissedDaily(true);
              }}
            >
              Để sau
            </button>
          </div>
        </div>
      )}

      {error && <p className="text-[var(--danger)]">{error}</p>}
      {loading && <p className="text-sm text-[var(--muted)]">Đang tải…</p>}

      {!loading && !hskLevel && (
        <div className="grid gap-4 sm:grid-cols-3">
          {(decks?.hsk || []).map((h) => (
            <button
              key={h.hsk_level}
              type="button"
              onClick={() => router.push(flashcardsHref({ hsk_level: h.hsk_level }))}
              className="card-panel p-5 text-left transition hover:-translate-y-0.5 hover:border-[var(--accent)]"
            >
              <p className="text-xs font-bold uppercase tracking-wide text-[var(--muted)]">Cấp độ</p>
              <h2 className="font-display mt-1 text-2xl text-[var(--navy)]">HSK {h.hsk_level}</h2>
              <p className="mt-3 text-sm text-[var(--muted)]">
                {h.learned}/{h.total} đã học · {h.topics.length} chủ đề
              </p>
              <div className="progress-bar mt-3">
                <div
                  className="progress-fill"
                  style={{ width: `${h.total ? Math.round((100 * h.learned) / h.total) : 0}%` }}
                />
              </div>
            </button>
          ))}
        </div>
      )}

      {!loading && hskLevel && selectedHsk && (
        <div className="space-y-4">
          <button
            type="button"
            className="text-sm text-[var(--muted)] hover:text-[var(--accent)]"
            onClick={() => router.push("/flashcards")}
          >
            ← Tất cả HSK
          </button>
          <h2 className="font-display text-2xl text-[var(--navy)]">HSK {hskLevel} · Chủ đề</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {selectedHsk.topics.map((t) => (
              <button
                key={t.topic}
                type="button"
                onClick={() =>
                  router.push(flashcardsHref({ hsk_level: hskLevel, topic: t.topic }))
                }
                className="card-panel p-4 text-left transition hover:-translate-y-0.5 hover:border-[var(--accent)]"
              >
                <p className="text-lg">
                  {topicIcon(t.topic)} {topicLabel(t.topic)}
                </p>
                <p className="mt-2 text-sm text-[var(--muted)]">
                  {t.learned}/{t.total} đã học
                </p>
                <div className="progress-bar mt-2">
                  <div
                    className="progress-fill"
                    style={{ width: `${t.total ? Math.round((100 * t.learned) / t.total) : 0}%` }}
                  />
                </div>
                <p className="mt-3 text-xs font-bold uppercase text-[var(--orange)]">Bắt đầu ôn →</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {!loading && hskLevel && !selectedHsk && (
        <p className="text-sm text-[var(--muted)]">Không có chủ đề cho HSK {hskLevel}.</p>
      )}
    </div>
  );
}

export default function FlashcardsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-[var(--muted)]">Đang tải…</p>}>
      <FlashcardsInner />
    </Suspense>
  );
}
