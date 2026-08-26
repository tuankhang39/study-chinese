"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AdminDashboard, api } from "@/lib/api";

function StatCard({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: number | string;
  hint?: string;
  tone: "orange" | "navy" | "teal" | "rose";
}) {
  const tones = {
    orange: "from-[#f7931e] to-[#e07d0a]",
    navy: "from-[#002060] to-[#001540]",
    teal: "from-[#0d9488] to-[#0f766e]",
    rose: "from-[#e11d48] to-[#be123c]",
  };
  return (
    <div className={`relative overflow-hidden rounded-sm bg-gradient-to-br ${tones[tone]} p-5 text-white shadow-lg`}>
      <p className="text-xs font-semibold uppercase tracking-wider text-white/75">{label}</p>
      <p className="mt-2 font-display text-3xl font-bold tabular-nums">{value}</p>
      {hint && <p className="mt-1 text-xs text-white/70">{hint}</p>}
      <div className="pointer-events-none absolute -bottom-4 -right-4 h-20 w-20 rounded-full bg-white/10" />
    </div>
  );
}

function BarChart({
  title,
  data,
  color = "var(--orange)",
}: {
  title: string;
  data: { label: string; value: number }[];
  color?: string;
}) {
  const max = Math.max(1, ...data.map((d) => d.value));
  return (
    <div className="card-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-display text-sm font-bold uppercase tracking-wide text-[var(--navy)]">{title}</h2>
      </div>
      {data.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">Chưa có dữ liệu</p>
      ) : (
        <div className="flex h-48 items-end gap-3">
          {data.map((d) => (
            <div key={d.label} className="flex flex-1 flex-col items-center gap-2">
              <span className="text-xs font-semibold text-[var(--navy)]">{d.value}</span>
              <div className="flex w-full flex-1 items-end justify-center">
                <div
                  className="w-full max-w-[48px] rounded-t-sm transition-all"
                  style={{
                    height: `${Math.max(8, (d.value / max) * 100)}%`,
                    background: color,
                  }}
                  title={`${d.label}: ${d.value}`}
                />
              </div>
              <span className="text-[11px] font-medium uppercase text-[var(--muted)]">{d.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ShareList({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data);
  const total = entries.reduce((s, [, v]) => s + v, 0) || 1;
  return (
    <div className="card-panel p-5">
      <h2 className="font-display text-sm font-bold uppercase tracking-wide text-[var(--navy)]">{title}</h2>
      <ul className="mt-4 space-y-3">
        {entries.length === 0 && <li className="text-sm text-[var(--muted)]">—</li>}
        {entries.map(([k, v]) => (
          <li key={k}>
            <div className="mb-1 flex justify-between text-sm">
              <span className="font-medium capitalize">{k}</span>
              <span className="tabular-nums text-[var(--muted)]">
                {v} · {Math.round((v / total) * 100)}%
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-[var(--bg-soft)]">
              <div
                className="h-full rounded-full bg-[var(--orange)]"
                style={{ width: `${(v / total) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function AdminDashboardPage() {
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [curriculum, setCurriculum] = useState<{ courses: number; lessons: number } | null>(null);

  function refresh() {
    setLoading(true);
    api.admin
      .dashboard()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Lỗi"))
      .finally(() => setLoading(false));
    api.admin
      .curriculumCourses({ page: 1, page_size: 100 })
      .then((res) => {
        const lessons = res.items.reduce((n, c) => n + (c.lesson_count ?? 0), 0);
        setCurriculum({ courses: res.total, lessons });
      })
      .catch(() => setCurriculum(null));
  }

  useEffect(() => {
    refresh();
  }, []);

  if (error) return <p className="text-[var(--danger)]">{error}</p>;
  if (loading && !data) return <p className="text-[var(--muted)]">Đang tải thống kê…</p>;
  if (!data) return null;

  const hskBars = Object.entries(data.by_hsk || {})
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([k, v]) => ({ label: `HSK ${k}`, value: v }));

  const planBars = ["free", "pro", "unlimit"].map((k) => ({
    label: k,
    value: data.by_plan[k] || 0,
  }));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold uppercase text-[var(--navy)]">Dashboard</h1>
          <p className="text-[var(--muted)]">Thống kê vận hành · HSK + career Chinese</p>
        </div>
        <div className="flex gap-2">
          <button type="button" className="btn btn-ghost px-3 py-2 text-xs" onClick={refresh}>
            Làm mới
          </button>
          <Link href="/admin/curriculum" className="btn btn-navy px-3 py-2 text-xs">
            Giáo trình
          </Link>
          <Link href="/admin/users" className="btn btn-primary px-3 py-2 text-xs">
            Quản lý user
          </Link>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Users" value={data.users} hint={`+${data.users_new_7d ?? 0} / 7 ngày`} tone="orange" />
        <StatCard label="Từ vựng" value={data.vocab} hint="HSK trong DB" tone="navy" />
        <StatCard label="Gói trả phí" value={data.paid_users ?? 0} hint="pro + unlimit" tone="teal" />
        <StatCard label="Roleplay" value={data.roleplay_sessions ?? 0} hint="Phiên AI" tone="rose" />
      </div>

      <Link
        href="/admin/curriculum"
        className="card-panel flex flex-wrap items-center justify-between gap-4 p-5 transition hover:border-[var(--orange)]"
      >
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-[var(--orange)]">Giáo trình HSK</p>
          <p className="mt-1 font-display text-xl font-bold text-[var(--navy)]">
            {curriculum ? `${curriculum.courses} khóa · ${curriculum.lessons} bài` : "Đang tải…"}
          </p>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Quản lý Course → Lesson → Step → Card (CRUD đầy đủ)
          </p>
        </div>
        <span className="btn btn-primary text-xs">Mở giáo trình →</span>
      </Link>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="card-panel flex items-center justify-between p-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Google login</p>
            <p className="mt-1 font-display text-2xl font-bold text-[var(--navy)]">{data.google_users ?? 0}</p>
          </div>
          <span className="text-2xl opacity-40">G</span>
        </div>
        <div className="card-panel flex items-center justify-between p-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Scenario</p>
            <p className="mt-1 font-display text-2xl font-bold text-[var(--navy)]">{data.scenarios}</p>
          </div>
          <span className="text-2xl opacity-40">☰</span>
        </div>
        <div className="card-panel flex items-center justify-between p-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Thẻ FSRS</p>
            <p className="mt-1 font-display text-2xl font-bold text-[var(--navy)]">{data.user_cards ?? 0}</p>
          </div>
          <span className="text-2xl opacity-40">◇</span>
        </div>
        <div className="card-panel flex items-center justify-between p-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">User mới (7 ngày)</p>
            <p className="mt-1 font-display text-2xl font-bold text-[var(--navy)]">{data.users_new_7d ?? 0}</p>
          </div>
          <span className="text-2xl opacity-40">↑</span>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <BarChart title="Từ vựng theo cấp HSK" data={hskBars} color="var(--navy)" />
        </div>
        <div className="lg:col-span-2">
          <BarChart title="User theo gói" data={planBars} color="var(--orange)" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <ShareList title="Phân bổ gói" data={data.by_plan} />
        <ShareList title="Phân bổ role" data={data.by_role} />
      </div>
    </div>
  );
}
