import Link from "next/link";

export function LandingFooter() {
  return (
    <footer className="border-t border-[var(--line)] bg-[var(--navy)] text-white">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-14 md:grid-cols-4">
        <div className="md:col-span-1">
          <div className="flex items-center gap-2">
            <span className="flex h-10 w-10 items-center justify-center rounded-sm bg-[var(--orange)] font-zh text-lg font-bold">
              中
            </span>
            <span className="font-display text-xl font-bold uppercase">Tiếng Trung đi làm</span>
          </div>
          <p className="mt-4 text-sm leading-relaxed text-white/65">
            Nền tảng học tiếng Trung theo hướng nghề nghiệp — HSK nền tảng + hội thoại công việc với AI.
          </p>
        </div>
        <div>
          <p className="text-sm font-bold uppercase tracking-wide text-[var(--orange)]">Khóa học</p>
          <ul className="mt-4 space-y-2.5 text-sm text-white/70">
            <li>
              <a href="/learn" className="hover:text-white">
                Giáo trình HSK
              </a>
            </li>
            <li>
              <a href="/vocab" className="hover:text-white">
                Từ vựng chủ đề
              </a>
            </li>
            <li>
              <a href="/work" className="hover:text-white">
                Hội thoại đi làm
              </a>
            </li>
            <li>
              <a href="/learn" className="hover:text-white">
                Luyện thi HSK
              </a>
            </li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-bold uppercase tracking-wide text-[var(--orange)]">Công cụ</p>
          <ul className="mt-4 space-y-2.5 text-sm text-white/70">
            <li>Flashcard FSRS</li>
            <li>Listening TTS</li>
            <li>AI Roleplay</li>
            <li>XP & Streak</li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-bold uppercase tracking-wide text-[var(--orange)]">Bắt đầu</p>
          <div className="mt-4 flex flex-col gap-3">
            <Link href="/register" className="btn btn-primary w-fit text-xs">
              Đăng ký miễn phí
            </Link>
            <Link href="/login" className="text-sm text-white/70 hover:text-white">
              Đã có tài khoản? Đăng nhập
            </Link>
            <p className="text-xs text-white/45">Miễn phí — không cần thẻ tín dụng</p>
          </div>
        </div>
      </div>
      <div className="border-t border-white/10 py-5 text-center text-xs text-white/45">
        © {new Date().getFullYear()} Tiếng Trung đi làm · MVP
      </div>
    </footer>
  );
}
