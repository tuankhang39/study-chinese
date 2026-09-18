export const TOPIC_META: Record<string, { label: string; icon: string }> = {
  greeting: { label: "Chào hỏi & Giao tiếp", icon: "👋" },
  pronoun: { label: "Đại từ & Từ hỏi", icon: "🙋" },
  number: { label: "Số & Lượng từ", icon: "🔢" },
  time: { label: "Thời gian", icon: "🕒" },
  family: { label: "Gia đình & Con người", icon: "👨‍👩‍👧" },
  body: { label: "Cơ thể & Sức khỏe", icon: "🩺" },
  food: { label: "Ăn uống", icon: "🍜" },
  house: { label: "Nhà cửa & Đồ vật", icon: "🏠" },
  place: { label: "Nơi chốn & Giao thông", icon: "🚌" },
  direction: { label: "Phương hướng & Vị trí", icon: "🧭" },
  nature: { label: "Thời tiết & Tự nhiên", icon: "🌤️" },
  emotion: { label: "Cảm xúc", icon: "😊" },
  adjective: { label: "Tính từ mô tả", icon: "✨" },
  entertainment: { label: "Giải trí & Thể thao", icon: "🎬" },
  school: { label: "Trường học & Học tập", icon: "📚" },
  work: { label: "Công việc & Đi làm", icon: "💼" },
  verb: { label: "Động từ thông dụng", icon: "🏃" },
  grammar: { label: "Ngữ pháp & Từ nối", icon: "🔗" },
  other: { label: "Khác", icon: "🔖" },
};

export function topicLabel(id: string): string {
  return TOPIC_META[id]?.label || id;
}

export function topicIcon(id: string): string {
  return TOPIC_META[id]?.icon || "🔖";
}

/** Build /flashcards URL for the current HSK / topic / mode filter. */
export function flashcardsHref(opts?: {
  hsk_level?: number;
  topic?: string;
  mode?: "daily" | "study";
}): string {
  const sp = new URLSearchParams();
  if (opts?.mode === "daily") {
    sp.set("mode", "daily");
  } else {
    if (opts?.hsk_level) sp.set("hsk_level", String(opts.hsk_level));
    if (opts?.topic) sp.set("topic", opts.topic);
  }
  const qs = sp.toString();
  return qs ? `/flashcards?${qs}` : "/flashcards";
}
