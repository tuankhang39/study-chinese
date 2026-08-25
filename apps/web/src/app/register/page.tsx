"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.register({
        email,
        password,
        display_name: displayName,
      });
      localStorage.setItem("token", res.access_token);
      router.push("/home");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng ký thất bại");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative flex flex-col justify-center bg-[var(--orange)] px-6 py-12 lg:px-12">
        <p className="font-display text-4xl font-bold uppercase leading-tight text-white">
          Bắt đầu<br />học hôm nay
        </p>
        <p className="mt-4 max-w-sm text-white/90">
          600+ từ HSK · flashcard FSRS · listening · AI roleplay công việc — miễn phí cho MVP.
        </p>
        <p className="font-zh mt-6 text-2xl text-white/80">你好，欢迎！</p>
      </div>
      <div className="flex flex-col justify-center px-6 py-12 lg:px-16">
        <Link href="/" className="mb-8 font-display text-xl font-bold uppercase text-[var(--navy)] lg:hidden">
          ← Trang chủ
        </Link>
        <h1 className="font-display text-3xl font-bold uppercase text-[var(--navy)]">Tạo tài khoản</h1>
        <p className="mt-2 text-[var(--muted)]">HSK + tình huống đi làm trong một app.</p>
        <form onSubmit={onSubmit} className="mt-8 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-semibold uppercase tracking-wide">Tên hiển thị</label>
            <input
              className="input"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-semibold uppercase tracking-wide">Email</label>
            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="mb-1 block text-sm font-semibold uppercase tracking-wide">Mật khẩu</label>
            <input
              className="input"
              type="password"
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
          <button className="btn btn-primary w-full" disabled={loading}>
            {loading ? "Đang tạo…" : "Đăng ký"}
          </button>
        </form>
        <p className="mt-6 text-sm text-[var(--muted)]">
          Đã có tài khoản?{" "}
          <Link href="/login" className="font-semibold text-[var(--orange)] hover:underline">
            Đăng nhập
          </Link>
        </p>
      </div>
    </div>
  );
}
