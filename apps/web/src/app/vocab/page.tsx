"use client";

import { useEffect, useState } from "react";
import { api, Vocab, speakZh } from "@/lib/api";

export default function VocabPage() {
  const [level, setLevel] = useState<number | undefined>(1);
  const [q, setQ] = useState("");
  const [items, setItems] = useState<Vocab[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .vocab({ hsk_level: level, q: q || undefined })
      .then(setItems)
      .catch((e) => setError(e.message));
  }, [level, q]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl">Từ vựng HSK</h1>
        <p className="text-[var(--muted)]">Danh sách theo cấp · nghĩa tiếng Việt</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {[1, 2, 3].map((n) => (
          <button
            key={n}
            onClick={() => setLevel(n)}
            className={`rounded-full px-3 py-1.5 text-sm ${
              level === n ? "bg-[var(--accent)] text-white" : "border border-[var(--line)]"
            }`}
          >
            HSK {n}
          </button>
        ))}
        <button
          onClick={() => setLevel(undefined)}
          className={`rounded-full px-3 py-1.5 text-sm ${
            level === undefined ? "bg-[var(--accent)] text-white" : "border border-[var(--line)]"
          }`}
        >
          Tất cả
        </button>
        <input
          className="input max-w-xs"
          placeholder="Tìm hanzi / pinyin / nghĩa"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>
      {error && <p className="text-[var(--danger)]">{error}</p>}
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((v) => (
          <button
            key={v.id}
            className="card-panel p-4 text-left transition hover:-translate-y-0.5"
            onClick={() => speakZh(v.hanzi)}
          >
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-zh text-3xl">{v.hanzi}</span>
              <span className="text-xs text-[var(--muted)]">HSK {v.hsk_level}</span>
            </div>
            <p className="mt-1 text-[var(--muted)]">{v.pinyin}</p>
            <p className="mt-2">{v.meaning_vi}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
