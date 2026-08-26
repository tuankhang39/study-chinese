"use client";

import { FormEvent, useEffect, useState } from "react";
import { Modal } from "@/components/admin/Modal";
import { ADMIN_PAGE_SIZE, Pagination } from "@/components/admin/Pagination";
import { api, Vocab } from "@/lib/api";

const blank = {
  hanzi: "",
  pinyin: "",
  meaning_vi: "",
  meaning_en: "",
  hsk_level: 1,
  traditional: "",
  example_zh: "",
  example_vi: "",
};

export default function AdminVocabPage() {
  const [items, setItems] = useState<Vocab[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [hsk, setHsk] = useState<number | "">("");
  const [page, setPage] = useState(1);
  const [form, setForm] = useState(blank);
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<Vocab | null>(null);
  const [error, setError] = useState("");

  async function load(p = page) {
    const res = await api.admin.vocab({
      q: q || undefined,
      hsk_level: hsk === "" ? undefined : hsk,
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
      await api.admin.createVocab({
        hanzi: form.hanzi,
        pinyin: form.pinyin,
        meaning_vi: form.meaning_vi,
        meaning_en: form.meaning_en || undefined,
        hsk_level: form.hsk_level,
        traditional: form.traditional || undefined,
        example_zh: form.example_zh || undefined,
        example_vi: form.example_vi || undefined,
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
      await api.admin.updateVocab(editing.id, {
        hanzi: editing.hanzi,
        pinyin: editing.pinyin,
        meaning_vi: editing.meaning_vi,
        meaning_en: editing.meaning_en,
        hsk_level: editing.hsk_level,
        traditional: editing.traditional,
        example_zh: editing.example_zh,
        example_vi: editing.example_vi,
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
          <h1 className="font-display text-3xl font-bold uppercase text-[var(--navy)]">Từ vựng</h1>
          <p className="text-[var(--muted)]">CRUD HSK</p>
        </div>
        <button type="button" className="btn btn-primary text-xs" onClick={() => setCreateOpen(true)}>
          + Thêm từ
        </button>
      </div>

      <div className="card-panel flex flex-wrap gap-2 p-3">
        <input className="input max-w-xs" placeholder="Tìm" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="input max-w-[8rem]" value={hsk} onChange={(e) => setHsk(e.target.value ? Number(e.target.value) : "")}>
          <option value="">HSK</option>
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
        <button className="btn btn-navy text-xs" type="button" onClick={() => load(1).catch((e) => setError(e.message))}>
          Tìm
        </button>
      </div>
      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

      <div className="overflow-x-auto card-panel">
        <table className="w-full min-w-[700px] text-left text-sm">
          <thead className="border-b border-[var(--line)] bg-[var(--bg-soft)]">
            <tr>
              <th className="p-3 font-semibold uppercase tracking-wide text-[var(--muted)]">Hanzi</th>
              <th className="p-3 font-semibold uppercase tracking-wide text-[var(--muted)]">Pinyin</th>
              <th className="p-3 font-semibold uppercase tracking-wide text-[var(--muted)]">Nghĩa</th>
              <th className="p-3 font-semibold uppercase tracking-wide text-[var(--muted)]">HSK</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {items.map((v) => (
              <tr key={v.id} className="border-b border-[var(--line)] hover:bg-[var(--accent-soft)]/40">
                <td className="p-3 font-zh text-xl">{v.hanzi}</td>
                <td className="p-3">{v.pinyin}</td>
                <td className="p-3">{v.meaning_vi}</td>
                <td className="p-3">{v.hsk_level}</td>
                <td className="space-x-2 p-3 text-right">
                  <button type="button" className="font-semibold text-[var(--orange)]" onClick={() => setEditing({ ...v })}>
                    Sửa
                  </button>
                  <button
                    type="button"
                    className="text-[var(--danger)]"
                    onClick={async () => {
                      if (!confirm("Xóa từ này?")) return;
                      await api.admin.deleteVocab(v.id);
                      await load(page);
                    }}
                  >
                    Xóa
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageSize={ADMIN_PAGE_SIZE} total={total} onChange={(p) => load(p)} />

      <Modal open={createOpen} title="Thêm từ vựng" onClose={() => setCreateOpen(false)} wide>
        <form onSubmit={onCreate} className="grid gap-3 md:grid-cols-3">
          <input className="input" placeholder="Hanzi" required value={form.hanzi} onChange={(e) => setForm({ ...form, hanzi: e.target.value })} />
          <input className="input" placeholder="Pinyin" required value={form.pinyin} onChange={(e) => setForm({ ...form, pinyin: e.target.value })} />
          <input className="input" type="number" min={1} max={6} value={form.hsk_level} onChange={(e) => setForm({ ...form, hsk_level: Number(e.target.value) })} />
          <input className="input md:col-span-2" placeholder="Nghĩa VI" required value={form.meaning_vi} onChange={(e) => setForm({ ...form, meaning_vi: e.target.value })} />
          <input className="input" placeholder="Nghĩa EN" value={form.meaning_en} onChange={(e) => setForm({ ...form, meaning_en: e.target.value })} />
          <div className="md:col-span-3 mt-2 flex justify-end gap-2">
            <button className="btn btn-ghost" type="button" onClick={() => setCreateOpen(false)}>
              Hủy
            </button>
            <button className="btn btn-primary" type="submit">
              Thêm
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={!!editing} title={editing ? `Sửa #${editing.id}` : "Sửa"} onClose={() => setEditing(null)}>
        {editing && (
          <form onSubmit={onSave} className="grid gap-3">
            <input className="input" value={editing.hanzi} onChange={(e) => setEditing({ ...editing, hanzi: e.target.value })} />
            <input className="input" value={editing.pinyin} onChange={(e) => setEditing({ ...editing, pinyin: e.target.value })} />
            <input className="input" value={editing.meaning_vi} onChange={(e) => setEditing({ ...editing, meaning_vi: e.target.value })} />
            <input className="input" type="number" value={editing.hsk_level} onChange={(e) => setEditing({ ...editing, hsk_level: Number(e.target.value) })} />
            <div className="mt-2 flex justify-end gap-2">
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
