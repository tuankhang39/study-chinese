const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001";

export type Role = "user" | "admin" | "super_admin";
export type Plan = "free" | "pro" | "unlimit";

export type User = {
  id: number;
  email: string;
  display_name: string;
  role?: Role;
  plan?: Plan;
  xp: number;
  level: number;
  streak: number;
  last_active_date?: string | null;
};

export type Vocab = {
  id: number;
  hanzi: string;
  traditional?: string | null;
  pinyin: string;
  meaning_vi: string;
  meaning_en?: string | null;
  hsk_level: number;
  part_of_speech?: string | null;
  example_zh?: string | null;
  example_vi?: string | null;
  image_url?: string | null;
  frequency?: number | null;
};

export type Card = {
  id: number;
  due: string;
  reps: number;
  lapses: number;
  state: number;
  vocab: Vocab;
};

export type MissionTask = {
  id: string;
  title: string;
  xp: number;
  done: boolean;
  target: number;
  progress: number;
};

export type Mission = {
  id: number;
  mission_date: string;
  tasks: MissionTask[];
  completed: boolean;
  xp_awarded: number;
};

export type HomeData = {
  user: User;
  mission: Mission;
  due_count: number;
  continue_track: "hsk" | "work";
  tip: string;
};

export type Scenario = {
  id: number;
  track: string;
  job_tag?: string | null;
  title: string;
  description: string;
  starter_lines: string[];
  difficulty: number;
  prompt_system?: string;
};

export type RoleplaySession = {
  id: number;
  scenario_id: number;
  messages: { role: string; zh: string; vi?: string }[];
  scores?: {
    grammar?: number;
    vocabulary?: number;
    naturalness?: number;
    corrected_zh?: string;
    corrected_vi?: string;
    feedback_vi?: string;
  } | null;
};

export type AdminDashboard = {
  users: number;
  vocab: number;
  scenarios: number;
  by_plan: Record<string, number>;
  by_role: Record<string, number>;
  users_new_7d?: number;
  google_users?: number;
  roleplay_sessions?: number;
  user_cards?: number;
  by_hsk?: Record<string, number>;
  paid_users?: number;
};

export type Course = {
  id: number;
  slug: string;
  title: string;
  title_en?: string | null;
  description: string;
  hsk_level: number;
  cover_image_url?: string | null;
  published: boolean;
  coming_soon?: boolean;
  sort_order: number;
  lesson_count?: number;
  progress_percent?: number | null;
};

export type LessonSection = {
  id: number;
  lesson_id: number;
  sort_order: number;
  section_type: string;
  title: string;
  content: string;
  content_json?: Record<string, unknown> | null;
  image_url?: string | null;
  page_ref?: number | null;
};

export type LessonItem = {
  id: number;
  lesson_id: number;
  step_id?: number | null;
  sort_order: number;
  item_type: string;
  hanzi?: string | null;
  pinyin?: string | null;
  meaning_vi?: string | null;
  meaning_en?: string | null;
  audio_text?: string | null;
  speaker?: string | null;
  image_url?: string | null;
  source_page?: number | null;
  meta?: {
    quiz_kind?: string;
    options?: string[];
    answer?: string;
    [k: string]: unknown;
  } | null;
};

export type LessonStep = {
  id: number;
  lesson_id: number;
  step_key: string;
  title_vi: string;
  sort_order: number;
  required: boolean;
  items: LessonItem[];
};

export type Lesson = {
  id: number;
  course_id: number;
  number: number;
  title_zh: string;
  title_vi?: string | null;
  title_en?: string | null;
  title_pinyin?: string | null;
  lesson_type?: string;
  estimated_minutes?: number;
  unlock_rule?: string;
  objectives?: unknown[] | null;
  grammar_points?: unknown[] | null;
  page_start?: number | null;
  page_end?: number | null;
  cover_image_url?: string | null;
  published: boolean;
  section_count?: number;
  step_count?: number;
  locked?: boolean;
  progress_percent?: number | null;
  sections?: LessonSection[];
  steps?: LessonStep[];
};

export type LessonProgress = {
  lesson_id: number;
  completed_section_ids: number[];
  completed_step_keys?: string[];
  item_results?: Record<string, unknown> | null;
  percent: number;
  completed: boolean;
  completed_at?: string | null;
  cards_added?: number;
};

