"use client";

type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
};

// Builds a compact page-number list with ellipsis, e.g. 1 … 4 5 [6] 7 8 … 20
function pageNumbers(page: number, totalPages: number): (number | "…")[] {
  const pages = new Set<number>([1, totalPages, page, page - 1, page + 1]);
  const sorted = [...pages].filter((p) => p >= 1 && p <= totalPages).sort((a, b) => a - b);
  const out: (number | "…")[] = [];
  let prev = 0;
  for (const p of sorted) {
    if (prev && p - prev > 1) out.push("…");
    out.push(p);
    prev = p;
  }
  return out;
}

export function Pagination({ page, pageSize, total, onChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-[var(--muted)]">
      <p>
        Hiển thị <strong className="text-[var(--ink)]">{from}–{to}</strong> / {total}
      </p>
      <div className="flex flex-wrap items-center gap-1">
        <button
          type="button"
          className="btn btn-ghost px-3 py-1.5 text-xs disabled:opacity-40"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          Trước
        </button>
        {totalPages > 1 &&
          pageNumbers(page, totalPages).map((p, i) =>
            p === "…" ? (
              <span key={`ellipsis-${i}`} className="px-1 text-[var(--muted)]">
                …
              </span>
            ) : (
              <button
                key={p}
                type="button"
                onClick={() => onChange(p)}
                aria-current={p === page ? "page" : undefined}
                className={`min-w-[2rem] rounded-md px-2 py-1.5 text-xs font-semibold transition ${
                  p === page
                    ? "bg-[var(--accent)] text-white"
                    : "text-[var(--ink)] hover:bg-[var(--accent-soft)]"
                }`}
              >
                {p}
              </button>
            )
          )}
        <button
          type="button"
          className="btn btn-ghost px-3 py-1.5 text-xs disabled:opacity-40"
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
        >
          Sau
        </button>
        {totalPages > 8 && (
          <select
            className="input ml-1 max-w-[6rem] py-1.5 text-xs"
            value={page}
            onChange={(e) => onChange(Number(e.target.value))}
            aria-label="Đi tới trang"
          >
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <option key={p} value={p}>
                Trang {p}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  );
}

export const ADMIN_PAGE_SIZE = 20;
