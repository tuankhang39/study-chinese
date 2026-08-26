"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  api,
  LessonItem,
  LessonPlayer,
  LessonStep,
  speakZh,
} from "@/lib/api";

function isStepUnlocked(steps: LessonStep[], idx: number, doneKeys: string[]): boolean {
  if (idx <= 0) return true;
  for (let i = 0; i < idx; i++) {
    const s = steps[i];
    if (s.required && !doneKeys.includes(s.step_key)) return false;
  }
  return true;
}

export default function LessonPlayerPage() {
  const params = useParams();
  const router = useRouter();
  const level = Number(params.level);
  const id = Number(params.lessonId);
  const [data, setData] = useState<LessonPlayer | null>(null);
  const [stepIdx, setStepIdx] = useState(0);
  const [cardIdx, setCardIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [showPinyin, setShowPinyin] = useState(true);
  const [quizPick, setQuizPick] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");

  useEffect(() => {
    if (!id) return;
    api
      .lessonPlayer(id)
      .then((p) => {
        setData(p);
        const keys = p.progress.completed_step_keys || [];
        const firstOpen = p.steps.findIndex(
          (s, i) => isStepUnlocked(p.steps, i, keys) && !keys.includes(s.step_key)
        );
        setStepIdx(firstOpen >= 0 ? firstOpen : 0);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  const step: LessonStep | undefined = data?.steps[stepIdx];
  const items = useMemo(() => step?.items || [], [step]);
  const item: LessonItem | undefined = items[cardIdx];
  const doneKeys = data?.progress.completed_step_keys || [];

  useEffect(() => {
    setCardIdx(0);
    setFlipped(false);
    setQuizPick(null);
  }, [stepIdx]);

  function tryGoStep(i: number) {
    if (!data) return;
    if (!isStepUnlocked(data.steps, i, doneKeys)) {
      setToast("Hãy hoàn thành bước trước đã!");
      setTimeout(() => setToast(""), 1800);
      return;
    }
    setStepIdx(i);
  }

  async function markStepDone(andComplete = false) {
    if (!data || !step || busy) return;
    if (!isStepUnlocked(data.steps, stepIdx, doneKeys)) {
      setToast("Hãy hoàn thành bước trước đã!");
      setTimeout(() => setToast(""), 1800);
      return;
    }
    // Hoàn thành bài chỉ khi mọi bước bắt buộc đã xong
    if (step.step_key === "complete" || andComplete) {
      const required = data.steps.filter((s) => s.required).map((s) => s.step_key);
      const missing = required.filter((k) => !doneKeys.includes(k) && k !== step.step_key);
      if (missing.length) {
        setToast("Cần học xong mọi bước trước khi hoàn thành bài.");
        setTimeout(() => setToast(""), 2000);
        return;
      }
    }
    setBusy(true);
    try {
      const keys = Array.from(new Set([...doneKeys, step.step_key]));
      if (andComplete || step.step_key === "complete") {
        keys.push("complete");
      }
      const required = data.steps.filter((s) => s.required).map((s) => s.step_key);
      const allRequired = required.every((k) => keys.includes(k));
      const prog = await api.updateLessonProgress(id, {
        completed_step_keys: keys,
        completed: andComplete || allRequired || step.step_key === "complete",
        push_to_fsrs: true,
      });
      setData({ ...data, progress: prog });
      if (stepIdx + 1 < data.steps.length && isStepUnlocked(data.steps, stepIdx + 1, keys)) {
        setStepIdx(stepIdx + 1);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi lưu tiến độ");
    } finally {
      setBusy(false);
    }
  }

  if (!data) {
    return (
      <div className="grid min-h-[50vh] place-items-center text-[var(--muted)]">
        {error || "Đang tải bài…"}
      </div>
    );
  }

  const { lesson, progress, next_lesson_id } = data;
  const pct = progress.percent || 0;
  const stepDone = doneKeys.includes(step?.step_key || "");

  return (
    <div className="relative min-h-[calc(100vh-8rem)] pb-10">
      <div className="absolute inset-x-0 top-0 h-56 bg-gradient-to-br from-[#fff4e6] via-white to-[#e8eef8]" />

      <div className="relative mx-auto max-w-5xl space-y-5 p-4 md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link
              href={`/learn/hsk/${level}`}
              className="text-xs font-semibold text-[var(--muted)] hover:text-[var(--orange)]"
            >
              ← HSK {level}
            </Link>
            <h1 className="font-zh mt-2 text-3xl font-bold text-[var(--navy)] md:text-4xl">
              {lesson.number}. {lesson.title_zh}
            </h1>
            {lesson.title_pinyin && (
              <p className="text-base font-medium text-[var(--orange-dark)]">{lesson.title_pinyin}</p>
            )}
            <p className="text-[var(--muted)]">{lesson.title_vi || lesson.title_en}</p>
          </div>
          <div className="min-w-[10rem] rounded-md border border-[var(--line)] bg-white/90 px-4 py-3 shadow-sm">
            <p className="text-[10px] font-bold uppercase tracking-wide text-[var(--muted)]">Tiến độ bài</p>
            <p className="font-display text-2xl font-bold text-[var(--orange)]">{pct}%</p>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-[var(--bg-soft)]">
              <div className="h-full rounded-full bg-[var(--orange)] transition-all" style={{ width: `${pct}%` }} />
            </div>
          </div>
        </div>

        {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
        {toast && (
          <p className="rounded-sm border border-[var(--orange)] bg-[var(--accent-soft)] px-3 py-2 text-sm font-semibold text-[var(--orange-dark)]">
            {toast}
          </p>
        )}

        {/* Step rail */}
        <div className="overflow-x-auto rounded-md border border-[var(--line)] bg-white p-2 shadow-sm">
          <div className="flex min-w-max gap-2">
            {data.steps.map((s, i) => {
              const done = doneKeys.includes(s.step_key);
              const unlocked = isStepUnlocked(data.steps, i, doneKeys);
              const active = i === stepIdx;
              return (
                <button
                  key={s.id}
                  type="button"
                  disabled={!unlocked}
                  onClick={() => tryGoStep(i)}
                  className={`relative flex min-w-[7.5rem] flex-col items-start rounded-sm px-3 py-2 text-left transition ${
                    active
                      ? "bg-[var(--orange)] text-white shadow-md"
                      : done
                        ? "bg-[var(--navy)] text-white/95"
                        : unlocked
                          ? "bg-[var(--bg-soft)] text-[var(--navy)] hover:bg-[var(--accent-soft)]"
                          : "cursor-not-allowed bg-[var(--bg-soft)] text-[var(--muted)] opacity-55"
                  }`}
                >
                  <span className="text-[10px] font-bold uppercase opacity-80">
                    {i + 1}/{data.steps.length}
                    {!unlocked ? " · khóa" : done ? " · xong" : ""}
                  </span>
                  <span className="text-xs font-bold leading-tight">{s.title_vi}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="grid gap-5 lg:grid-cols-[1fr_280px]">
          <div className="space-y-4">
            {step && (
              <StepBody
                step={step}
                item={item}
                items={items}
                cardIdx={cardIdx}
                flipped={flipped}
                showPinyin={showPinyin}
                quizPick={quizPick}
                onFlip={() => setFlipped((f) => !f)}
                onTogglePinyin={() => setShowPinyin((v) => !v)}
                onQuizPick={setQuizPick}
                onPrevCard={() => {
                  setCardIdx((i) => Math.max(0, i - 1));
                  setFlipped(false);
                  setQuizPick(null);
                }}
                onNextCard={() => {
                  setCardIdx((i) => Math.min(items.length - 1, i + 1));
                  setFlipped(false);
                  setQuizPick(null);
                }}
              />
            )}

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                className="btn btn-primary min-w-[12rem] flex-1 text-sm"
                disabled={busy}
                onClick={() => markStepDone(step?.step_key === "complete")}
              >
                {step?.step_key === "complete"
                  ? "Hoàn thành bài ✓"
                  : stepDone
                    ? "Qua bước tiếp →"
                    : "Xong bước này →"}
              </button>
              {step?.step_key === "complete" && next_lesson_id && (
                <button
                  type="button"
                  className="btn btn-navy flex-1 text-sm"
                  onClick={() => router.push(`/learn/hsk/${level}/${next_lesson_id}`)}
                >
                  Bài tiếp theo
                </button>
              )}
            </div>
          </div>

          <aside className="space-y-3">
            <div className="rounded-md border border-[var(--line)] bg-white p-4 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-[var(--orange)]">Lộ trình</p>
              <ul className="mt-3 space-y-2">
                {data.steps.map((s, i) => {
                  const done = doneKeys.includes(s.step_key);
                  const unlocked = isStepUnlocked(data.steps, i, doneKeys);
                  return (
                    <li key={s.id} className="flex items-center gap-2 text-sm">
                      <span
                        className={`grid h-6 w-6 place-items-center rounded-full text-[10px] font-bold ${
                          done
                            ? "bg-[var(--orange)] text-white"
                            : unlocked
                              ? "bg-[var(--navy)] text-white"
                              : "bg-[var(--line)] text-[var(--muted)]"
                        }`}
                      >
                        {done ? "✓" : i + 1}
                      </span>
                      <span className={unlocked ? "text-[var(--ink)]" : "text-[var(--muted)]"}>
                        {s.title_vi}
                      </span>
                    </li>
                  );
                })}
              </ul>
              <p className="mt-3 text-[11px] leading-relaxed text-[var(--muted)]">
                Phải xong từng bước mới mở bước sau — kể cả bước Hoàn thành.
              </p>
            </div>

            {step?.step_key === "complete" && (
              <Link href="/flashcards" className="btn btn-ghost w-full text-xs">
                Ôn flashcard ngay
              </Link>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}

function StepBody({
  step,
  item,
  items,
  cardIdx,
  flipped,
  showPinyin,
  quizPick,
  onFlip,
  onTogglePinyin,
  onQuizPick,
  onPrevCard,
  onNextCard,
}: {
  step: LessonStep;
  item?: LessonItem;
  items: LessonItem[];
  cardIdx: number;
  flipped: boolean;
  showPinyin: boolean;
  quizPick: string | null;
  onFlip: () => void;
  onTogglePinyin: () => void;
  onQuizPick: (v: string) => void;
  onPrevCard: () => void;
  onNextCard: () => void;
}) {
  if (!items.length) {
    return (
      <div className="rounded-md border border-dashed border-[var(--line)] bg-white p-8 text-sm text-[var(--muted)]">
        Chưa có nội dung cho bước “{step.title_vi}”.
      </div>
    );
  }

  if (step.step_key === "complete") {
    const msg = items[0];
    return (
      <div className="overflow-hidden rounded-md border border-[var(--line)] bg-white shadow-md">
        <div className="bg-gradient-to-br from-[var(--orange)] to-[#e07a00] px-6 py-10 text-center text-white">
          <p className="font-zh text-5xl font-bold">完成!</p>
          <p className="mt-2 text-lg font-semibold">Bạn đã đi hết lộ trình bài này</p>
          <p className="mt-1 text-sm text-white/85">
            {msg?.meaning_vi || "Bấm hoàn thành để mở bài tiếp theo và đẩy từ vào flashcard."}
          </p>
        </div>
        <div className="grid gap-3 p-5 sm:grid-cols-3">
          {["Đã nghe từ", "Đã xem hội thoại", "Sẵn sàng ôn FSRS"].map((t) => (
            <div key={t} className="rounded-sm bg-[var(--bg-soft)] px-3 py-3 text-center text-xs font-bold text-[var(--navy)]">
              ✓ {t}
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (step.step_key === "dialogue") {
    return (
      <div className="overflow-hidden rounded-md border border-[var(--line)] bg-white shadow-md">
        <div className="bg-gradient-to-r from-[var(--navy)] to-[#003399] px-5 py-3 text-white">
          <p className="text-xs font-bold uppercase tracking-wide text-[var(--orange)]">Hội thoại</p>
          <p className="text-sm opacity-90">Nghe từng câu · xem bản dịch tiếng Việt bên dưới</p>
        </div>
        <div className="divide-y divide-[var(--line)]">
          {items.map((line, idx) => (
            <div
              key={line.id}
              className={`flex gap-3 px-4 py-4 ${idx % 2 === 0 ? "bg-white" : "bg-[var(--bg-soft)]/60"}`}
            >
              <button
                type="button"
                className="mt-1 grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[var(--orange)] text-sm font-bold text-white shadow"
                onClick={() => speakZh(line.audio_text || line.hanzi || "")}
                aria-label="Nghe"
              >
                ▶
              </button>
              <div className="min-w-0 flex-1">
                {line.speaker && (
                  <p className="text-[11px] font-bold uppercase tracking-wide text-[var(--orange)]">
                    {line.speaker}
                  </p>
                )}
                <p className="font-zh text-2xl font-semibold text-[var(--navy)]">{line.hanzi}</p>
                <p className="text-sm font-medium text-[var(--orange-dark)]">
                  {line.pinyin || "—"}
                </p>
                <p className="mt-1 text-base font-medium text-[var(--ink)]">
                  {line.meaning_vi || line.meaning_en || "—"}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (step.step_key === "objectives" || step.step_key === "review" || step.step_key === "grammar") {
    return (
      <div className="rounded-md border border-[var(--line)] bg-white p-5 shadow-md md:p-6">
        <p className="text-xs font-bold uppercase tracking-wide text-[var(--orange)]">{step.title_vi}</p>
        <ul className="mt-4 space-y-4">
          {items.map((it, i) => (
            <li key={it.id} className="flex gap-3">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-sm bg-[var(--accent-soft)] text-sm font-bold text-[var(--orange-dark)]">
                {i + 1}
              </span>
              <div>
                {it.hanzi && reHasHanzi(it.hanzi) && (
                  <>
                    <p className="font-zh text-lg text-[var(--navy)]">{it.hanzi}</p>
                    <p className="text-sm font-medium text-[var(--orange-dark)]">{it.pinyin || "—"}</p>
                  </>
                )}
                <p className="text-base text-[var(--ink)]">{it.meaning_vi || it.meaning_en || it.hanzi}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  if (step.step_key === "practice" && item?.item_type === "quiz_prompt") {
    const options = item.meta?.options || [];
    const answer = item.meta?.answer;
    const correct = quizPick != null && quizPick === answer;
    return (
      <div className="rounded-md border border-[var(--line)] bg-white p-5 shadow-md md:p-8">
        <div className="flex items-center justify-between">
          <p className="text-xs font-bold uppercase text-[var(--orange)]">
            Luyện {cardIdx + 1}/{items.length}
          </p>
          <button
            type="button"
            className="btn btn-primary px-3 py-2 text-xs"
            onClick={() => speakZh(item.audio_text || item.hanzi || "")}
          >
            Nghe
          </button>
        </div>
        <p className="mt-6 text-center font-zh text-6xl font-bold text-[var(--navy)]">{item.hanzi}</p>
        <p className="mt-2 text-center text-lg font-medium text-[var(--orange-dark)]">{item.pinyin || "—"}</p>
        <p className="mt-4 text-center text-sm text-[var(--muted)]">Chọn nghĩa tiếng Việt đúng</p>
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {options.map((opt) => (
            <button
              key={opt}
              type="button"
              className={`rounded-sm border px-4 py-3 text-left text-sm font-semibold transition ${
                quizPick === opt
                  ? opt === answer
                    ? "border-emerald-500 bg-emerald-50 text-emerald-800"
                    : "border-[var(--danger)] bg-red-50 text-[var(--danger)]"
                  : "border-[var(--line)] hover:border-[var(--orange)] hover:bg-[var(--accent-soft)]"
              }`}
              onClick={() => onQuizPick(opt)}
            >
              {opt}
            </button>
          ))}
        </div>
        {quizPick && (
          <p className={`mt-3 text-sm font-semibold ${correct ? "text-emerald-700" : "text-[var(--danger)]"}`}>
            {correct ? "Đúng rồi!" : `Sai — đáp án: ${answer}`}
          </p>
        )}
        <div className="mt-4 flex gap-2">
          <button type="button" className="btn btn-ghost flex-1 text-xs" onClick={onPrevCard} disabled={cardIdx === 0}>
            Trước
          </button>
          <button
            type="button"
            className="btn btn-ghost flex-1 text-xs"
            onClick={onNextCard}
            disabled={cardIdx >= items.length - 1}
          >
            Câu sau
          </button>
        </div>
      </div>
    );
  }

  if (!item) return null;
  const speak = item.audio_text || item.hanzi || "";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-semibold text-[var(--navy)]">
          {step.title_vi}
          <span className="ml-2 text-[var(--muted)]">
            {cardIdx + 1}/{items.length}
          </span>
        </p>
        <div className="flex gap-2">
          <button type="button" className="btn btn-ghost px-3 py-2 text-xs" onClick={onTogglePinyin}>
            {showPinyin ? "Ẩn pinyin" : "Hiện pinyin"}
          </button>
          <button type="button" className="btn btn-primary px-4 py-2 text-xs" onClick={() => speakZh(speak)}>
            Nghe
          </button>
        </div>
      </div>

      <button
        type="button"
        onClick={onFlip}
        className="relative flex min-h-[320px] w-full flex-col items-center justify-center gap-3 overflow-hidden rounded-md border-2 border-[var(--navy)] bg-gradient-to-b from-white to-[#f7f9fc] p-8 text-center shadow-lg transition hover:shadow-xl"
      >
        <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-[var(--orange)]/15" />
        <div className="pointer-events-none absolute -bottom-10 -left-6 h-28 w-28 rounded-full bg-[var(--navy)]/10" />
        {!flipped ? (
          <>
            {item.speaker && <p className="text-xs font-bold uppercase text-[var(--orange)]">{item.speaker}</p>}
            <p className="font-zh text-6xl font-bold tracking-wide text-[var(--navy)] md:text-7xl">{item.hanzi}</p>
            {showPinyin && (
              <p className="text-2xl font-medium text-[var(--orange-dark)]">{item.pinyin || "—"}</p>
            )}
            <p className="mt-6 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
              Chạm để xem nghĩa VI
            </p>
          </>
        ) : (
          <>
            <p className="text-3xl font-bold text-[var(--navy)] md:text-4xl">
              {item.meaning_vi || item.meaning_en || "—"}
            </p>
            <p className="font-zh mt-4 text-3xl text-[var(--ink)]">{item.hanzi}</p>
            <p className="text-lg font-medium text-[var(--orange-dark)]">{item.pinyin || "—"}</p>
          </>
        )}
      </button>

      <div className="grid grid-cols-3 gap-2">
        <button type="button" className="btn btn-ghost text-xs" onClick={onPrevCard} disabled={cardIdx === 0}>
          ← Trước
        </button>
        <button type="button" className="btn btn-navy text-xs" onClick={() => speakZh(speak)}>
          Đọc theo
        </button>
        <button
          type="button"
          className="btn btn-ghost text-xs"
          onClick={onNextCard}
          disabled={cardIdx >= items.length - 1}
        >
          Sau →
        </button>
      </div>
    </div>
  );
}

function reHasHanzi(s: string) {
  return /[\u4e00-\u9fff]/.test(s);
}
