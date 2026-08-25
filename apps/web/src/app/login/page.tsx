"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.login({ email, password });
      localStorage.setItem("token", res.access_token);
      router.push("/home");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng nhập thất bại");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden bg-[var(--navy)] lg:flex lg:flex-col lg:justify-center lg:px-12">
        <div className="absolute inset-0 opacity-20" style={{
          backgroundImage: "url('https://images.unsplash.com/photo-1600880292203-757bb62b4baf?auto=format&fit=crop&w=800&q=80')",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }} />
        <div className="relative z-10">
          <p className="font-display text-4xl font-bold uppercase leading-tight text-white">
            Tiếng Trung<br />đi làm
          </p>
          <p className="mt-4 max-w-sm text-white/75">
            Tiếp tục streak, hoàn thành nhiệm vụ hôm nay và luyện nói với AI sếp Trung Quốc.
          </p>
        </div>
      </div>
      <div className="flex flex-col justify-center px-6 py-12 lg:px-16">
        <Link href="/" className="mb-8 font-display text-xl font-bold uppercase text-[var(--navy)] lg:hidden">
          ← Trang chủ
        </Link>
        <h1 className="font-display text-3xl font-bold uppercase text-[var(--navy)]">Đăng nhập</h1>
        <p className="mt-2 text-[var(--muted)]">Chào mừng quay lại.</p>
        <form onSubmit={onSubmit} className="mt-8 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-semibold uppercase tracking-wide">Email</label>
            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="mb-1 block text-sm font-semibold uppercase tracking-wide">Mật khẩu</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
          <button className="btn btn-primary w-full" disabled={loading}>
            {loading ? "Đang vào…" : "Đăng nhập"}
          </button>
        </form>
        <p className="mt-6 text-sm text-[var(--muted)]">
          Chưa có tài khoản?{" "}
          <Link href="/register" className="font-semibold text-[var(--orange)] hover:underline">
            Đăng ký miễn phí
          </Link>
        </p>
      </div>
    </div>
  );
}
