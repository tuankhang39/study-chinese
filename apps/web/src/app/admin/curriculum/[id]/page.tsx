"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

/** Legacy `/admin/curriculum/[id]` → lesson editor */
export default function AdminCurriculumLegacyRedirect() {
  const params = useParams();
  const router = useRouter();
  const id = params.id;

  useEffect(() => {
    if (id) router.replace(`/admin/curriculum/lesson/${id}`);
  }, [id, router]);

  return <p className="p-6 text-sm text-[var(--muted)]">Chuyển tới trình sửa bài…</p>;
}
