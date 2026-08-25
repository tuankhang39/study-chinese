"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, RoleplaySession } from "@/lib/api";

export default function RoleplayPage() {
  const params = useParams<{ id: string }>();
  const scenarioId = Number(params.id);
  const [session, setSession] = useState<RoleplaySession | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!scenarioId) return;
    api
      .startRoleplay(scenarioId)
      .then(setSession)
      .catch((e) => setError(e.message));
  }, [scenarioId]);

  async function onSend(e: FormEvent) {
    e.preventDefault();
    if (!session || !message.trim()) return;
    setLoading(true);
    setError("");
    try {
      const updated = await api.sendRoleplay(session.id, message.trim());
      setSession(updated);
      setMessage("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi AI");
    } finally {
      setLoading(false);
    }
  }

  if (error && !session) return <p className="text-[var(--danger)]">{error}</p>;
  if (!session) return <p className="text-[var(--muted)]">Đang mở tình huống…</p>;

  return (
    <div className="mx-auto grid max-w-4xl gap-6 lg:grid-cols-[1.4fr_1fr]">
      <section className="card-panel flex min-h-[60vh] flex-col p-5">
        <h1 className="font-display text-2xl">AI Roleplay</h1>
        <div className="mt-4 flex-1 space-y-3 overflow-y-auto">
          {session.messages.map((m, i) => (
            <div
              key={i}
              className={`rounded-2xl px-4 py-3 ${
                m.role === "user" ? "ml-8 bg-[var(--accent-soft)]" : "mr-8 bg-white border border-[var(--line)]"
              }`}
            >
              <p className="font-zh text-lg">{m.zh}</p>
              {m.vi && <p className="mt-1 text-sm text-[var(--muted)]">{m.vi}</p>}
            </div>
          ))}
        </div>
        <form onSubmit={onSend} className="mt-4 flex gap-2">
          <input
            className="input"
            placeholder="Trả lời bằng tiếng Trung…"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
          <button className="btn btn-primary" disabled={loading}>
            {loading ? "…" : "Gửi"}
          </button>
        </form>
        {error && <p className="mt-2 text-sm text-[var(--danger)]">{error}</p>}
      </section>

      <aside className="card-panel h-fit p-5">
        <h2 className="font-display text-xl">Chấm điểm</h2>
        {session.scores ? (
          <div className="mt-4 space-y-3 text-sm">
            <Score label="Ngữ pháp" value={session.scores.grammar} />
            <Score label="Từ vựng" value={session.scores.vocabulary} />
            <Score label="Tự nhiên" value={session.scores.naturalness} />
            {session.scores.corrected_zh && (
              <div className="rounded-xl bg-[var(--bg)] p-3">
                <p className="text-xs text-[var(--muted)]">Gợi ý sửa</p>
                <p className="font-zh mt-1 text-base">{session.scores.corrected_zh}</p>
                {session.scores.corrected_vi && (
                  <p className="mt-1 text-[var(--muted)]">{session.scores.corrected_vi}</p>
                )}
              </div>
            )}
            {session.scores.feedback_vi && (
              <p className="text-[var(--muted)]">{session.scores.feedback_vi}</p>
            )}
          </div>
        ) : (
          <p className="mt-3 text-sm text-[var(--muted)]">Gửi câu trả lời để nhận điểm.</p>
        )}
      </aside>
    </div>
  );
}

function Score({ label, value }: { label: string; value?: number }) {
  return (
    <div>
      <div className="mb-1 flex justify-between">
        <span>{label}</span>
        <span>{value ?? "—"}/100</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-[var(--line)]">
        <div
          className="h-full rounded-full bg-[var(--accent)]"
          style={{ width: `${Math.max(0, Math.min(100, value ?? 0))}%` }}
        />
      </div>
    </div>
  );
}
