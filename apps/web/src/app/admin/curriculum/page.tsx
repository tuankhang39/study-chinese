"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Modal } from "@/components/admin/Modal";
import { api, Course } from "@/lib/api";

const blankCourse = {
  slug: "",
  title: "",
  title_en: "",
  description: "",
  hsk_level: 1,
  published: true,
  coming_soon: false,
  sort_order: 0,
};

export default function AdminCurriculumCoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [error, setError] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<Course | null>(null);
  const [form, setForm] = useState(blankCourse);
  const [busy, setBusy] = useState(false);

  async function load() {
    const res = await api.admin.curriculumCourses({ page: 1, page_size: 100 });
    setCourses(res.items);
  }

  useEffect(() => {
    load().catch((e) => setError(e instanceof Error ? e.message : "Lỗi tải"));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.admin.createCurriculumCourse({
        slug: form.slug.trim(),
        title: form.title.trim(),
        title_en: form.title_en.trim() || null,
        description: form.description,
        hsk_level: Number(form.hsk_level),
        published: form.published,
        coming_soon: form.coming_soon,
        sort_order: Number(form.sort_order),
        cover_image_url: null,
      });
      setCreateOpen(false);
      setForm(blankCourse);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không tạo được");
    } finally {
      setBusy(false);
    }
  }

  async function onSave(e: FormEvent) {
    e.preventDefault();
    if (!editing) return;
    setBusy(true);
    setError("");
    try {
      await api.admin.updateCurriculumCourse(editing.id, {
        slug: editing.slug,
        title: editing.title,
        title_en: editing.title_en ?? null,
        description: editing.description,
        hsk_level: editing.hsk_level,
        published: editing.published,
        coming_soon: !!editing.coming_soon,
        sort_order: editing.sort_order,
        cover_image_url: null,
      });
      setEditing(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không lưu được");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(c: Course) {
    if (!confirm(`Xóa giáo trình “${c.title}”? Toàn bộ bài học sẽ bị xóa.`)) return;
    try {
      await api.admin.deleteCurriculumCourse(c.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không xóa được");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold uppercase text-[var(--navy)]">Giáo trình</h1>
          <p className="text-[var(--muted)]">Chọn khóa HSK → bài học → bước → card</p>
        </div>
        <button
          type="button"
          className="btn btn-primary text-xs"
          onClick={() => {
            setForm({ ...blankCourse, sort_order: courses.length + 1 });
            setCreateOpen(true);
          }}
        >
          + Giáo trình
        </button>
      </div>

      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {courses.map((c) => (
          <article
            key={c.id}
            className="group relative overflow-hidden rounded-md border border-[var(--line)] bg-white shadow-sm transition hover:border-[var(--orange)] hover:shadow-md"
          >
            <Link href={`/admin/curriculum/course/${c.id}`} className="block">
              <div className="flex h-28 items-center justify-center bg-gradient-to-br from-[var(--navy)] to-[#003399]">
                <span className="font-display text-4xl font-bold tracking-wide text-white">
                  HSK {c.hsk_level}
                </span>
              </div>
              <div className="space-y-2 p-4">
                <p className="font-display text-base font-bold uppercase text-[var(--navy)]">{c.title}</p>
                <p className="text-sm text-[var(--muted)] line-clamp-2">{c.description || c.title_en || c.slug}</p>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="font-semibold text-[var(--navy)]">{c.lesson_count ?? 0} bài</span>
                  {c.published ? (
                    <span className="rounded-sm bg-emerald-50 px-2 py-0.5 font-bold text-emerald-700">Published</span>
                  ) : (
                    <span className="rounded-sm bg-[var(--bg-soft)] px-2 py-0.5 font-bold text-[var(--muted)]">
                      Nháp
                    </span>
                  )}
                  {c.coming_soon && (
                    <span className="rounded-sm bg-[var(--accent-soft)] px-2 py-0.5 font-bold text-[var(--orange-dark)]">
                      Sắp mở
                    </span>
                  )}
                </div>
                <p className="text-xs font-bold uppercase text-[var(--orange)] group-hover:underline">
                  Xem bài học →
                </p>
              </div>
            </Link>
            <div className="flex gap-2 border-t border-[var(--line)] px-4 py-2">
              <button
                type="button"
                className="btn btn-ghost flex-1 px-2 py-1.5 text-xs"
                onClick={() => setEditing(c)}
              >
                Sửa
              </button>
              <button
                type="button"
                className="btn btn-ghost flex-1 px-2 py-1.5 text-xs text-[var(--danger)]"
                onClick={() => onDelete(c)}
              >
                Xóa
              </button>
            </div>
          </article>
        ))}
      </div>

      {courses.length === 0 && !error && (
        <p className="text-sm text-[var(--muted)]">Chưa có giáo trình. Bấm “+ Giáo trình” để tạo.</p>
      )}

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Thêm giáo trình">
        <form className="space-y-3" onSubmit={onCreate}>
          <CourseFields value={form} onChange={setForm} />
          <button className="btn btn-primary w-full text-xs" type="submit" disabled={busy}>
            Tạo
          </button>
        </form>
      </Modal>

      <Modal open={!!editing} onClose={() => setEditing(null)} title="Sửa giáo trình">
        {editing && (
          <form className="space-y-3" onSubmit={onSave}>
            <CourseFields
              value={{
                slug: editing.slug,
                title: editing.title,
                title_en: editing.title_en || "",
                description: editing.description || "",
                hsk_level: editing.hsk_level,
                published: editing.published,
                coming_soon: !!editing.coming_soon,
                sort_order: editing.sort_order,
              }}
              onChange={(v) =>
                setEditing({
                  ...editing,
                  ...v,
                  title_en: v.title_en || null,
                })
              }
            />
            <button className="btn btn-primary w-full text-xs" type="submit" disabled={busy}>
              Lưu
            </button>
          </form>
        )}
      </Modal>
    </div>
  );
}

function CourseFields({
  value,
  onChange,
}: {
  value: typeof blankCourse;
  onChange: (v: typeof blankCourse) => void;
}) {
  return (
    <>
      <label className="block text-xs font-semibold">
        Slug
        <input
          className="input mt-1"
          required
          value={value.slug}
          onChange={(e) => onChange({ ...value, slug: e.target.value })}
          placeholder="hsk1"
        />
      </label>
      <label className="block text-xs font-semibold">
        Tiêu đề
        <input
          className="input mt-1"
          required
          value={value.title}
          onChange={(e) => onChange({ ...value, title: e.target.value })}
        />
      </label>
      <label className="block text-xs font-semibold">
        Title EN
        <input
          className="input mt-1"
          value={value.title_en}
          onChange={(e) => onChange({ ...value, title_en: e.target.value })}
        />
      </label>
      <label className="block text-xs font-semibold">
        Mô tả
        <textarea
          className="input mt-1 min-h-[72px]"
          value={value.description}
          onChange={(e) => onChange({ ...value, description: e.target.value })}
        />
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label className="block text-xs font-semibold">
          HSK level
          <input
            className="input mt-1"
            type="number"
            min={1}
            max={6}
            required
            value={value.hsk_level}
            onChange={(e) => onChange({ ...value, hsk_level: Number(e.target.value) })}
          />
        </label>
        <label className="block text-xs font-semibold">
          Sort
          <input
            className="input mt-1"
            type="number"
            value={value.sort_order}
            onChange={(e) => onChange({ ...value, sort_order: Number(e.target.value) })}
          />
        </label>
      </div>
      <label className="flex items-center gap-2 text-xs font-semibold">
        <input
          type="checkbox"
          checked={value.published}
          onChange={(e) => onChange({ ...value, published: e.target.checked })}
        />
        Published
      </label>
      <label className="flex items-center gap-2 text-xs font-semibold">
        <input
          type="checkbox"
          checked={value.coming_soon}
          onChange={(e) => onChange({ ...value, coming_soon: e.target.checked })}
        />
        Coming soon
      </label>
    </>
  );
}