export type LessonPlayer = {
  lesson: Lesson;
  steps: LessonStep[];
  progress: LessonProgress;
  next_lesson_id?: number | null;
  source_pages: string[];
};

export type PageResult<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

function authHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function formatError(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object" && "error" in detail) {
    return String((detail as { error: unknown }).error);
  }
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === "object" && d && "msg" in d ? String(d.msg) : String(d))).join("; ");
  }
  return fallback;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(formatError(err.detail, "Request failed"));
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  register: (body: { email: string; password: string; display_name: string }) =>
    request<{ access_token: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  login: (body: { email: string; password: string }) =>
    request<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  me: () => request<User>("/api/auth/me"),
  googleStatus: () => request<{ enabled: boolean }>("/api/auth/google/status"),
  googleStartUrl: () => `${API_URL}/api/auth/google/start`,
  home: () => request<HomeData>("/api/home"),
  vocab: (params?: { hsk_level?: number; q?: string }) => {
    const sp = new URLSearchParams();
    if (params?.hsk_level) sp.set("hsk_level", String(params.hsk_level));
    if (params?.q) sp.set("q", params.q);
    const qs = sp.toString();
    return request<Vocab[]>(`/api/vocab${qs ? `?${qs}` : ""}`);
  },
  dueCards: () => request<Card[]>("/api/cards/due"),
  reviewCard: (id: number, rating: "again" | "hard" | "good" | "easy") =>
    request<Card>(`/api/cards/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ rating }),
    }),
  scenarios: (job_tag?: string) => {
    const sp = new URLSearchParams({ track: "work" });
    if (job_tag) sp.set("job_tag", job_tag);
    return request<Scenario[]>(`/api/scenarios?${sp}`);
  },
  startRoleplay: (scenario_id: number) =>
    request<RoleplaySession>("/api/roleplay/sessions", {
      method: "POST",
      body: JSON.stringify({ scenario_id }),
    }),
  sendRoleplay: (session_id: number, message: string) =>
    request<RoleplaySession>(`/api/roleplay/sessions/${session_id}/message`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
  listeningNext: (hsk_level?: number) => {
    const qs = hsk_level ? `?hsk_level=${hsk_level}` : "";
    return request<{ vocab: Vocab; options: string[]; answer_index: number }>(
      `/api/listening/next${qs}`
    );
  },
  listeningComplete: (correct: boolean) =>
    request<{ ok: boolean }>(`/api/listening/complete?correct=${correct}`, {
      method: "POST",
    }),

  admin: {
    dashboard: () => request<AdminDashboard>("/api/admin/dashboard"),
    users: (params?: { q?: string; role?: string; plan?: string; page?: number; page_size?: number }) => {
      const sp = new URLSearchParams();
      if (params?.q) sp.set("q", params.q);
      if (params?.role) sp.set("role", params.role);
      if (params?.plan) sp.set("plan", params.plan);
      if (params?.page) sp.set("page", String(params.page));
      if (params?.page_size) sp.set("page_size", String(params.page_size));
      const qs = sp.toString();
      return request<PageResult<User>>(`/api/admin/users${qs ? `?${qs}` : ""}`);
    },
    createUser: (body: {
      email: string;
      password: string;
      display_name: string;
      role?: Role;
      plan?: Plan;
    }) =>
      request<User>("/api/admin/users", { method: "POST", body: JSON.stringify(body) }),
    updateUser: (
      id: number,
      body: Partial<{ display_name: string; role: Role; plan: Plan; password: string }>
    ) =>
      request<User>(`/api/admin/users/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    deleteUser: (id: number) =>
      request<{ ok: boolean }>(`/api/admin/users/${id}`, { method: "DELETE" }),
    vocab: (params?: { q?: string; hsk_level?: number; page?: number; page_size?: number }) => {
      const sp = new URLSearchParams();
      if (params?.q) sp.set("q", params.q);
      if (params?.hsk_level) sp.set("hsk_level", String(params.hsk_level));
      if (params?.page) sp.set("page", String(params.page));
      if (params?.page_size) sp.set("page_size", String(params.page_size));
      const qs = sp.toString();
      return request<PageResult<Vocab>>(`/api/admin/vocab${qs ? `?${qs}` : ""}`);
    },
    createVocab: (body: Partial<Vocab> & { hanzi: string; pinyin: string; meaning_vi: string; hsk_level: number }) =>
      request<Vocab>("/api/admin/vocab", { method: "POST", body: JSON.stringify(body) }),
    updateVocab: (id: number, body: Partial<Vocab>) =>
      request<Vocab>(`/api/admin/vocab/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    deleteVocab: (id: number) =>
      request<{ ok: boolean }>(`/api/admin/vocab/${id}`, { method: "DELETE" }),
    scenarios: (params?: { q?: string; track?: string; page?: number; page_size?: number }) => {
      const sp = new URLSearchParams();
      if (params?.q) sp.set("q", params.q);
      if (params?.track) sp.set("track", params.track);
      if (params?.page) sp.set("page", String(params.page));
      if (params?.page_size) sp.set("page_size", String(params.page_size));
      const qs = sp.toString();
      return request<PageResult<Scenario>>(`/api/admin/scenarios${qs ? `?${qs}` : ""}`);
    },
    createScenario: (body: {
      track: string;
      title: string;
      description: string;
      prompt_system: string;
      job_tag?: string;
      starter_lines?: string[];
      difficulty?: number;
    }) =>
      request<Scenario>("/api/admin/scenarios", { method: "POST", body: JSON.stringify(body) }),
    updateScenario: (id: number, body: Partial<Scenario> & { prompt_system?: string }) =>
      request<Scenario>(`/api/admin/scenarios/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    deleteScenario: (id: number) =>
      request<{ ok: boolean }>(`/api/admin/scenarios/${id}`, { method: "DELETE" }),

    curriculumCourses: (params?: { page?: number; page_size?: number }) => {
      const sp = new URLSearchParams();
      if (params?.page) sp.set("page", String(params.page));
      if (params?.page_size) sp.set("page_size", String(params.page_size));
      const qs = sp.toString();
      return request<PageResult<Course>>(`/api/admin/curriculum/courses${qs ? `?${qs}` : ""}`);
    },
    getCurriculumCourse: async (id: number) => {
      const res = await request<PageResult<Course>>(`/api/admin/curriculum/courses?page=1&page_size=100`);
      const course = res.items.find((c) => c.id === id);
      if (!course) throw new Error("Không tìm thấy giáo trình");
      return course;
    },
    createCurriculumCourse: (body: {
      slug: string;
      title: string;
      title_en?: string | null;
      description?: string;
      hsk_level: number;
      cover_image_url?: string | null;
      published?: boolean;
      coming_soon?: boolean;
      sort_order?: number;
    }) => request<Course>("/api/admin/curriculum/courses", { method: "POST", body: JSON.stringify(body) }),
    updateCurriculumCourse: (
      id: number,
      body: Partial<{
        slug: string;
        title: string;
        title_en: string | null;
        description: string;
        hsk_level: number;
        cover_image_url: string | null;
        published: boolean;
        coming_soon: boolean;
        sort_order: number;
      }>
    ) =>
      request<Course>(`/api/admin/curriculum/courses/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    deleteCurriculumCourse: (id: number) =>
      request<{ ok: boolean }>(`/api/admin/curriculum/courses/${id}`, { method: "DELETE" }),
    curriculumLessons: (params?: { course_id?: number; page?: number; page_size?: number }) => {
      const sp = new URLSearchParams();
      if (params?.course_id) sp.set("course_id", String(params.course_id));
      if (params?.page) sp.set("page", String(params.page));
      if (params?.page_size) sp.set("page_size", String(params.page_size));
      const qs = sp.toString();
      return request<PageResult<Lesson>>(`/api/admin/curriculum/lessons${qs ? `?${qs}` : ""}`);
    },
    curriculumLesson: (id: number) =>
      request<Lesson>(`/api/admin/curriculum/lessons/${id}`),
    createCurriculumLesson: (body: Partial<Lesson> & { course_id: number; number: number; title_zh: string }) =>
      request<Lesson>("/api/admin/curriculum/lessons", { method: "POST", body: JSON.stringify(body) }),
    updateCurriculumLesson: (id: number, body: Partial<Lesson>) =>
      request<Lesson>(`/api/admin/curriculum/lessons/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    deleteCurriculumLesson: (id: number) =>
      request<{ ok: boolean }>(`/api/admin/curriculum/lessons/${id}`, { method: "DELETE" }),
    createCurriculumSection: (body: {
      lesson_id: number;
      sort_order?: number;
      section_type: string;
      title?: string;
      content?: string;
      image_url?: string | null;
      page_ref?: number | null;
    }) => request<LessonSection>("/api/admin/curriculum/sections", { method: "POST", body: JSON.stringify(body) }),
    updateCurriculumSection: (id: number, body: Partial<LessonSection>) =>
      request<LessonSection>(`/api/admin/curriculum/sections/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    deleteCurriculumSection: (id: number) =>
      request<{ ok: boolean }>(`/api/admin/curriculum/sections/${id}`, { method: "DELETE" }),
    seedHsk1: (replace = false) =>
      request<{
        ok: boolean;
        lessons?: number;
        steps?: number;
        items?: number;
        vocab_links?: number;
        ocr_draft_used?: boolean;
        message?: string;
      }>(`/api/admin/curriculum/seed-hsk1?replace=${replace}`, { method: "POST" }),
    createCurriculumItem: (body: Partial<LessonItem> & { lesson_id: number; item_type: string }) =>
      request<LessonItem>("/api/admin/curriculum/items", { method: "POST", body: JSON.stringify(body) }),
    updateCurriculumItem: (id: number, body: Partial<LessonItem>) =>
      request<LessonItem>(`/api/admin/curriculum/items/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    deleteCurriculumItem: (id: number) =>
      request<{ ok: boolean }>(`/api/admin/curriculum/items/${id}`, { method: "DELETE" }),
    createCurriculumStep: (body: {
      lesson_id: number;
      step_key: string;
      title_vi?: string;
      sort_order?: number;
      required?: boolean;
    }) => request<LessonStep>("/api/admin/curriculum/steps", { method: "POST", body: JSON.stringify(body) }),
    updateCurriculumStep: (id: number, body: Partial<LessonStep>) =>
      request<LessonStep>(`/api/admin/curriculum/steps/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    deleteCurriculumStep: (id: number) =>
      request<{ ok: boolean }>(`/api/admin/curriculum/steps/${id}`, { method: "DELETE" }),
    uploadCurriculumImage: async (file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API_URL}/api/admin/curriculum/upload`, {
        method: "POST",
        headers: { ...authHeaders() },
        body: fd,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(formatError(err.detail, "Upload failed"));
      }
      return res.json() as Promise<{ image_url: string }>;
    },
  },

  catalog: () => request<Course[]>("/api/curriculum/catalog"),
  courses: () => request<Course[]>("/api/curriculum/courses"),
  courseLessons: (slug: string) => request<Lesson[]>(`/api/curriculum/courses/${slug}/lessons`),
  lesson: (id: number) => request<Lesson>(`/api/curriculum/lessons/${id}`),
  lessonPlayer: (id: number) => request<LessonPlayer>(`/api/curriculum/lessons/${id}/player`),
  lessonProgress: (id: number) => request<LessonProgress>(`/api/curriculum/lessons/${id}/progress`),
  updateLessonProgress: (
    id: number,
    body: {
      completed_section_ids?: number[];
      completed_step_keys?: string[];
      item_results?: Record<string, unknown>;
      completed?: boolean;
      push_to_fsrs?: boolean;
    }
  ) =>
    request<LessonProgress>(`/api/curriculum/lessons/${id}/progress`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

export function mediaUrl(path?: string | null): string | undefined {
  if (!path) return undefined;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export function speakZh(text: string) {
  if (typeof window === "undefined" || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "zh-CN";
  u.rate = 0.9;
  const voices = window.speechSynthesis.getVoices();
  const zh = voices.find((v) => v.lang.toLowerCase().startsWith("zh"));
  if (zh) u.voice = zh;
  window.speechSynthesis.speak(u);
}

export function isAdminRole(role?: string | null) {
  return role === "admin" || role === "super_admin";
}
