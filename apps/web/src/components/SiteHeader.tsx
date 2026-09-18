"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BrandLogo } from "@/components/BrandLogo";

export type NavItem = { href: string; label: string };

export const siteNavItems: NavItem[] = [
  { href: "/home", label: "Trang chủ" },
  { href: "/learn", label: "Khóa HSK" },
  { href: "/vocab", label: "Từ vựng" },
  { href: "/work", label: "Hội thoại" },
  { href: "/listening", label: "Nghe" },
  { href: "/flashcards", label: "Flashcard" },
  { href: "/work", label: "Đi làm" },
];

type SiteHeaderProps = {
  variant: "public" | "app";
  activePath?: string;
  userName?: string;
  showAdmin?: boolean;
  onLogout?: () => void;
};

export function SiteHeader({
  variant,
  activePath = "",
  userName,
  showAdmin,
  onLogout,
}: SiteHeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const logoHref = variant === "app" ? "/home" : "/";
  const navItems =
    variant === "public"
      ? siteNavItems.map((item) => {
          if (item.label === "Trang chủ") return { ...item, href: "/" };
          if (item.label === "Khóa HSK") return { ...item, href: "/learn" };
          return { ...item, href: item.href };
        })
      : [...siteNavItems, ...(showAdmin ? [{ href: "/admin", label: "Admin" }] : [])];

  useEffect(() => {
    setMenuOpen(false);
  }, [activePath]);

  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  return (
    <header className="sticky top-0 z-40 bg-white shadow-md">
      <div className="hidden border-b border-white/10 bg-[var(--navy)] text-white sm:block">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2 text-xs">
          <span>HSK + Career Chinese</span>
          <div className="flex items-center gap-5">
            {variant === "app" ? (
              <>
                {userName && (
                  <span className="font-zh text-white/90">
                    你好, <strong>{userName}</strong>
                  </span>
                )}
                <button type="button" onClick={onLogout} className="hover:text-[var(--orange)]">
                  Thoát
                </button>
              </>
            ) : (
              <>
                <span>Liên hệ: hello@tiengtrungdilam.vn</span>
                <Link href="/login" className="hover:text-[var(--orange)]">
                  Đăng nhập
                </Link>
                <Link href="/register" className="font-semibold text-[var(--orange)] hover:underline">
                  Đăng ký
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="border-b border-[var(--line)]">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3">
          <BrandLogo href={logoHref} size="md" priority />

          <nav className="hidden flex-1 items-center gap-1 overflow-x-auto lg:flex">
            {navItems.map((item, i) => {
              const active = activePath === item.href || activePath.startsWith(item.href + "/");
              return (
                <Link
                  key={`${item.label}-${i}`}
                  href={item.href}
                  className={`whitespace-nowrap rounded-sm px-3 py-2 text-sm font-semibold transition ${
                    active
                      ? "bg-[var(--orange)] text-white"
                      : "text-[var(--ink)] hover:bg-[var(--accent-soft)] hover:text-[var(--orange-dark)]"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            {variant === "public" && (
              <Link
                href="/register"
                className="btn btn-primary hidden px-4 py-2 text-xs sm:inline-flex lg:inline-flex"
              >
                Bắt đầu học
              </Link>
            )}

            <button
              type="button"
              className="grid h-10 w-10 place-items-center rounded-sm border border-[var(--line)] text-[var(--navy)] transition hover:border-[var(--orange)] hover:text-[var(--orange)] lg:hidden"
              aria-label={menuOpen ? "Đóng menu" : "Mở menu"}
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((o) => !o)}
            >
              {menuOpen ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
                  <path
                    d="M6 6l12 12M18 6L6 18"
                    stroke="currentColor"
                    strokeWidth="2.2"
                    strokeLinecap="round"
                  />
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
                  <path
                    d="M4 7h16M4 12h16M4 17h16"
                    stroke="currentColor"
                    strokeWidth="2.2"
                    strokeLinecap="round"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {menuOpen && (
        <>
          <button
            type="button"
            className="fixed inset-0 z-40 bg-black/35 lg:hidden"
            aria-label="Đóng menu"
            onClick={() => setMenuOpen(false)}
          />
          <div className="absolute left-0 right-0 top-full z-50 border-b border-[var(--line)] bg-white shadow-lg lg:hidden">
            <nav className="mx-auto flex max-w-7xl flex-col gap-1 px-4 py-3">
              {variant === "app" && userName && (
                <p className="mb-1 px-3 text-xs text-[var(--muted)]">
                  你好, <strong className="text-[var(--navy)]">{userName}</strong>
                </p>
              )}
              {navItems.map((item, i) => {
                const active = activePath === item.href || activePath.startsWith(item.href + "/");
                return (
                  <Link
                    key={`m-${item.label}-${i}`}
                    href={item.href}
                    onClick={() => setMenuOpen(false)}
                    className={`rounded-sm px-3 py-3 text-sm font-semibold transition ${
                      active
                        ? "bg-[var(--orange)] text-white"
                        : "text-[var(--ink)] hover:bg-[var(--accent-soft)]"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
              <div className="mt-2 flex flex-col gap-2 border-t border-[var(--line)] pt-3">
                {variant === "app" ? (
                  <button
                    type="button"
                    className="btn btn-ghost w-full justify-center text-sm"
                    onClick={() => {
                      setMenuOpen(false);
                      onLogout?.();
                    }}
                  >
                    Thoát
                  </button>
                ) : (
                  <>
                    <Link
                      href="/login"
                      className="btn btn-ghost w-full justify-center text-sm"
                      onClick={() => setMenuOpen(false)}
                    >
                      Đăng nhập
                    </Link>
                    <Link
                      href="/register"
                      className="btn btn-primary w-full justify-center text-sm"
                      onClick={() => setMenuOpen(false)}
                    >
                      Đăng ký
                    </Link>
                  </>
                )}
              </div>
            </nav>
          </div>
        </>
      )}
    </header>
  );
}
