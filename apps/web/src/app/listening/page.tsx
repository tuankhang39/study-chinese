"use client";

import { useCallback, useEffect, useState } from "react";
import { api, Vocab, speakZh } from "@/lib/api";

type Item = { vocab: Vocab; options: string[]; answer_index: number };

export default function ListeningPage() {
  const [item, setItem] = useState<Item | null>(null);
  const [picked, setPicked] = useState<number | null>(null);
  const [score, setScore] = useState({ correct: 0, total: 0 });
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setPicked(null);
    try {
      const next = await api.listeningNext();
      setItem(next);
      setTimeout(() => speakZh(next.vocab.hanzi), 200);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi listening");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function choose(i: number) {
    if (!item || picked !== null) return;
    setPicked(i);
    const ok = i === item.answer_index;
    setScore((s) => ({ correct: s.correct + (ok ? 1 : 0), total: s.total + 1 }));
    try {
      await api.listeningComplete(ok);
    } catch {
      /* ignore xp errors for UX */
    }
  }

  if (error) return <p className="text-[var(--danger)]">{error}</p>;
  if (!item) return <p className="text-[var(--muted)]">Đang tải…</p>;

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="font-display text-3xl">Listening</h1>
        <p className="text-sm text-[var(--muted)]">
          Nghe TTS (zh-CN) · đúng {score.correct}/{score.total}
        </p>
        <p className="mt-1 text-xs text-[var(--muted)]">
          Audio dùng SpeechSynthesis của trình duyệt — chất lượng phụ thuộc thiết bị.
        </p>
      </div>

      <div className="card-panel p-8 text-center">
        <button className="btn btn-primary" onClick={() => speakZh(item.vocab.hanzi)}>
          Nghe lại
        </button>
        {picked !== null && (
          <p className="font-zh mt-6 text-4xl">{item.vocab.hanzi}</p>
        )}
      </div>

      <div className="grid gap-2">
        {item.options.map((opt, i) => {
          let cls = "card-panel p-4 text-left";
          if (picked !== null) {
            if (i === item.answer_index) cls += " ring-2 ring-emerald-500";
            else if (i === picked) cls += " ring-2 ring-red-400 opacity-70";
          }
          return (
            <button key={opt + i} className={cls} onClick={() => choose(i)} disabled={picked !== null}>
              {opt}
            </button>
          );
        })}
      </div>

      {picked !== null && (
        <button className="btn btn-primary w-full" onClick={load}>
          Câu tiếp
        </button>
      )}
    </div>
  );
}
