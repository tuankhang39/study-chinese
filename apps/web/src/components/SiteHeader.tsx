import Link from "next/link";

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
  const logoHref = variant === "app" ? "/home" : "/";
  const navItems =
    variant === "public"
      ? siteNavItems.map((item) => {
          if (item.label === "Trang chủ") return { ...item, href: "/" };
          if (item.label === "Khóa HSK") return { ...item, href: "/learn" };
          return { ...item, href: item.href };
        })
      : [
          ...siteNavItems,
          ...(showAdmin ? [{ href: "/admin", label: "Admin" }] : []),
        ];

  return (
    <header className="sticky top-0 z-40 bg-white shadow-md">
      <div className="hidden border-b border-white/10 bg-[var(--navy)] text-white sm:block">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2 text-xs">
          <span>Tiếng Trung đi làm · HSK + Career Chinese</span>
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
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3">
          <Link href={logoHref} className="flex shrink-0 items-center gap-2.5">
            <span className="flex h-11 w-11 items-center justify-center rounded-sm bg-[var(--orange)] font-zh text-xl font-bold text-white shadow-md">
              中
            </span>
            <div className="leading-tight">
              <span className="font-display block text-lg font-bold uppercase tracking-wide text-[var(--navy)]">
                Tiếng Trung
              </span>
              <span className="block text-xs font-semibold uppercase tracking-widest text-[var(--orange)]">
                Đi làm
              </span>
            </div>
          </Link>

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

          <div className="ml-auto flex items-center gap-2 lg:hidden">
            {variant === "app" ? (
              <button type="button" onClick={onLogout} className="btn btn-ghost px-3 py-2 text-xs">
                Thoát
              </button>
            ) : (
              <Link href="/login" className="btn btn-ghost px-3 py-2 text-xs">
                Vào học
              </Link>
            )}
          </div>

          {variant === "public" && (
            <Link href="/register" className="btn btn-primary hidden px-4 py-2 text-xs sm:inline-flex">
              Bắt đầu học
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
