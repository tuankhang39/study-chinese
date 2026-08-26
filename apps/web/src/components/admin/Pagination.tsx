"use client";

type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
};

export function Pagination({ page, pageSize, total, onChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-[var(--muted)]">
      <p>
        Hiển thị <strong className="text-[var(--ink)]">{from}–{to}</strong> / {total} · Trang{" "}
        <strong className="text-[var(--ink)]">
          {page}/{totalPages}
        </strong>
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="btn btn-ghost px-3 py-1.5 text-xs disabled:opacity-40"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          Trước
        </button>
        <button
          type="button"
          className="btn btn-ghost px-3 py-1.5 text-xs disabled:opacity-40"
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
        >
          Sau
        </button>
      </div>
    </div>
  );
}

export const ADMIN_PAGE_SIZE = 20;
