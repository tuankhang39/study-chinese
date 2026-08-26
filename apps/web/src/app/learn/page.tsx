"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Course } from "@/lib/api";

export default function LearnHubPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/login";
      return;
    }
    api
      .catalog()
      .then(setCourses)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="relative min-h-[calc(100vh-8rem)] overflow-hidden">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 20%, #f7931e 0, transparent 40%), radial-gradient(circle at 80% 0%, #002060 0, transparent 35%)",
        }}
      />
      <div className="relative mx-auto max-w-6xl space-y-8 p-4 md:p-8">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <Link href="/home" className="text-xs font-semibold text-[var(--muted)] hover:text-[var(--orange)]">
              ← Trang chủ
            </Link>
            <h1 className="font-display mt-2 text-4xl font-bold uppercase tracking-tight text-[var(--navy)] md:text-5xl">
              Khóa HSK
            </h1>
            <p className="mt-2 max-w-xl text-[var(--muted)]">
              Chọn cấp độ · học theo bước (từ → câu → hội thoại → luyện) · nghe phát âm từng card
            </p>
          </div>
          <Link href="/learn/hsk/1" className="btn btn-primary shadow-lg">
            Vào HSK 1 ngay
          </Link>
        </header>

        {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {courses.map((c) => {
            const soon = c.coming_soon && !c.published;
            const pct = c.progress_percent ?? 0;
            const card = (
              <article
                className={`group relative overflow-hidden rounded-md border border-[var(--line)] bg-white shadow-md transition ${
                  soon ? "opacity-70" : "hover:-translate-y-1 hover:border-[var(--orange)] hover:shadow-xl"
                }`}
              >
                <div className="flex h-36 items-center justify-center bg-gradient-to-br from-[var(--navy)] to-[#003399]">
                  <span className="font-display text-5xl font-bold tracking-wide text-white">
                    HSK {c.hsk_level}
                  </span>
                </div>
                <div className="space-y-3 p-4">
                  <p className="font-display text-lg font-bold uppercase text-[var(--navy)]">{c.title}</p>
                  <p className="line-clamp-2 text-sm text-[var(--muted)]">{c.description || c.title_en}</p>
                  {!soon ? (
                    <>
                      <div className="h-2 overflow-hidden rounded-full bg-[var(--bg-soft)]">
                        <div
                          className="h-full rounded-full bg-[var(--orange)] transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span className="text-[var(--muted)]">{c.lesson_count ?? 0} bài</span>
                        <span className="text-[var(--navy)]">{pct}% hoàn thành</span>
                      </div>
                      <span className="btn btn-navy w-full text-xs">Vào học →</span>
                    </>
                  ) : (
                    <p className="rounded-sm bg-[var(--bg-soft)] px-3 py-2 text-center text-xs font-bold uppercase text-[var(--muted)]">
                      Sắp mở
                    </p>
                  )}
                </div>
              </article>
            );
            if (soon) return <div key={c.id}>{card}</div>;
            return (
              <Link key={c.id} href={`/learn/hsk/${c.hsk_level}`}>
                {card}
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
