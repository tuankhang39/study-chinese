"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Scenario } from "@/lib/api";

export default function WorkPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [tag, setTag] = useState<string | undefined>();
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .scenarios(tag)
      .then(setScenarios)
      .catch((e) => setError(e.message));
  }, [tag]);

  const tags = ["production", "office", "qc", "sales", "it"];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl">Tiếng Trung đi làm</h1>
        <p className="text-[var(--muted)]">Chọn tình huống · AI đóng vai sếp / khách / đồng nghiệp</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setTag(undefined)}
          className={`rounded-full px-3 py-1.5 text-sm ${
            !tag ? "bg-[var(--accent)] text-white" : "border border-[var(--line)]"
          }`}
        >
          Tất cả
        </button>
        {tags.map((t) => (
          <button
            key={t}
            onClick={() => setTag(t)}
            className={`rounded-full px-3 py-1.5 text-sm capitalize ${
              tag === t ? "bg-[var(--accent)] text-white" : "border border-[var(--line)]"
            }`}
          >
            {t}
          </button>
        ))}
      </div>
      {error && <p className="text-[var(--danger)]">{error}</p>}
      <div className="grid gap-4 md:grid-cols-2">
        {scenarios.map((s) => (
          <Link key={s.id} href={`/work/${s.id}`} className="card-panel block p-6 transition hover:-translate-y-0.5">
            <p className="text-xs uppercase tracking-wide text-[var(--accent)]">{s.job_tag}</p>
            <h2 className="font-display mt-1 text-2xl">{s.title}</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">{s.description}</p>
            <p className="mt-4 text-sm font-medium text-[var(--accent)]">Bắt đầu roleplay →</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
