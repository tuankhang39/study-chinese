"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function LegacyHsk1Redirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/learn/hsk/1");
  }, [router]);
  return <p className="p-8 text-[var(--muted)]">Chuyển tới Khóa HSK 1…</p>;
}
