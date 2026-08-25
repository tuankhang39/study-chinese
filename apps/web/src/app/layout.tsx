import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { fontClassName } from "@/lib/fonts";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tiếng Trung đi làm",
  description: "Học tiếng Trung theo hướng nghề nghiệp và từ vựng HSK cho người Việt",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi" className={fontClassName}>
      <body className="antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
