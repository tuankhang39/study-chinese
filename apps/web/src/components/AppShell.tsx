"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { SiteHeader } from "@/components/SiteHeader";
import { api, isAdminRole, User } from "@/lib/api";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  const isAdminPath = pathname.startsWith("/admin");
  const publicPaths = ["/", "/login", "/register"];

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token && !publicPaths.includes(pathname)) {
      router.replace("/login");
      return;
    }
    if (token && (pathname === "/login" || pathname === "/register")) {
      // login page may still process ?token= from Google
      if (!pathname.startsWith("/login")) {
        router.replace("/home");
        return;
      }
    }
    if (token && !publicPaths.includes(pathname)) {
      api
        .me()
        .then(setUser)
        .catch(() => setUser(null));
    }
    setReady(true);
  }, [pathname, router]);

  const isApp = !publicPaths.includes(pathname) && !isAdminPath;

  function logout() {
    localStorage.removeItem("token");
    router.push("/login");
  }

  if (!ready && (isApp || isAdminPath)) {
    return (
      <div className="grid min-h-screen place-items-center bg-white text-[var(--muted)]">
        Đang tải…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {isApp && (
        <SiteHeader
          variant="app"
          activePath={pathname}
          userName={user?.display_name}
          showAdmin={isAdminRole(user?.role)}
          onLogout={logout}
        />
      )}
      <main className={isApp ? "mx-auto max-w-7xl px-4 py-8 md:py-10" : ""}>{children}</main>
    </div>
  );
}
