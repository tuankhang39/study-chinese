const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type User = {
  id: number;
  email: string;
  display_name: string;
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

function authHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
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
    throw new Error(err.detail || "Request failed");
  }
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
};

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
