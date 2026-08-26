"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, isAdminRole, User } from "@/lib/api";

const NAV = [
  { href: "/admin", label: "Dashboard", exact: true, icon: "◫" },
  { href: "/admin/users", label: "Users", exact: false, icon: "◎" },
  { href: "/admin/vocab", label: "Từ vựng", exact: false, icon: "文" },
  { href: "/admin/curriculum", label: "Giáo trình", exact: false, icon: "册" },
  { href: "/admin/scenarios", label: "Scenario", exact: false, icon: "☰" },
];

const SIDEBAR_W = "w-60"; // 15rem

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.replace("/login");
      return;
    }
    api
      .me()
      .then((u) => {
        if (!isAdminRole(u.role)) {
          setError("Bạn không có quyền Admin");
          setTimeout(() => router.replace("/home"), 1200);
          return;
        }
        setUser(u);
      })
      .catch(() => {
        localStorage.removeItem("token");
        router.replace("/login");
      });
  }, [router]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  if (error) {
    return <p className="p-8 text-[var(--danger)]">{error}</p>;
  }
  if (!user) {
    return (
      <div className="grid min-h-screen place-items-center bg-[var(--bg-soft)] text-[var(--muted)]">
        Đang tải admin…
      </div>
    );
  }

  const crumb =
    NAV.find((n) => (n.exact ? pathname === n.href : pathname.startsWith(n.href)))?.label || "Admin";

  return (
    <div className="min-h-screen bg-[var(--bg-soft)]">
      {/* Fixed sidebar — luôn gắn viewport */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex ${SIDEBAR_W} flex-col bg-[var(--navy)] text-white transition-transform duration-200 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0`}
      >
        <div className="flex shrink-0 items-center gap-2.5 border-b border-white/10 px-5 py-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-sm bg-[var(--orange)] font-zh text-lg font-bold">
            中
          </span>
          <div className="leading-tight">
            <p className="font-display text-sm font-bold uppercase tracking-wide">Admin</p>
            <p className="text-[10px] uppercase tracking-widest text-white/55">Tiếng Trung đi làm</p>
          </div>
        </div>
        <nav className="flex-1 space-y-0.5 overflow-y-auto p-3">
          {NAV.map((item) => {
            const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-sm px-3 py-2.5 text-sm font-semibold transition ${
                  active
                    ? "bg-[var(--orange)] text-white shadow-md"
                    : "text-white/75 hover:bg-white/10 hover:text-white"
                }`}
              >
                <span className="w-5 text-center opacity-80">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="shrink-0 border-t border-white/10 p-4 text-xs text-white/55">
          <p className="truncate font-medium text-white/85">{user.display_name}</p>
          <p className="mt-0.5">
            {user.role} · {user.plan}
          </p>
        </div>
      </aside>

      {sidebarOpen && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          aria-label="Đóng menu"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Content offset bằng sidebar trên desktop */}
      <div className="flex min-h-screen min-w-0 flex-col md:pl-60">
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-[var(--line)] bg-white px-4 py-3 shadow-sm">
          <button
            type="button"
            className="grid h-9 w-9 place-items-center rounded-sm border border-[var(--line)] text-[var(--navy)] md:hidden"
            onClick={() => setSidebarOpen(true)}
            aria-label="Menu"
          >
            ☰
          </button>
          <div className="min-w-0 flex-1">
            <p className="text-xs text-[var(--muted)]">
              Admin <span className="text-[var(--line)]">/</span>{" "}
              <span className="font-semibold text-[var(--navy)]">{crumb}</span>
            </p>
          </div>
          <Link href="/home" className="btn btn-ghost px-3 py-2 text-xs">
            Về app
          </Link>
          <button
            type="button"
            className="btn btn-primary px-3 py-2 text-xs"
            onClick={() => {
              localStorage.removeItem("token");
              router.push("/login");
            }}
          >
            Thoát
          </button>
        </header>
        <main className="flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
