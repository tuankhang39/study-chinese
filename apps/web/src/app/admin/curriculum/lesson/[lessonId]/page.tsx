"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { Modal } from "@/components/admin/Modal";
import { api, Course, Lesson, LessonItem, LessonStep, speakZh } from "@/lib/api";

const ITEM_TYPES = [
  "vocab_card",
  "sentence_card",
  "dialogue_line",
  "grammar_tip",
  "quiz_prompt",
  "objective",
  "media",
];

const STEP_KEYS = [
  "objectives",
  "vocab",
  "sentences",
  "dialogue",
  "grammar",
  "practice",
  "review",
  "tongue_twister",
  "complete",
];

const blankItem = {
  item_type: "vocab_card",
  hanzi: "",
  pinyin: "",
  meaning_vi: "",
  meaning_en: "",
  audio_text: "",
  speaker: "",
  sort_order: 0,
  step_id: "" as number | "",
};

const blankStep = {
  step_key: "vocab",
  title_vi: "",
  sort_order: 0,
  required: true,
};

const blankMeta = {
  number: 1,
  title_zh: "",
  title_vi: "",
  title_en: "",
  lesson_type: "dialogue_core",
  estimated_minutes: 12,
  unlock_rule: "sequential",
  published: true,
};

export default function AdminLessonEditorPage() {
  const params = useParams();
  const lessonId = Number(params.lessonId);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [course, setCourse] = useState<Course | null>(null);
  const [selectedStepId, setSelectedStepId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const [createItemOpen, setCreateItemOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<LessonItem | null>(null);
  const [itemForm, setItemForm] = useState(blankItem);

  const [createStepOpen, setCreateStepOpen] = useState(false);
  const [editingStep, setEditingStep] = useState<LessonStep | null>(null);
  const [stepForm, setStepForm] = useState(blankStep);

  const [metaOpen, setMetaOpen] = useState(false);
  const [metaForm, setMetaForm] = useState(blankMeta);

  async function load() {
    const L = await api.admin.curriculumLesson(lessonId);
    setLesson(L);
    try {
      const c = await api.admin.getCurriculumCourse(L.course_id);
      setCourse(c);
    } catch {
      setCourse(null);
    }
    setSelectedStepId((prev) => {
      const steps = [...(L.steps || [])].sort((a, b) => a.sort_order - b.sort_order);
      if (prev && steps.some((s) => s.id === prev)) return prev;
      return steps[0]?.id ?? null;
    });
  }

  useEffect(() => {
    if (!lessonId) return;
    load().catch((e) => setError(e instanceof Error ? e.message : "Lỗi tải"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lessonId]);

  const steps = useMemo(
    () => [...(lesson?.steps || [])].sort((a, b) => a.sort_order - b.sort_order),
    [lesson]
  );
  const selectedStep = steps.find((s) => s.id === selectedStepId) || null;
  const items = useMemo(() => {
    if (!selectedStep) return [];
    return [...(selectedStep.items || [])].sort((a, b) => a.sort_order - b.sort_order);
  }, [selectedStep]);
  const allItemCount = steps.reduce((n, s) => n + (s.items?.length || 0), 0);
  const hskLevel = course?.hsk_level ?? 1;

  async function onCreateItem(e: FormEvent) {
    e.preventDefault();
    try {
      const stepId = itemForm.step_id === "" ? selectedStepId : Number(itemForm.step_id);
      await api.admin.createCurriculumItem({
        lesson_id: lessonId,
        step_id: stepId,
        item_type: itemForm.item_type,
        hanzi: itemForm.hanzi || null,
        pinyin: itemForm.pinyin || null,
        meaning_vi: itemForm.meaning_vi || null,
        meaning_en: itemForm.meaning_en || null,
        audio_text: itemForm.audio_text || itemForm.hanzi || null,
        speaker: itemForm.speaker || null,
        sort_order: itemForm.sort_order,
      });
      setCreateItemOpen(false);
      setItemForm(blankItem);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi tạo card");
    }
  }

  async function onSaveItem(e: FormEvent) {
    e.preventDefault();
    if (!editingItem) return;
    try {
      await api.admin.updateCurriculumItem(editingItem.id, {
        step_id: editingItem.step_id,
        item_type: editingItem.item_type,
        hanzi: editingItem.hanzi,
        pinyin: editingItem.pinyin,
        meaning_vi: editingItem.meaning_vi,
        meaning_en: editingItem.meaning_en,
        audio_text: editingItem.audio_text,
        speaker: editingItem.speaker,
        sort_order: editingItem.sort_order,
      });
      setEditingItem(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi lưu card");
    }
  }

  async function onCreateStep(e: FormEvent) {
    e.preventDefault();
    try {
      const created = await api.admin.createCurriculumStep({
        lesson_id: lessonId,
        step_key: stepForm.step_key,
        title_vi: stepForm.title_vi || stepForm.step_key,
        sort_order: stepForm.sort_order,
        required: stepForm.required,
      });
      setCreateStepOpen(false);
      setStepForm(blankStep);
      await load();
      setSelectedStepId(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi tạo bước");
    }
  }

  async function onSaveStep(e: FormEvent) {
    e.preventDefault();
    if (!editingStep) return;
    try {
      await api.admin.updateCurriculumStep(editingStep.id, {
        step_key: editingStep.step_key,
        title_vi: editingStep.title_vi,
        sort_order: editingStep.sort_order,
        required: editingStep.required,
      });
      setEditingStep(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi lưu bước");
    }
  }

  async function onSaveMeta(e: FormEvent) {
    e.preventDefault();
    try {
      await api.admin.updateCurriculumLesson(lessonId, {
        number: metaForm.number,
        title_zh: metaForm.title_zh,
        title_vi: metaForm.title_vi || null,
        title_en: metaForm.title_en || null,
        lesson_type: metaForm.lesson_type,
        estimated_minutes: metaForm.estimated_minutes,
        unlock_rule: metaForm.unlock_rule,
        published: metaForm.published,
      });
      setMetaOpen(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi lưu bài");
    }
  }

  if (!lesson) return <p className="text-[var(--muted)]">{error || "Đang tải…"}</p>;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--muted)]">
            <Link href="/admin/curriculum" className="hover:text-[var(--orange)]">
              Giáo trình
            </Link>
            <span>/</span>
            <Link
              href={`/admin/curriculum/course/${lesson.course_id}`}
              className="hover:text-[var(--orange)]"
            >
              HSK {hskLevel}
            </Link>
            <span>/</span>
            <span className="text-[var(--navy)]">Bài {lesson.number}</span>
          </div>
          <h1 className="mt-1 font-display text-2xl font-bold uppercase text-[var(--navy)]">
            Bài {lesson.number}: <span className="font-zh normal-case">{lesson.title_zh}</span>
          </h1>
          {lesson.title_pinyin && (
            <p className="text-sm font-medium text-[var(--orange-dark)]">{lesson.title_pinyin}</p>
          )}
          <p className="text-sm text-[var(--muted)]">
            {lesson.lesson_type} · {steps.length} bước · {allItemCount} card
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="btn btn-ghost text-xs"
            onClick={() => {
              setMetaForm({
                number: lesson.number,
                title_zh: lesson.title_zh,
                title_vi: lesson.title_vi || "",
                title_en: lesson.title_en || "",
                lesson_type: lesson.lesson_type || "dialogue_core",
                estimated_minutes: lesson.estimated_minutes ?? 12,
                unlock_rule: lesson.unlock_rule || "sequential",
                published: lesson.published,
              });
              setMetaOpen(true);
            }}
          >
            Sửa bài
          </button>
          <Link
            className="btn btn-ghost text-xs"
            href={`/learn/hsk/${hskLevel}/${lesson.id}`}
            target="_blank"
          >
            Preview
          </Link>
          <button
            type="button"
            className="btn btn-navy text-xs"
            onClick={() => {
              setStepForm({
                ...blankStep,
                sort_order: steps.length,
              });
              setCreateStepOpen(true);
            }}
          >
            + Bước
          </button>
          <button
            type="button"
            className="btn btn-primary text-xs"
            disabled={!selectedStepId}
            onClick={() => {
              setItemForm({
                ...blankItem,
                step_id: selectedStepId ?? "",
                sort_order: items.length,
              });
              setCreateItemOpen(true);
            }}
          >
            + Card
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

      <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
        <aside className="space-y-2 rounded-md border border-[var(--line)] bg-white p-3 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wide text-[var(--orange)]">Bước học</p>
          {steps.length === 0 && (
            <p className="text-xs text-[var(--muted)]">Chưa có bước. Bấm “+ Bước”.</p>
          )}
          {steps.map((s, i) => {
            const active = s.id === selectedStepId;
            return (
              <div
                key={s.id}
                className={`rounded-sm border p-2 ${
                  active ? "border-[var(--orange)] bg-[var(--accent-soft)]" : "border-[var(--line)]"
                }`}
              >
                <button
                  type="button"
                  className="w-full text-left"
                  onClick={() => setSelectedStepId(s.id)}
                >
                  <p className="text-[10px] font-bold uppercase text-[var(--muted)]">
                    {i + 1}. {s.step_key}
                    {s.required ? "" : " · optional"}
                  </p>
                  <p className="text-sm font-semibold text-[var(--navy)]">{s.title_vi}</p>
                  <p className="text-xs text-[var(--muted)]">{(s.items || []).length} card</p>
                </button>
                <div className="mt-2 flex gap-1">
                  <button
                    type="button"
                    className="btn btn-ghost flex-1 px-1 py-1 text-[10px]"
                    onClick={() => setEditingStep(s)}
                  >
                    Sửa
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost flex-1 px-1 py-1 text-[10px] text-[var(--danger)]"
                    onClick={() => {
                      if (!confirm(`Xóa bước “${s.title_vi}”?`)) return;
                      api.admin
                        .deleteCurriculumStep(s.id)
                        .then(load)
                        .catch((e) => setError(e.message));
                    }}
                  >
                    Xóa
                  </button>
                </div>
              </div>
            );
          })}
        </aside>

        <section className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-display text-lg font-bold uppercase text-[var(--navy)]">
              {selectedStep ? selectedStep.title_vi : "Chọn bước"}
            </h2>
            {selectedStep && (
              <p className="text-xs text-[var(--muted)]">
                key: {selectedStep.step_key} · sort {selectedStep.sort_order}
              </p>
            )}
          </div>

          {!selectedStep && (
            <p className="rounded-md border border-dashed border-[var(--line)] p-8 text-sm text-[var(--muted)]">
              Chọn một bước bên trái để xem / sửa card.
            </p>
          )}

          {items.map((it) => (
            <div key={it.id} className="flex flex-wrap gap-4 rounded-md border border-[var(--line)] bg-white p-4 shadow-sm">
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold uppercase text-[var(--orange)]">
                  {it.item_type}
                  {it.speaker ? ` · ${it.speaker}` : ""}
                </p>
                <p className="font-zh text-2xl text-[var(--navy)]">{it.hanzi || "—"}</p>
                <p className="text-sm font-medium text-[var(--orange-dark)]">{it.pinyin || "—"}</p>
                <p className="mt-1 text-sm">{it.meaning_vi || it.meaning_en || ""}</p>
              </div>
              <div className="flex flex-col gap-2">
                <button
                  type="button"
                  className="btn btn-ghost text-xs"
                  onClick={() => speakZh(it.audio_text || it.hanzi || "")}
                >
                  Nghe
                </button>
                <button type="button" className="btn btn-ghost text-xs" onClick={() => setEditingItem(it)}>
                  Sửa
                </button>
                <button
                  type="button"
                  className="btn btn-ghost text-xs text-[var(--danger)]"
                  onClick={() =>
                    api.admin
                      .deleteCurriculumItem(it.id)
                      .then(load)
                      .catch((e) => setError(e.message))
                  }
                >
                  Xóa
                </button>
              </div>
            </div>
          ))}

          {selectedStep && items.length === 0 && (
            <p className="text-sm text-[var(--muted)]">Bước này chưa có card.</p>
          )}
        </section>
      </div>

      <Modal open={createItemOpen} onClose={() => setCreateItemOpen(false)} title="Thêm card">
        <form className="space-y-3" onSubmit={onCreateItem}>
          <ItemFields value={itemForm} steps={steps} onChange={setItemForm} />
          <button className="btn btn-primary w-full text-xs" type="submit">
            Tạo
          </button>
        </form>
      </Modal>

      <Modal open={!!editingItem} onClose={() => setEditingItem(null)} title="Sửa card">
        {editingItem && (
          <form className="space-y-3" onSubmit={onSaveItem}>
            <ItemFields
              value={{
                item_type: editingItem.item_type,
                hanzi: editingItem.hanzi || "",
                pinyin: editingItem.pinyin || "",
                meaning_vi: editingItem.meaning_vi || "",
                meaning_en: editingItem.meaning_en || "",
                audio_text: editingItem.audio_text || "",
                speaker: editingItem.speaker || "",
                sort_order: editingItem.sort_order,
                step_id: editingItem.step_id ?? "",
              }}
              steps={steps}
              onChange={(v) =>
                setEditingItem({
                  ...editingItem,
                  ...v,
                  step_id: v.step_id === "" ? null : Number(v.step_id),
                })
              }
            />
            <button className="btn btn-primary w-full text-xs" type="submit">
              Lưu
            </button>
          </form>
        )}
      </Modal>

      <Modal open={createStepOpen} onClose={() => setCreateStepOpen(false)} title="Thêm bước">
        <form className="space-y-3" onSubmit={onCreateStep}>
          <StepFields value={stepForm} onChange={setStepForm} />
          <button className="btn btn-primary w-full text-xs" type="submit">
            Tạo
          </button>
        </form>
      </Modal>

      <Modal open={!!editingStep} onClose={() => setEditingStep(null)} title="Sửa bước">
        {editingStep && (
          <form className="space-y-3" onSubmit={onSaveStep}>
            <StepFields
              value={{
                step_key: editingStep.step_key,
                title_vi: editingStep.title_vi,
                sort_order: editingStep.sort_order,
                required: editingStep.required,
              }}
              onChange={(v) => setEditingStep({ ...editingStep, ...v })}
            />
            <button className="btn btn-primary w-full text-xs" type="submit">
              Lưu
            </button>
          </form>
        )}
      </Modal>

      <Modal open={metaOpen} onClose={() => setMetaOpen(false)} title="Sửa thông tin bài">
        <form className="space-y-3" onSubmit={onSaveMeta}>
          <label className="block text-xs font-semibold">
            Số bài
            <input
              className="input mt-1"
              type="number"
              value={metaForm.number}
              onChange={(e) => setMetaForm({ ...metaForm, number: Number(e.target.value) })}
            />
          </label>
          <label className="block text-xs font-semibold">
            Title ZH
            <input
              className="input mt-1 font-zh"
              value={metaForm.title_zh}
              onChange={(e) => setMetaForm({ ...metaForm, title_zh: e.target.value })}
            />
          </label>
          <label className="block text-xs font-semibold">
            Title VI
            <input
              className="input mt-1"
              value={metaForm.title_vi}
              onChange={(e) => setMetaForm({ ...metaForm, title_vi: e.target.value })}
            />
          </label>
          <label className="block text-xs font-semibold">
            Title EN
            <input
              className="input mt-1"
              value={metaForm.title_en}
              onChange={(e) => setMetaForm({ ...metaForm, title_en: e.target.value })}
            />
          </label>
          <label className="block text-xs font-semibold">
            Lesson type
            <input
              className="input mt-1"
              value={metaForm.lesson_type}
              onChange={(e) => setMetaForm({ ...metaForm, lesson_type: e.target.value })}
            />
          </label>
          <label className="flex items-center gap-2 text-xs font-semibold">
            <input
              type="checkbox"
              checked={metaForm.published}
              onChange={(e) => setMetaForm({ ...metaForm, published: e.target.checked })}
            />
            Published
          </label>
          <button className="btn btn-primary w-full text-xs" type="submit">
            Lưu
          </button>
        </form>
      </Modal>
    </div>
  );
}

function StepFields({
  value,
  onChange,
}: {
  value: typeof blankStep;
  onChange: (v: typeof blankStep) => void;
}) {
  return (
    <>
      <label className="block text-xs font-semibold">
        step_key
        <select
          className="input mt-1"
          value={value.step_key}
          onChange={(e) => onChange({ ...value, step_key: e.target.value })}
        >
          {STEP_KEYS.map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-xs font-semibold">
        Tiêu đề VI
        <input
          className="input mt-1"
          required
          value={value.title_vi}
          onChange={(e) => onChange({ ...value, title_vi: e.target.value })}
        />
      </label>
      <label className="block text-xs font-semibold">
        Sort order
        <input
          className="input mt-1"
          type="number"
          value={value.sort_order}
          onChange={(e) => onChange({ ...value, sort_order: Number(e.target.value) })}
        />
      </label>
      <label className="flex items-center gap-2 text-xs font-semibold">
        <input
          type="checkbox"
          checked={value.required}
          onChange={(e) => onChange({ ...value, required: e.target.checked })}
        />
        Bắt buộc hoàn thành
      </label>
    </>
  );
}

function ItemFields({
  value,
  steps,
  onChange,
}: {
  value: typeof blankItem;
  steps: LessonStep[];
  onChange: (v: typeof blankItem) => void;
}) {
  return (
    <>
      <label className="block text-xs font-semibold">
        Bước
        <select
          className="input mt-1"
          value={value.step_id}
          onChange={(e) =>
            onChange({ ...value, step_id: e.target.value ? Number(e.target.value) : "" })
          }
        >
          <option value="">—</option>
          {steps.map((s) => (
            <option key={s.id} value={s.id}>
              {s.title_vi} ({s.step_key})
            </option>
          ))}
        </select>
      </label>
      <label className="block text-xs font-semibold">
        Loại card
        <select
          className="input mt-1"
          value={value.item_type}
          onChange={(e) => onChange({ ...value, item_type: e.target.value })}
        >
          {ITEM_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-xs font-semibold">
        Hán tự
        <input
          className="input mt-1 font-zh"
          value={value.hanzi}
          onChange={(e) => onChange({ ...value, hanzi: e.target.value })}
        />
      </label>
      <label className="block text-xs font-semibold">
        Pinyin
        <input
          className="input mt-1"
          value={value.pinyin}
          onChange={(e) => onChange({ ...value, pinyin: e.target.value })}
        />
      </label>
      <label className="block text-xs font-semibold">
        Nghĩa VI
        <input
          className="input mt-1"
          value={value.meaning_vi}
          onChange={(e) => onChange({ ...value, meaning_vi: e.target.value })}
        />
      </label>
      <label className="block text-xs font-semibold">
        Nghĩa EN
        <input
          className="input mt-1"
          value={value.meaning_en}
          onChange={(e) => onChange({ ...value, meaning_en: e.target.value })}
        />
      </label>
      <label className="block text-xs font-semibold">
        Speaker
        <input
          className="input mt-1"
          value={value.speaker}
          onChange={(e) => onChange({ ...value, speaker: e.target.value })}
        />
      </label>
      <label className="block text-xs font-semibold">
        Audio text (TTS)
        <input
          className="input mt-1"
          value={value.audio_text}
          onChange={(e) => onChange({ ...value, audio_text: e.target.value })}
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
    </>
  );
}
