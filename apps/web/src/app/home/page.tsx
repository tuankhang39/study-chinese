"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, HomeData } from "@/lib/api";

const floatingChars = "学读写听说工作";

const quickModules = [
  {
    href: "/flashcards",
    title: "Flashcard FSRS",
    desc: "Ôn thẻ đến hạn — nhớ lâu, quên chậm.",
    count: "Hôm nay",
    icon: "卡",
    accent: "orange" as const,
  },
  {
    href: "/vocab",
    title: "Từ vựng HSK",
    desc: "Danh sách theo cấp, nghe TTS từng từ.",
    count: "600+ từ",
    icon: "词",
    accent: "navy" as const,
  },
  {
    href: "/listening",
    title: "Listening",
    desc: "Nghe và chọn nghĩa đúng.",
    count: "Luyện tai",
    icon: "听",
    accent: "navy" as const,
  },
  {
    href: "/work",
    title: "AI Roleplay",
    desc: "Nói chuyện với sếp / khách — AI chấm điểm.",
    count: "5 tình huống",
    icon: "AI",
    accent: "orange" as const,
  },
];

export default function HomePage() {
  const [data, setData] = useState<HomeData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .home()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="text-[var(--danger)]">{error}</p>;
  if (!data) return <p className="text-[var(--muted)]">Đang tải…</p>;

  const { user, mission, due_count, tip } = data;
  const doneCount = mission.tasks.filter((t) => t.done).length;

  return (
    <div className="space-y-10">
      {/* Hero — cùng layout trang chủ */}
      <section className="relative overflow-hidden rounded-sm bg-gradient-to-br from-[var(--bg-soft)] via-white to-[var(--accent-soft)] p-6 md:p-10">
        <div className="hero-zh-watermark pointer-events-none absolute inset-0 select-none" aria-hidden>
          {floatingChars.split("").map((ch, i) => (
            <span
              key={i}
              className="font-zh absolute text-[var(--navy)] opacity-[0.05]"
              style={{
                fontSize: `${40 + (i % 4) * 20}px`,
                top: `${(i * 19) % 80}%`,
                left: `${(i * 27) % 85}%`,
                transform: `rotate(${(i % 5) * 10 - 15}deg)`,
              }}
            >
              {ch}
            </span>
          ))}
        </div>

        <div className="relative grid gap-8 md:grid-cols-2 md:items-center">
          <div>
            <span className="badge-pill">Bảng điều khiển học tập</span>
            <h1 className="font-display mt-4 text-3xl font-bold uppercase leading-tight text-[var(--navy)] md:text-4xl">
              Hôm nay học gì,
              <br />
              <span className="text-[var(--orange)]">{user.display_name}?</span>
            </h1>
            <p className="mt-4 max-w-md text-[var(--muted)]">
              Hoàn thành nhiệm vụ hôm nay để giữ streak và mở khóa XP. Còn{" "}
              <strong className="text-[var(--navy)]">{due_count} thẻ</strong> đang chờ ôn.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/flashcards" className="btn btn-primary">
                Tiếp tục học
              </Link>
              <Link href="/work" className="btn btn-navy">
                Luyện hội thoại
              </Link>
            </div>
          </div>

          {/* Preview card — giống landing */}
          <div className="relative mx-auto w-full max-w-sm">
            <div className="hero-preview-card">
              <div className="rounded-sm border-2 border-[var(--navy)] bg-white p-5 shadow-xl">
                <p className="text-center text-xs font-bold uppercase text-[var(--muted)]">Tiến độ hôm nay</p>
                <p className="font-zh mt-2 text-center text-4xl font-bold text-[var(--navy)]">学习</p>
                <p className="text-center text-sm text-[var(--orange)]">xuéxí · học tập</p>
                <div className="mt-4 grid grid-cols-3 gap-2">
                  {[
                    { label: "Streak", value: `${user.streak}d` },
                    { label: "XP", value: String(user.xp) },
                    { label: "Level", value: String(user.level) },
                  ].map((s) => (
                    <div
                      key={s.label}
                      className="rounded-sm border border-[var(--line)] bg-[var(--bg-soft)] px-2 py-2 text-center"
                    >
                      <p className="font-display text-lg font-bold text-[var(--orange)]">{s.value}</p>
                      <p className="text-[10px] font-semibold uppercase text-[var(--muted)]">{s.label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="absolute -bottom-3 -left-3 -z-10 h-16 w-16 bg-[var(--navy)]" />
            <div className="absolute -right-2 -top-2 -z-10 h-12 w-12 bg-[var(--orange)]" />
          </div>
        </div>
      </section>

      {/* Nhiệm vụ — style feature card header */}
      <section>
        <div className="mb-5 flex items-end justify-between gap-4">
          <div>
            <span className="badge-pill badge-pill-outline">Nhiệm vụ hôm nay</span>
            <h2 className="font-display mt-3 text-2xl font-bold uppercase text-[var(--navy)]">
              {doneCount}/{mission.tasks.length} hoàn thành
            </h2>
          </div>
          {mission.completed && (
            <span className="rounded-sm bg-[var(--orange)] px-3 py-1.5 text-xs font-bold uppercase text-white">
              Perfect Day!
            </span>
          )}
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {mission.tasks.map((t) => (
            <div
              key={t.id}
              className={`overflow-hidden rounded-sm border bg-white shadow-sm ${
                t.done ? "border-[var(--orange)]" : "border-[var(--line)]"
              }`}
            >
              <div
                className={`px-4 py-2 text-xs font-bold uppercase text-white ${
                  t.done ? "bg-[var(--orange)]" : "bg-[var(--navy)]"
                }`}
              >
                +{t.xp} XP · {t.progress}/{t.target}
              </div>
              <div className="p-4">
                <p className={`font-medium ${t.done ? "text-[var(--muted)] line-through" : "text-[var(--ink)]"}`}>
                  {t.title}
                </p>
                <div className="progress-bar mt-3">
                  <div
                    className="progress-fill"
                    style={{ width: `${Math.min(100, (t.progress / t.target) * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Quick modules — giống grid trang chủ */}
      <section>
        <span className="badge-pill badge-pill-outline">Tiếp tục học</span>
        <h2 className="font-display mt-3 text-2xl font-bold uppercase text-[var(--navy)]">Chọn chuyên mục</h2>
        <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {quickModules.map((m) => (
            <Link
              key={m.title}
              href={m.href}
              className="feature-card group flex flex-col overflow-hidden rounded-sm border border-[var(--line)] bg-white shadow-sm transition hover:-translate-y-1 hover:border-[var(--orange)] hover:shadow-lg"
            >
              <div
                className={`flex h-14 items-center justify-between px-4 ${
                  m.accent === "orange" ? "bg-[var(--orange)]" : "bg-[var(--navy)]"
                }`}
              >
                <span className="font-zh text-2xl font-bold text-white/90">{m.icon}</span>
                <span className="text-xs font-bold uppercase tracking-wide text-white/80">{m.count}</span>
              </div>
              <div className="flex flex-1 flex-col p-4">
                <h3 className="font-display text-base font-bold uppercase text-[var(--navy)] group-hover:text-[var(--orange-dark)]">
                  {m.title}
                </h3>
                <p className="mt-2 flex-1 text-sm text-[var(--muted)]">{m.desc}</p>
                <span className="mt-4 text-xs font-bold uppercase text-[var(--orange)]">Vào học →</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* AI Teacher band */}
      <section className="overflow-hidden rounded-sm bg-[var(--navy)] p-6 text-white md:p-8">
        <p className="text-xs font-bold uppercase tracking-wide text-[var(--orange)]">AI Teacher</p>
        <p className="mt-3 max-w-2xl text-lg leading-relaxed text-white/90">{tip}</p>
        <Link href="/listening" className="btn btn-primary mt-5">
          Luyện ngay
        </Link>
      </section>
    </div>
  );
}
