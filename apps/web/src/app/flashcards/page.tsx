"use client";

import { useEffect, useState } from "react";
import { api, Card } from "@/lib/api";
import { speakZh } from "@/lib/api";

export default function FlashcardsPage() {
  const [cards, setCards] = useState<Card[]>([]);
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const data = await api.dueCards();
      setCards(data);
      setIdx(0);
      setFlipped(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải thẻ");
    }
  }

  useEffect(() => {
    load();
  }, []);

  const card = cards[idx];

  async function rate(rating: "again" | "hard" | "good" | "easy") {
    if (!card || busy) return;
    setBusy(true);
    try {
      await api.reviewCard(card.id, rating);
      if (idx + 1 >= cards.length) {
        await load();
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

  if (error) return <p className="text-[var(--danger)]">{error}</p>;
  if (!card) {
    return (
      <div className="card-panel p-8 text-center">
        <h1 className="font-display text-3xl">Hết thẻ đến hạn</h1>
        <p className="mt-2 text-[var(--muted)]">Quay lại sau hoặc học Listening / Đi làm.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Flashcard</h1>
          <p className="text-sm text-[var(--muted)]">
            {idx + 1}/{cards.length} · HSK {card.vocab.hsk_level}
          </p>
        </div>
        <button className="btn btn-ghost" onClick={() => speakZh(card.vocab.hanzi)}>
          Nghe
        </button>
      </div>

      <button
        type="button"
        className="card-panel w-full min-h-[280px] p-8 text-center transition hover:shadow-lg"
        onClick={() => setFlipped((f) => !f)}
      >
        {!flipped ? (
          <>
            <p className="font-zh text-6xl font-medium tracking-wide">{card.vocab.hanzi}</p>
            <p className="mt-4 text-xl text-[var(--muted)]">{card.vocab.pinyin}</p>
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
            onClick={() => rate(key)}
            className={`rounded-xl px-2 py-3 text-sm font-semibold ${cls}`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
