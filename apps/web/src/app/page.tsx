import Link from "next/link";
import { LandingFooter } from "@/components/LandingFooter";
import { LandingNav } from "@/components/LandingNav";

const floatingChars = "学中文语汉读写听说工作";

const modules = [
  {
    title: "Giáo trình HSK",
    desc: "Học theo chuẩn HSK quốc tế từ cấp 1 đến 3, phù hợp người mới và đi làm.",
    count: "600+ từ",
    icon: "HSK",
    accent: "navy",
  },
  {
    title: "Từ vựng chủ đề",
    desc: "Từ vựng phân loại theo nhà máy, văn phòng, QC, sales, IT — dễ học và ghi nhớ.",
    count: "8 chủ đề",
    icon: "词",
    accent: "orange",
  },
  {
    title: "Hội thoại đi làm",
    desc: "Luyện hội thoại thực tế: báo cáo sếp, đơn trễ, xin nghỉ, thương lượng khách.",
    count: "5 tình huống",
    icon: "话",
    accent: "navy",
  },
  {
    title: "Flashcard FSRS",
    desc: "Ôn từ thông minh với thuật toán spaced repetition — nhớ lâu, quên chậm.",
    count: "Ôn hàng ngày",
    icon: "卡",
    accent: "orange",
  },
  {
    title: "Listening",
    desc: "Nghe phát âm chuẩn qua TTS trình duyệt, chọn nghĩa đúng — luyện tai nhanh.",
    count: "Không giới hạn",
    icon: "听",
    accent: "navy",
  },
  {
    title: "AI Roleplay",
    desc: "AI đóng vai 老板 / khách hàng — chấm ngữ pháp, từ vựng, tự nhiên và sửa câu.",
    count: "Demo + API",
    icon: "AI",
    accent: "orange",
  },
  {
    title: "Luyện thi HSK",
    desc: "Lộ trình HSK gắn với mục tiêu xin việc — không học lan man, học để dùng.",
    count: "HSK 1–3",
    icon: "试",
    accent: "navy",
  },
  {
    title: "XP & Streak",
    desc: "Nhiệm vụ hàng ngày, điểm kinh nghiệm, chuỗi ngày học — giữ nhịp mỗi ngày.",
    count: "4 nhiệm vụ/ngày",
    icon: "火",
    accent: "orange",
  },
];

const bigStats = [
  { value: "600+", label: "Từ vựng HSK" },
  { value: "5", label: "Tình huống đi làm" },
  { value: "1000+", label: "Câu hội thoại mẫu" },
  { value: "146K", label: "Lượt thi HSK VN/năm" },
];

