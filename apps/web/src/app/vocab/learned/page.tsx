"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, LearnedCard, speakZh } from "@/lib/api";
import { flashcardsHref, topicIcon, topicLabel } from "@/lib/topics";

export default function LearnedVocabPage() {
  const [items, setItems] = useState<LearnedCard[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .learnedCards({ limit: 200 })
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl">Từ vựng đã học</h1>
          <p className="text-[var(--muted)]">
            Các từ bạn đã ôn bằng flashcard · {items.length} từ
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/flashcards" className="btn btn-ghost text-sm">
            Bộ flashcard
          </Link>
          <Link href={flashcardsHref({ mode: "daily" })} className="btn btn-primary text-sm">
            Ôn 5 từ gần nhất
          </Link>
        </div>
      </div>

      {error && <p className="text-[var(--danger)]">{error}</p>}
      {loading && <p className="text-sm text-[var(--muted)]">Đang tải…</p>}

      {!loading && items.length === 0 && !error && (
        <div className="card-panel p-8 text-center">
          <h2 className="font-display text-2xl">Chưa có từ nào</h2>
          <p className="mt-2 text-[var(--muted)]">Học flashcard theo chủ đề để lưu từ vào đây.</p>
          <Link href="/flashcards" className="btn btn-primary mt-4">
            Chọn bộ thẻ
          </Link>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((c) => (
          <button
            key={c.id}
            type="button"
            className="card-panel p-4 text-left transition hover:-translate-y-0.5"
            onClick={() => speakZh(c.vocab.hanzi)}
          >
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-zh text-3xl">{c.vocab.hanzi}</span>
              <span className="text-xs text-[var(--muted)]">HSK {c.vocab.hsk_level}</span>
            </div>
            <p className="mt-1 text-[var(--muted)]">{c.vocab.pinyin}</p>
            <p className="mt-2">{c.vocab.meaning_vi}</p>
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-[var(--muted)]">
              {c.vocab.topic && (
                <span className="font-medium text-[var(--orange-dark)]">
                  {topicIcon(c.vocab.topic)} {topicLabel(c.vocab.topic)}
                </span>
              )}
              <span>Ôn {c.reps} lần</span>
              {c.last_review && (
                <span>Gần nhất: {new Date(c.last_review).toLocaleDateString("vi-VN")}</span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
