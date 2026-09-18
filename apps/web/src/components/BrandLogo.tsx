import Image from "next/image";
import Link from "next/link";

type BrandLogoProps = {
  href?: string | null;
  /** header | footer | admin | hero */
  size?: "sm" | "md" | "lg";
  className?: string;
  priority?: boolean;
};

const SIZES = {
  sm: { width: 140, height: 36, className: "h-8 w-auto" },
  md: { width: 180, height: 48, className: "h-10 w-auto sm:h-11" },
  lg: { width: 280, height: 72, className: "h-14 w-auto sm:h-16" },
};

export function BrandLogo({
  href = "/",
  size = "md",
  className = "",
  priority = false,
}: BrandLogoProps) {
  const s = SIZES[size];
  const img = (
    <Image
      src="/logo.png"
      alt="Tiếng Trung đi làm"
      width={s.width}
      height={s.height}
      className={`${s.className} object-contain ${className}`}
      priority={priority}
    />
  );
  if (href == null || href === "") return img;
  return (
    <Link href={href} className="inline-flex shrink-0 items-center" aria-label="Trang chủ">
      {img}
    </Link>
  );
}
