"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Modal } from "@/components/admin/Modal";
import { ADMIN_PAGE_SIZE, Pagination } from "@/components/admin/Pagination";
import { api, Course, Lesson } from "@/lib/api";

const LESSON_TYPES = [
  "dialogue_core",
  "survival_phrases",
  "phonics_focus",
  "grammar_focus",
  "review_summary",
  "culture_bonus",
  "workplace_scene",
];

const blankLesson = {
  number: 1,
  title_zh: "",
  title_vi: "",
  title_en: "",
  lesson_type: "dialogue_core",
  estimated_minutes: 12,
  unlock_rule: "sequential",
  published: true,
};

export default function AdminCourseLessonsPage() {
  const params = useParams();
  const courseId = Number(params.courseId);
  const [course, setCourse] = useState<Course | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<Lesson | null>(null);
  const [form, setForm] = useState(blankLesson);
  const [busy, setBusy] = useState(false);

  async function loadCourse() {
    const c = await api.admin.getCurriculumCourse(courseId);
    setCourse(c);
  }

  async function loadLessons(p = 1) {
    const res = await api.admin.curriculumLessons({
      course_id: courseId,
      page: p,
      page_size: ADMIN_PAGE_SIZE,
    });
    setLessons(res.items);
    setTotal(res.total);
    setPage(res.page);
  }

  useEffect(() => {
    if (!courseId) return;
    Promise.all([loadCourse(), loadLessons(1)]).catch((e) =>
      setError(e instanceof Error ? e.message : "Lỗi tải")
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.admin.createCurriculumLesson({
        course_id: courseId,
        number: Number(form.number),
        title_zh: form.title_zh.trim(),
        title_vi: form.title_vi.trim() || null,
        title_en: form.title_en.trim() || null,
        lesson_type: form.lesson_type,
        estimated_minutes: Number(form.estimated_minutes),
        unlock_rule: form.unlock_rule,
        cover_image_url: null,
        published: form.published,
      });
      setCreateOpen(false);
      setForm(blankLesson);
      await loadLessons(1);
      await loadCourse();
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
      await api.admin.updateCurriculumLesson(editing.id, {
        number: editing.number,
        title_zh: editing.title_zh,
        title_vi: editing.title_vi,
        title_en: editing.title_en,
        lesson_type: editing.lesson_type,
        estimated_minutes: editing.estimated_minutes,
        unlock_rule: editing.unlock_rule,
        cover_image_url: null,
        published: editing.published,
      });
      setEditing(null);
      await loadLessons(page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không lưu được");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(L: Lesson) {
    if (!confirm(`Xóa bài ${L.number}: ${L.title_zh}?`)) return;
    try {
      await api.admin.deleteCurriculumLesson(L.id);
      await loadLessons(page);
      await loadCourse();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không xóa được");
    }
  }

  if (!course && !error) return <p className="text-[var(--muted)]">Đang tải…</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <Link href="/admin/curriculum" className="text-xs font-semibold text-[var(--muted)] hover:text-[var(--orange)]">
            ← Giáo trình
          </Link>
          <h1 className="font-display mt-1 text-3xl font-bold uppercase text-[var(--navy)]">
            HSK {course?.hsk_level ?? "—"} · {course?.title}
          </h1>
          <p className="text-sm text-[var(--muted)]">
            {total} bài · slug <code className="text-xs">{course?.slug}</code>
          </p>
        </div>
        <button
          type="button"
          className="btn btn-primary text-xs"
          onClick={() => {
            const nextNum = (lessons.reduce((m, L) => Math.max(m, L.number), 0) || 0) + 1;
            setForm({ ...blankLesson, number: nextNum });
            setCreateOpen(true);
          }}
        >
          + Bài học
        </button>
      </div>

      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

      <div className="overflow-x-auto rounded-md border border-[var(--line)] bg-white shadow-sm">
        <table className="w-full min-w-[860px] text-left text-sm">
          <thead className="border-b border-[var(--line)] bg-[var(--bg-soft)]">
            <tr>
              <th className="p-3">#</th>
              <th className="p-3">Bài</th>
              <th className="p-3">Type</th>
              <th className="p-3">Steps</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {lessons.map((L) => (
              <tr key={L.id} className="border-b border-[var(--line)] hover:bg-[var(--bg-soft)]/50">
                <td className="p-3 font-mono font-semibold">{L.number}</td>
                <td className="p-3">
                  <Link
                    href={`/admin/curriculum/lesson/${L.id}`}
                    className="font-zh text-base font-semibold text-[var(--navy)] hover:text-[var(--orange)]"
                  >
                    {L.title_zh}
                  </Link>
                  {L.title_pinyin && (
                    <p className="text-xs font-medium text-[var(--orange-dark)]">{L.title_pinyin}</p>
                  )}
                  <p className="text-xs text-[var(--muted)]">{L.title_vi || L.title_en}</p>
                </td>
                <td className="p-3 text-xs">{L.lesson_type}</td>
                <td className="p-3">{L.step_count ?? 0}</td>
                <td className="p-3 text-right">
                  <div className="flex flex-wrap justify-end gap-1">
                    <Link
                      className="btn btn-navy px-2 py-1 text-xs"
                      href={`/admin/curriculum/lesson/${L.id}`}
                    >
                      Mở
                    </Link>
                    <Link
                      className="btn btn-ghost px-2 py-1 text-xs"
                      href={`/learn/hsk/${course?.hsk_level ?? 1}/${L.id}`}
                      target="_blank"
                    >
                      Preview
                    </Link>
                    <button type="button" className="btn btn-ghost px-2 py-1 text-xs" onClick={() => setEditing(L)}>
                      Sửa
                    </button>
                    <button
                      type="button"
                      className="btn btn-ghost px-2 py-1 text-xs text-[var(--danger)]"
                      onClick={() => onDelete(L)}
                    >
                      Xóa
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {lessons.length === 0 && (
          <p className="p-6 text-sm text-[var(--muted)]">Chưa có bài. Bấm “+ Bài học”.</p>
        )}
      </div>

      <Pagination
        page={page}
        pageSize={ADMIN_PAGE_SIZE}
        total={total}
        onChange={(p) => loadLessons(p).catch((e) => setError(e.message))}
      />

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Thêm bài học" wide>
        <form className="space-y-3" onSubmit={onCreate}>
          <LessonFields value={form} onChange={setForm} />
          <button className="btn btn-primary w-full text-xs" type="submit" disabled={busy}>
            Tạo
          </button>
        </form>
      </Modal>

      <Modal open={!!editing} onClose={() => setEditing(null)} title="Sửa bài học" wide>
        {editing && (
          <form className="space-y-3" onSubmit={onSave}>
            <LessonFields
              value={{
                number: editing.number,
                title_zh: editing.title_zh,
                title_vi: editing.title_vi || "",
                title_en: editing.title_en || "",
                lesson_type: editing.lesson_type || "dialogue_core",
                estimated_minutes: editing.estimated_minutes ?? 12,
                unlock_rule: editing.unlock_rule || "sequential",
                published: editing.published,
              }}
              onChange={(v) =>
                setEditing({
                  ...editing,
                  ...v,
                  title_vi: v.title_vi || null,
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

function LessonFields({
  value,
  onChange,
}: {
  value: typeof blankLesson;
  onChange: (v: typeof blankLesson) => void;
}) {
  return (
    <>
      <div className="grid grid-cols-2 gap-3">
        <label className="block text-xs font-semibold">
          Số bài
          <input
            className="input mt-1"
            type="number"
            min={1}
            required
            value={value.number}
            onChange={(e) => onChange({ ...value, number: Number(e.target.value) })}
          />
        </label>
        <label className="block text-xs font-semibold">
          Phút ước tính
          <input
            className="input mt-1"
            type="number"
            min={1}
            value={value.estimated_minutes}
            onChange={(e) => onChange({ ...value, estimated_minutes: Number(e.target.value) })}
          />
        </label>
      </div>
      <label className="block text-xs font-semibold">
        Title ZH
        <input
          className="input mt-1 font-zh"
          required
          value={value.title_zh}
          onChange={(e) => onChange({ ...value, title_zh: e.target.value })}
        />
      </label>
      <label className="block text-xs font-semibold">
        Title VI
        <input
          className="input mt-1"
          value={value.title_vi}
          onChange={(e) => onChange({ ...value, title_vi: e.target.value })}
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
      <div className="grid grid-cols-2 gap-3">
        <label className="block text-xs font-semibold">
          Lesson type
          <select
            className="input mt-1"
            value={value.lesson_type}
            onChange={(e) => onChange({ ...value, lesson_type: e.target.value })}
          >
            {LESSON_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-xs font-semibold">
          Unlock
          <select
            className="input mt-1"
            value={value.unlock_rule}
            onChange={(e) => onChange({ ...value, unlock_rule: e.target.value })}
          >
            <option value="sequential">sequential</option>
            <option value="open">open</option>
          </select>
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
    </>
  );
}
