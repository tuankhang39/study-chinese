"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Pagination } from "@/components/admin/Pagination";
import { api, Vocab, VocabTopic, speakZh } from "@/lib/api";
import { flashcardsHref, topicIcon, topicLabel } from "@/lib/topics";

const PAGE_SIZE = 24;

export default function VocabPage() {
  const [level, setLevel] = useState<number | undefined>(1);
  const [topic, setTopic] = useState<string | undefined>(undefined);
  const [q, setQ] = useState("");
  const [items, setItems] = useState<Vocab[]>([]);
  const [topics, setTopics] = useState<VocabTopic[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);

  // Topic tabs depend only on the selected HSK level (not on search text).
  useEffect(() => {
    api
      .vocabTopics(level)
      .then((rows) => setTopics(rows.sort((a, b) => b.count - a.count)))
      .catch((e) => setError(e.message));
  }, [level]);

  useEffect(() => {
    setLoading(true);
    api
      .vocab({ hsk_level: level, topic, q: q || undefined })
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [level, topic, q]);

  // Reset to page 1 whenever the filtered result set changes.
  useEffect(() => {
    setPage(1);
  }, [level, topic, q]);

  const totalForLevel = useMemo(() => topics.reduce((sum, t) => sum + t.count, 0), [topics]);
  const pageItems = useMemo(
    () => items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [items, page]
  );
  const studyHref = topic
    ? flashcardsHref({ hsk_level: level, topic })
    : flashcardsHref({ hsk_level: level });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl">Từ vựng HSK</h1>
          <p className="text-[var(--muted)]">
            Danh sách theo cấp · nghĩa tiếng Việt · {items.length} từ
            {totalForLevel ? ` (tổng ${totalForLevel} từ ở cấp này)` : ""}
          </p>
        </div>
        <Link href={studyHref} className="btn btn-primary shrink-0">
          {topic ? `Ôn flashcard · ${topicLabel(topic)}` : level ? `Flashcard HSK ${level}` : "Flashcard"}
        </Link>
      </div>

      <div className="flex flex-wrap gap-2">
        {[1, 2, 3].map((n) => (
          <button
            key={n}
            onClick={() => {
              setLevel(n);
              setTopic(undefined);
            }}
            className={`rounded-full px-3 py-1.5 text-sm font-semibold transition ${
              level === n ? "bg-[var(--accent)] text-white" : "border border-[var(--line)] hover:border-[var(--accent)]"
            }`}
          >
            HSK {n}
          </button>
        ))}
        <button
          onClick={() => {
            setLevel(undefined);
            setTopic(undefined);
          }}
          className={`rounded-full px-3 py-1.5 text-sm font-semibold transition ${
            level === undefined ? "bg-[var(--accent)] text-white" : "border border-[var(--line)] hover:border-[var(--accent)]"
          }`}
        >
          Tất cả cấp
        </button>
        <input
          className="input max-w-xs"
          placeholder="Tìm hanzi / pinyin / nghĩa"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {topics.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setTopic(undefined)}
            className={`shrink-0 rounded-full px-3 py-1.5 text-sm font-medium transition ${
              topic === undefined
                ? "bg-[var(--navy)] text-white"
                : "bg-[var(--bg-soft)] text-[var(--muted)] hover:bg-[var(--accent-soft)]"
            }`}
          >
            🗂️ Tất cả chủ đề
          </button>
          {topics.map((t) => (
            <div key={t.topic} className="flex shrink-0 items-center gap-1">
              <button
                onClick={() => setTopic(t.topic === topic ? undefined : t.topic)}
                className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
                  topic === t.topic
                    ? "bg-[var(--navy)] text-white"
                    : "bg-[var(--bg-soft)] text-[var(--muted)] hover:bg-[var(--accent-soft)]"
                }`}
              >
                {topicIcon(t.topic)} {topicLabel(t.topic)} · {t.count}
              </button>
              <Link
                href={flashcardsHref({ hsk_level: level, topic: t.topic })}
                title={`Ôn flashcard: ${topicLabel(t.topic)}`}
                className="rounded-full border border-[var(--line)] px-2 py-1.5 text-xs font-semibold text-[var(--muted)] transition hover:border-[var(--accent)] hover:text-[var(--accent)]"
              >
                Thẻ
              </Link>
            </div>
          ))}
        </div>
      )}

      {error && <p className="text-[var(--danger)]">{error}</p>}
      {loading && <p className="text-sm text-[var(--muted)]">Đang tải…</p>}

      {!loading && items.length === 0 && !error && (
        <p className="text-sm text-[var(--muted)]">Không có từ nào khớp bộ lọc.</p>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {pageItems.map((v) => (
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
            {v.topic && (
              <p className="mt-2 text-xs font-medium text-[var(--orange-dark)]">
                {topicIcon(v.topic)} {topicLabel(v.topic)}
              </p>
            )}
          </button>
        ))}
      </div>

      {items.length > PAGE_SIZE && (
        <Pagination page={page} pageSize={PAGE_SIZE} total={items.length} onChange={setPage} />
      )}
    </div>
  );
}
