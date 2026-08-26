"use client";

import { FormEvent, useEffect, useState } from "react";
import { Modal } from "@/components/admin/Modal";
import { ADMIN_PAGE_SIZE, Pagination } from "@/components/admin/Pagination";
import { api, Plan, Role, User } from "@/lib/api";

const emptyCreate = {
  email: "",
  password: "",
  display_name: "",
  role: "user" as Role,
  plan: "free" as Plan,
};

export default function AdminUsersPage() {
  const [me, setMe] = useState<User | null>(null);
  const [items, setItems] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [form, setForm] = useState(emptyCreate);
  const [editForm, setEditForm] = useState({
    display_name: "",
    role: "user" as Role,
    plan: "free" as Plan,
    password: "",
  });

  const isSuper = me?.role === "super_admin";

  async function load(p = page, query = q) {
    const res = await api.admin.users({
      q: query || undefined,
      page: p,
      page_size: ADMIN_PAGE_SIZE,
    });
    setItems(res.items);
    setTotal(res.total);
    setPage(res.page);
  }

  useEffect(() => {
    api.me().then(setMe).catch(() => setMe(null));
    load(1, "").catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.admin.createUser({
        ...form,
        role: isSuper ? form.role : "user",
        plan: isSuper ? form.plan : "free",
      });
      setForm(emptyCreate);
      setCreateOpen(false);
      await load(1, q);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi tạo user");
    }
  }

  async function onSaveEdit(e: FormEvent) {
    e.preventDefault();
    if (!editing) return;
    setError("");
    try {
      const body: Partial<{ display_name: string; role: Role; plan: Plan; password: string }> = {
        display_name: editForm.display_name,
      };
      if (isSuper) {
        body.role = editForm.role;
        body.plan = editForm.plan;
      }
      if (editForm.password) body.password = editForm.password;
      await api.admin.updateUser(editing.id, body);
      setEditing(null);
      await load(page, q);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi cập nhật");
    }
  }

  async function onDelete(u: User) {
    if (!isSuper) return;
    if (!confirm(`Xóa ${u.email}?`)) return;
    try {
      await api.admin.deleteUser(u.id);
      await load(page, q);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi xóa");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold uppercase text-[var(--navy)]">Users</h1>
          <p className="text-[var(--muted)]">
            Tìm · thêm · sửa · {isSuper ? "đổi role/gói" : "user thường"}
          </p>
        </div>
        <button type="button" className="btn btn-primary text-xs" onClick={() => setCreateOpen(true)}>
          + Thêm user
        </button>
      </div>

      <div className="card-panel flex flex-wrap gap-2 p-3">
        <input
          className="input max-w-sm"
          placeholder="Tìm email / tên"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load(1, q).catch((err) => setError(err.message))}
        />
        <button
          className="btn btn-navy text-xs"
          type="button"
          onClick={() => load(1, q).catch((e) => setError(e.message))}
        >
          Tìm
        </button>
      </div>

      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

      <div className="overflow-x-auto card-panel">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="border-b border-[var(--line)] bg-[var(--bg-soft)]">
            <tr>
              <th className="p-3 font-semibold uppercase tracking-wide text-[var(--muted)]">ID</th>
              <th className="p-3 font-semibold uppercase tracking-wide text-[var(--muted)]">Email</th>
              <th className="p-3 font-semibold uppercase tracking-wide text-[var(--muted)]">Tên</th>
              <th className="p-3 font-semibold uppercase tracking-wide text-[var(--muted)]">Role</th>
              <th className="p-3 font-semibold uppercase tracking-wide text-[var(--muted)]">Gói</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {items.map((u) => (
              <tr key={u.id} className="border-b border-[var(--line)] hover:bg-[var(--accent-soft)]/40">
                <td className="p-3 tabular-nums">{u.id}</td>
                <td className="p-3">{u.email}</td>
                <td className="p-3 font-medium">{u.display_name}</td>
                <td className="p-3">
                  <span className="rounded-sm bg-[var(--bg-soft)] px-2 py-0.5 text-xs font-semibold">{u.role}</span>
                </td>
                <td className="p-3">
                  <span className="rounded-sm bg-[var(--accent-soft)] px-2 py-0.5 text-xs font-semibold text-[var(--orange-dark)]">
                    {u.plan}
                  </span>
                </td>
                <td className="space-x-2 p-3 text-right">
                  <button
                    type="button"
                    className="font-semibold text-[var(--orange)]"
                    onClick={() => {
                      setEditing(u);
                      setEditForm({
                        display_name: u.display_name,
                        role: (u.role as Role) || "user",
                        plan: (u.plan as Plan) || "free",
                        password: "",
                      });
                    }}
                  >
                    Sửa
                  </button>
                  {isSuper && (
                    <button type="button" className="text-[var(--danger)]" onClick={() => onDelete(u)}>
                      Xóa
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageSize={ADMIN_PAGE_SIZE} total={total} onChange={(p) => load(p, q)} />

      <Modal open={createOpen} title="Thêm user" onClose={() => setCreateOpen(false)}>
        <form onSubmit={onCreate} className="grid gap-3">
          <input className="input" placeholder="Email" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input className="input" placeholder="Tên hiển thị" required value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
          <input className="input" placeholder="Mật khẩu" type="password" required minLength={6} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          {isSuper && (
            <div className="grid gap-3 sm:grid-cols-2">
              <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}>
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
              <select className="input" value={form.plan} onChange={(e) => setForm({ ...form, plan: e.target.value as Plan })}>
                <option value="free">free</option>
                <option value="pro">pro</option>
                <option value="unlimit">unlimit</option>
              </select>
            </div>
          )}
          <div className="mt-2 flex justify-end gap-2">
            <button className="btn btn-ghost" type="button" onClick={() => setCreateOpen(false)}>
              Hủy
            </button>
            <button className="btn btn-primary" type="submit">
              Tạo
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={!!editing} title={editing ? `Sửa ${editing.email}` : "Sửa"} onClose={() => setEditing(null)}>
        <form onSubmit={onSaveEdit} className="grid gap-3">
          <input className="input" value={editForm.display_name} onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })} />
          {isSuper && (
            <div className="grid gap-3 sm:grid-cols-2">
              <select className="input" value={editForm.role} onChange={(e) => setEditForm({ ...editForm, role: e.target.value as Role })}>
                <option value="user">user</option>
                <option value="admin">admin</option>
                <option value="super_admin">super_admin</option>
              </select>
              <select className="input" value={editForm.plan} onChange={(e) => setEditForm({ ...editForm, plan: e.target.value as Plan })}>
                <option value="free">free</option>
                <option value="pro">pro</option>
                <option value="unlimit">unlimit</option>
              </select>
            </div>
          )}
          <input className="input" type="password" placeholder="Mật khẩu mới (tuỳ chọn)" value={editForm.password} onChange={(e) => setEditForm({ ...editForm, password: e.target.value })} />
          <div className="mt-2 flex justify-end gap-2">
            <button className="btn btn-ghost" type="button" onClick={() => setEditing(null)}>
              Hủy
            </button>
            <button className="btn btn-primary" type="submit">
              Lưu
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
