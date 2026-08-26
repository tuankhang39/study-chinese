"use client";

import { FormEvent, useEffect, useState } from "react";
import { Modal } from "@/components/admin/Modal";
import { ADMIN_PAGE_SIZE, Pagination } from "@/components/admin/Pagination";
import { api, Scenario } from "@/lib/api";

const blank = {
  track: "work",
  job_tag: "",
  title: "",
  description: "",
  prompt_system: "",
  starter_lines: "",
  difficulty: 1,
};

export default function AdminScenariosPage() {
  const [items, setItems] = useState<Scenario[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [form, setForm] = useState(blank);
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<(Scenario & { prompt_system?: string }) | null>(null);
  const [error, setError] = useState("");

  async function load(p = page) {
    const res = await api.admin.scenarios({
      q: q || undefined,
      page: p,
      page_size: ADMIN_PAGE_SIZE,
    });
    setItems(res.items);
    setTotal(res.total);
    setPage(res.page);
  }

  useEffect(() => {
    load(1).catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    try {
      await api.admin.createScenario({
        track: form.track,
        job_tag: form.job_tag || undefined,
        title: form.title,
        description: form.description,
        prompt_system: form.prompt_system,
        starter_lines: form.starter_lines
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean),
        difficulty: form.difficulty,
      });
      setForm(blank);
      setCreateOpen(false);
      await load(1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi");
    }
  }

  async function onSave(e: FormEvent) {
    e.preventDefault();
    if (!editing) return;
    try {
      await api.admin.updateScenario(editing.id, {
        track: editing.track,
        job_tag: editing.job_tag,
        title: editing.title,
        description: editing.description,
        prompt_system: editing.prompt_system,
        starter_lines: editing.starter_lines,
        difficulty: editing.difficulty,
      });
      setEditing(null);
      await load(page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold uppercase text-[var(--navy)]">Scenario</h1>
          <p className="text-[var(--muted)]">CRUD hội thoại / roleplay</p>
        </div>
        <button type="button" className="btn btn-primary text-xs" onClick={() => setCreateOpen(true)}>
          + Thêm scenario
        </button>
      </div>

      <div className="card-panel flex gap-2 p-3">
        <input className="input max-w-sm" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm" />
        <button className="btn btn-navy text-xs" type="button" onClick={() => load(1).catch((e) => setError(e.message))}>
          Tìm
        </button>
      </div>
      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

      <div className="space-y-3">
        {items.map((s) => (
          <div key={s.id} className="card-panel p-4 transition hover:shadow-md">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-semibold text-[var(--navy)]">{s.title}</p>
                <p className="text-xs text-[var(--muted)]">
                  #{s.id} · {s.track} · {s.job_tag || "—"} · độ khó {s.difficulty}
                </p>
                <p className="mt-2 text-sm">{s.description}</p>
              </div>
              <div className="space-x-2">
                <button type="button" className="font-semibold text-[var(--orange)]" onClick={() => setEditing({ ...s })}>
                  Sửa
                </button>
                <button
                  type="button"
                  className="text-[var(--danger)]"
                  onClick={async () => {
                    if (!confirm("Xóa scenario?")) return;
                    await api.admin.deleteScenario(s.id);
                    await load(page);
                  }}
                >
                  Xóa
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      <Pagination page={page} pageSize={ADMIN_PAGE_SIZE} total={total} onChange={(p) => load(p)} />

      <Modal open={createOpen} title="Thêm scenario" onClose={() => setCreateOpen(false)} wide>
        <form onSubmit={onCreate} className="grid gap-3">
          <div className="grid gap-2 md:grid-cols-3">
            <input className="input" placeholder="Track (work/hsk)" value={form.track} onChange={(e) => setForm({ ...form, track: e.target.value })} />
            <input className="input" placeholder="Job tag" value={form.job_tag} onChange={(e) => setForm({ ...form, job_tag: e.target.value })} />
            <input className="input" type="number" min={1} max={5} value={form.difficulty} onChange={(e) => setForm({ ...form, difficulty: Number(e.target.value) })} />
          </div>
          <input className="input" placeholder="Tiêu đề" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <textarea className="input min-h-[70px]" placeholder="Mô tả" required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <textarea className="input min-h-[90px]" placeholder="Prompt system" required value={form.prompt_system} onChange={(e) => setForm({ ...form, prompt_system: e.target.value })} />
          <textarea className="input min-h-[60px]" placeholder="Starter lines (mỗi dòng 1 câu)" value={form.starter_lines} onChange={(e) => setForm({ ...form, starter_lines: e.target.value })} />
          <div className="flex justify-end gap-2">
            <button className="btn btn-ghost" type="button" onClick={() => setCreateOpen(false)}>
              Hủy
            </button>
            <button className="btn btn-primary" type="submit">
              Thêm
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={!!editing} title="Sửa scenario" onClose={() => setEditing(null)} wide>
        {editing && (
          <form onSubmit={onSave} className="grid gap-3">
            <input className="input" value={editing.title} onChange={(e) => setEditing({ ...editing, title: e.target.value })} />
            <textarea className="input min-h-[60px]" value={editing.description} onChange={(e) => setEditing({ ...editing, description: e.target.value })} />
            <textarea
              className="input min-h-[80px]"
              value={editing.prompt_system || ""}
              onChange={(e) => setEditing({ ...editing, prompt_system: e.target.value })}
              placeholder="Prompt system"
            />
            <div className="flex justify-end gap-2">
              <button className="btn btn-ghost" type="button" onClick={() => setEditing(null)}>
                Hủy
              </button>
              <button className="btn btn-primary" type="submit">
                Lưu
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