export default function LandingPage() {
  return (
    <div className="overflow-x-hidden bg-white">
      <LandingNav />

      {/* Hero — HiHSK layout + cam/navy style */}
      <section className="relative overflow-hidden bg-gradient-to-br from-[var(--bg-soft)] via-white to-[var(--accent-soft)]">
        {/* Floating Chinese chars background */}
        <div className="hero-zh-watermark pointer-events-none absolute inset-0 select-none" aria-hidden>
          {floatingChars.split("").map((ch, i) => (
            <span
              key={i}
              className="font-zh absolute text-[var(--navy)] opacity-[0.04]"
              style={{
                fontSize: `${48 + (i % 5) * 24}px`,
                top: `${(i * 17) % 85}%`,
                left: `${(i * 23) % 90}%`,
                transform: `rotate(${(i % 7) * 8 - 20}deg)`,
              }}
            >
              {ch}
            </span>
          ))}
        </div>

        <div className="relative mx-auto grid max-w-7xl gap-10 px-4 py-14 md:grid-cols-2 md:items-center md:py-20 lg:gap-16">
          {/* Left — copy + CTA */}
          <div className="animate-fade-up">
            <span className="badge-pill">Nền tảng học tiếng Trung đi làm</span>
            <h1 className="font-display mt-5 text-4xl font-bold uppercase leading-[1.08] text-[var(--navy)] md:text-5xl lg:text-[3.25rem]">
              Chinh phục
              <br />
              <span className="text-[var(--orange)]">Tiếng Trung</span>
              <br />
              để đi làm
            </h1>
            <p className="mt-5 max-w-lg text-base leading-relaxed text-[var(--muted)] md:text-lg">
              Hệ thống học toàn diện — từ vựng HSK, hội thoại công việc, nghe, flashcard, AI roleplay — tất cả trong một nền tảng, tập trung vào mục tiêu{" "}
              <strong className="text-[var(--navy)]">xin việc & tăng thu nhập</strong>.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/register" className="btn btn-primary">
                Bắt đầu học ngay
              </Link>
              <a href="#modules" className="btn btn-navy">
                Khám phá khóa học
              </a>
            </div>
            <div className="mt-8 flex items-center gap-3">
              <div className="flex -space-x-2">
                {["H", "T", "L", "M"].map((l) => (
                  <span
                    key={l}
                    className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-white bg-[var(--navy)] text-xs font-bold text-white"
                  >
                    {l}
                  </span>
                ))}
              </div>
              <p className="text-sm text-[var(--muted)]">
                Hơn <strong className="text-[var(--navy)]">1,000+</strong> người đang thử MVP
              </p>
            </div>
          </div>

          {/* Right — preview card (HiHSK flashcard style) */}
          <div className="relative animate-fade-up md:justify-self-end" style={{ animationDelay: "0.15s" }}>
            <div className="hero-preview-card mx-auto w-full max-w-md">
              <div className="mb-3 flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
                <span>Xem trước bài học</span>
                <span className="rounded bg-[var(--orange)] px-2 py-0.5 text-white">Đi làm</span>
              </div>
              <div className="rounded-sm border-2 border-[var(--navy)] bg-white p-6 shadow-xl">
                <p className="font-zh text-center text-5xl font-bold text-[var(--navy)]">老板</p>
                <p className="mt-2 text-center text-lg text-[var(--orange)]">lǎobǎn</p>
                <p className="mt-1 text-center text-[var(--muted)]">Sếp, chủ</p>
                <div className="mt-5 rounded-sm bg-[var(--bg-soft)] p-3 text-center text-sm text-[var(--ink)]">
                  <span className="font-zh">这个订单什么时候交？</span>
                  <br />
                  <span className="text-[var(--muted)]">Đơn hàng này khi nào giao?</span>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2">
                {[
                  { label: "HSK Level", value: "1–3" },
                  { label: "Streak", value: "7 ngày" },
                  { label: "Từ vựng", value: "600+" },
                ].map((s) => (
                  <div key={s.label} className="rounded-sm border border-[var(--line)] bg-white px-2 py-3 text-center shadow-sm">
                    <p className="font-display text-lg font-bold text-[var(--orange)]">{s.value}</p>
                    <p className="text-[10px] font-semibold uppercase text-[var(--muted)]">{s.label}</p>
                  </div>
                ))}
              </div>
            </div>
            {/* Decorative navy block — industrial accent */}
            <div className="absolute -bottom-4 -left-4 -z-10 h-24 w-24 bg-[var(--navy)] opacity-90" />
            <div className="absolute -right-3 -top-3 -z-10 h-16 w-16 bg-[var(--orange)] opacity-80" />
          </div>
        </div>
      </section>

      {/* Modules grid — HiHSK "11 chuyên mục" style */}
      <section id="modules" className="section-chevron border-y border-[var(--line)] py-16 md:py-20">
        <div className="mx-auto max-w-7xl px-4">
          <div className="text-center">
            <span className="badge-pill badge-pill-outline">Nội dung đa dạng</span>
            <h2 className="font-display mt-4 text-3xl font-bold uppercase text-[var(--navy)] md:text-4xl">
              Tất cả những gì bạn cần
              <br className="hidden sm:block" /> để thành thạo tiếng Trung đi làm
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-[var(--muted)]">
              8 chuyên mục học tập được thiết kế khoa học — từ HSK nền tảng đến hội thoại công việc thực chiến.
            </p>
          </div>

          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {modules.map((m) => (
              <Link
                key={m.title}
                href="/register"
                className="feature-card group flex flex-col overflow-hidden rounded-sm border border-[var(--line)] bg-white shadow-sm transition hover:-translate-y-1 hover:border-[var(--orange)] hover:shadow-lg"
              >
                <div
                  className={`flex h-14 items-center justify-between px-4 ${
                    m.accent === "orange" ? "bg-[var(--orange)]" : "bg-[var(--navy)]"
                  }`}
                >
                  <span className="font-zh text-2xl font-bold text-white/90">{m.icon}</span>
                  <span className="text-xs font-bold uppercase tracking-wide text-white/80">{m.count}</span>
                </div>
                <div className="flex flex-1 flex-col p-4">
                  <h3 className="font-display text-base font-bold uppercase text-[var(--navy)] group-hover:text-[var(--orange-dark)]">
                    {m.title}
                  </h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-[var(--muted)]">{m.desc}</p>
                  <span className="mt-4 text-xs font-bold uppercase text-[var(--orange)]">Bắt đầu →</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Big stats — HiHSK numbers row */}
      <section className="bg-[var(--navy)] py-14 text-white">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-8 px-4 md:grid-cols-4">
          {bigStats.map((s) => (
            <div key={s.label} className="text-center">
              <p className="font-display text-4xl font-bold text-[var(--orange)] md:text-5xl">{s.value}</p>
              <p className="mt-2 text-sm text-white/70">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Skills preview — industrial split section */}
      <section id="skills" className="py-16 md:py-20">
        <div className="mx-auto grid max-w-7xl gap-12 px-4 md:grid-cols-2 md:items-center">
          <div className="relative overflow-hidden rounded-sm shadow-2xl">
            <div
              className="aspect-[4/3] bg-cover bg-center"
              style={{
                backgroundImage:
                  "linear-gradient(135deg, rgba(0,32,96,0.75), rgba(247,147,30,0.35)), url('https://images.unsplash.com/photo-1600880292203-757bb62b4baf?auto=format&fit=crop&w=900&q=80')",
              }}
            />
            <div className="absolute inset-0 flex items-end p-6">
              <div className="border-l-4 border-[var(--orange)] bg-white/95 px-5 py-4 backdrop-blur-sm">
                <p className="font-zh text-2xl font-bold text-[var(--navy)]">因为供应商还没到货</p>
                <p className="mt-1 text-sm text-[var(--muted)]">Nhà cung cấp chưa giao hàng — câu dùng khi báo sếp</p>
              </div>
            </div>
          </div>
          <div>
            <span className="badge-pill badge-pill-outline">AI Teacher</span>
            <h2 className="font-display mt-4 text-3xl font-bold uppercase text-[var(--navy)]">
              Theo dõi tiến độ từng kỹ năng
            </h2>
            <p className="mt-4 text-[var(--muted)]">
              Dashboard cá nhân: từ vựng, nghe, nói, ngữ pháp — AI gợi ý bài luyện phù hợp mỗi ngày.
            </p>
            <div className="mt-8 space-y-5">
              {[
                { label: "Từ vựng", pct: 82 },
                { label: "Nghe", pct: 61 },
                { label: "Nói", pct: 54 },
                { label: "Ngữ pháp", pct: 73 },
              ].map((s) => (
                <div key={s.label}>
                  <div className="mb-2 flex justify-between text-sm font-semibold">
                    <span>{s.label}</span>
                    <span className="text-[var(--orange)]">{s.pct}%</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${s.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Bottom CTA — HiHSK style */}
      <section className="border-t border-[var(--line)] bg-gradient-to-r from-[var(--orange)] to-[#e07d0a] py-16 text-white md:py-20">
        <div className="mx-auto max-w-3xl px-4 text-center">
          <h2 className="font-display text-3xl font-bold uppercase md:text-4xl">
            Sẵn sàng chinh phục tiếng Trung đi làm?
          </h2>
          <p className="mt-4 text-white/90">
            Tham gia cùng người học đang luyện HSK + hội thoại công việc với AI — miễn phí cho MVP.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/register" className="btn btn-navy">
              Đăng ký miễn phí
            </Link>
            <a href="#modules" className="btn border-2 border-white bg-transparent text-white hover:bg-white/10">
              Xem khóa học
            </a>
          </div>
          <p className="mt-5 text-sm text-white/75">Miễn phí — không cần thẻ tín dụng</p>
        </div>
      </section>

      <LandingFooter />
    </div>
  );
}
