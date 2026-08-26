"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, Lesson } from "@/lib/api";

const TYPE_LABEL: Record<string, string> = {
  dialogue_core: "Hội thoại",
  survival_phrases: "Câu sinh tồn",
  phonics_focus: "Phát âm",
  grammar_focus: "Ngữ pháp",
  review_summary: "Ôn tập",
  culture_bonus: "Văn hóa",
  workplace_scene: "Đi làm",
};

export default function HskLevelPage() {
  const params = useParams();
  const level = Number(params.level);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [error, setError] = useState("");
  const slug = `hsk${level}`;

  useEffect(() => {
    if (!level || level < 1 || level > 6) return;
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/login";
      return;
    }
    api
      .courseLessons(slug)
      .then(setLessons)
      .catch((e) => setError(e.message));
  }, [level, slug]);

  const doneCount = lessons.filter((L) => (L.progress_percent ?? 0) >= 100).length;

  return (
    <div className="relative min-h-[calc(100vh-8rem)]">
      <div className="absolute inset-x-0 top-0 h-48 bg-gradient-to-b from-[#fff4e6] to-transparent" />
      <div className="relative mx-auto max-w-6xl space-y-6 p-4 md:p-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <Link href="/learn" className="text-xs font-semibold text-[var(--muted)] hover:text-[var(--orange)]">
              ← Khóa HSK
            </Link>
            <h1 className="font-display mt-2 text-4xl font-bold uppercase text-[var(--navy)] md:text-5xl">
              HSK {level}
            </h1>
            <p className="mt-1 text-[var(--muted)]">
              {doneCount}/{lessons.length} bài xong · hoàn thành lần lượt để mở khóa bài sau
            </p>
          </div>
          {lessons[0] && !lessons[0].locked && (
            <Link href={`/learn/hsk/${level}/${lessons[0].id}`} className="btn btn-primary">
              {(lessons[0].progress_percent ?? 0) > 0 ? "Tiếp tục bài 1" : "Bắt đầu bài 1"}
            </Link>
          )}
        </div>

        {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

        <div className="grid gap-4 md:grid-cols-2">
          {lessons.map((L) => {
            const locked = !!L.locked;
            const pct = L.progress_percent ?? 0;
            const href = `/learn/hsk/${level}/${L.id}`;
            const inner = (
              <article
                className={`flex h-full gap-4 overflow-hidden rounded-md border bg-white p-4 shadow-sm transition ${
                  locked
                    ? "border-[var(--line)] opacity-65"
                    : "border-[var(--line)] hover:border-[var(--orange)] hover:shadow-lg"
                }`}
              >
                <div className="relative grid h-28 w-20 shrink-0 place-items-center overflow-hidden rounded-sm bg-gradient-to-br from-[var(--navy)] to-[#003399]">
                  <span className="font-display text-center text-sm font-bold leading-tight text-white">
                    HSK
                    <br />
                    {level}
                  </span>
                  <span className="absolute bottom-2 text-xs font-bold text-[var(--orange)]">Bài {L.number}</span>
                  {locked && (
                    <div className="absolute inset-0 grid place-items-center bg-[var(--navy)]/55 text-xs font-bold text-white">
                      KHÓA
                    </div>
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-bold text-[var(--orange)]">Bài {L.number}</span>
                    {L.lesson_type && (
                      <span className="rounded-sm bg-[var(--accent-soft)] px-2 py-0.5 text-[10px] font-bold uppercase text-[var(--orange-dark)]">
                        {TYPE_LABEL[L.lesson_type] || L.lesson_type}
                      </span>
                    )}
                  </div>
                  <h2 className="font-zh mt-1 text-xl font-bold text-[var(--navy)]">{L.title_zh}</h2>
                  {L.title_pinyin && (
                    <p className="text-sm font-medium text-[var(--orange-dark)]">{L.title_pinyin}</p>
                  )}
                  <p className="text-sm text-[var(--muted)]">{L.title_vi || L.title_en}</p>
                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[var(--bg-soft)]">
                    <div className="h-full bg-[var(--orange)]" style={{ width: `${pct}%` }} />
                  </div>
                  <div className="mt-2 flex items-center justify-between gap-2">
                    <p className="text-xs text-[var(--muted)]">
                      ~{L.estimated_minutes ?? 12} phút · {pct}%
                    </p>
                    {!locked && (
                      <span className="text-xs font-bold uppercase text-[var(--navy)]">
                        {pct >= 100 ? "Học lại →" : pct > 0 ? "Tiếp tục →" : "Học ngay →"}
                      </span>
                    )}
                  </div>
                </div>
              </article>
            );
            if (locked) return <div key={L.id}>{inner}</div>;
            return (
              <Link key={L.id} href={href}>
                {inner}
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
