"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

export default function LegacyHsk1LessonRedirect() {
  const params = useParams();
  const router = useRouter();
  const id = params.id;
  useEffect(() => {
    if (id) router.replace(`/learn/hsk/1/${id}`);
  }, [id, router]);
  return <p className="p-8 text-[var(--muted)]">Chuyển tới bài học…</p>;
}
