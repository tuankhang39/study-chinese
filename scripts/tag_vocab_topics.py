#!/usr/bin/env python3
"""Tag every vocabulary row with a `topic` for topic-based study tabs.

Classification is done by exact hanzi lookup (reliable, independent of the
often-messy `meaning_vi` text inherited from CC-CEDICT), with a part-of-speech
based fallback for anything not explicitly listed so every row ends up with a
non-null topic.

Idempotent — safe to re-run any time after seeding/adding new vocab.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, "/app")

from app.core.database import SessionLocal
from app.models import Vocabulary

# ---------------------------------------------------------------------------
# Topic buckets: (topic_id, label_vi) -> ordered; first match wins.
# ---------------------------------------------------------------------------

TOPICS: list[tuple[str, str]] = [
    ("greeting", "Chào hỏi & Giao tiếp"),
    ("pronoun", "Đại từ & Từ hỏi"),
    ("number", "Số & Lượng từ"),
    ("time", "Thời gian"),
    ("family", "Gia đình & Con người"),
    ("body", "Cơ thể & Sức khỏe"),
    ("food", "Ăn uống"),
    ("house", "Nhà cửa & Đồ vật"),
    ("place", "Nơi chốn & Giao thông"),
    ("direction", "Phương hướng & Vị trí"),
    ("nature", "Thời tiết & Tự nhiên"),
    ("emotion", "Cảm xúc"),
    ("adjective", "Tính từ mô tả"),
    ("entertainment", "Giải trí & Thể thao"),
    ("school", "Trường học & Học tập"),
    ("work", "Công việc & Đi làm"),
    ("verb", "Động từ thông dụng"),
    ("grammar", "Ngữ pháp & Từ nối"),
    ("other", "Khác"),
]
TOPIC_LABEL = dict(TOPICS)

HANZI_TOPIC: dict[str, str] = {}


def add(topic: str, hanzi_list: list[str]) -> None:
    for h in hanzi_list:
        HANZI_TOPIC[h] = topic


add(
    "greeting",
    [
        "不客气", "对不起", "没关系", "谢谢", "请", "再见", "喂", "姓", "叫",
        "认识", "介绍", "欢迎", "打电话", "说话", "告诉", "回答", "问",
    ],
)

add(
    "pronoun",
    [
        "我", "你", "他", "她", "我们", "它", "您", "大家", "别人", "自己",
        "谁", "什么", "哪", "那", "这", "怎么", "怎么样", "多少", "为什么", "每", "其他",
    ],
)

add(
    "number",
    [
        "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
        "百", "千", "万", "零", "两", "第一", "几",
        "个", "本", "件", "块", "张", "双", "条", "辆", "位", "些",
        "公斤", "米", "段", "层", "种", "半", "次", "一会儿", "一共", "角",
    ],
)

add(
    "time",
    [
        "今天", "明天", "昨天", "现在", "以前", "以后", "刚才", "已经", "正在",
        "一直", "终于", "马上", "时候", "时间", "年", "月", "日", "星期",
        "分钟", "小时", "点", "早上", "上午", "中午", "下午", "晚上", "周末",
        "春", "夏", "秋", "冬", "季节", "过去", "去年", "最近", "生日", "号",
    ],
)

add(
    "family",
    [
        "爸爸", "妈妈", "哥哥", "姐姐", "弟弟", "妹妹", "儿子", "女儿",
        "爷爷", "奶奶", "叔叔", "阿姨", "丈夫", "妻子", "孩子", "朋友",
        "同学", "同事", "邻居", "老师", "学生", "医生", "先生", "小姐",
        "男人", "女人", "人", "客人", "老板", "经理", "校长", "司机",
        "服务员", "名字",
    ],
)

add(
    "body",
    [
        "头发", "脸", "眼睛", "鼻子", "耳朵", "脚", "身体", "生病", "感冒",
        "发烧", "疼", "舒服", "健康", "累", "渴", "饿", "胖", "瘦", "矮",
        "药", "医院",
    ],
)

add(
    "food",
    [
        "吃", "喝", "菜", "茶", "米饭", "面包", "面条", "鸡蛋", "苹果",
        "香蕉", "西瓜", "葡萄", "牛奶", "咖啡", "啤酒", "果汁", "糖", "甜",
        "饭馆", "菜单", "好吃", "蛋糕", "羊肉",
    ],
)

add(
    "house",
    [
        "杯子", "桌子", "椅子", "电脑", "电视", "电子", "手机", "手表",
        "书", "铅笔", "字典", "照相机", "照片", "黑板", "灯", "冰箱",
        "空调", "衣服", "裤子", "鞋", "衬衫", "裙子", "帽子", "眼镜",
        "行李箱", "筷子", "碗", "盘子", "伞", "东西", "房间", "厨房", "洗手间",
    ],
)

add(
    "place",
    [
        "北京", "中国", "出租车", "火车站", "机场", "银行", "公园",
        "图书馆", "花园", "超市", "宾馆", "城市", "国家", "地方", "世界",
        "街道", "地铁", "公共汽车", "飞机", "自行车", "船", "路", "附近",
    ],
)

add(
    "direction",
    [
        "后面", "前面", "左边", "右边", "旁边", "里", "外", "上", "下",
        "东", "南", "西", "北方", "中间",
    ],
)

add(
    "nature",
    [
        "天气", "冷", "热", "晴", "雪", "太阳", "月亮", "云", "河",
        "动物", "鸟", "狗", "猫", "熊猫", "鱼", "树", "草", "花",
        "颜色", "红", "黄", "蓝", "绿", "黑", "白", "环境",
    ],
)

add(
    "emotion",
    [
        "高兴", "快乐", "喜欢", "爱", "爱好", "难过", "生气", "害怕",
        "担心", "放心", "满意", "着急", "热情", "安静", "可爱", "兴趣", "关心",
    ],
)

add(
    "adjective",
    [
        "大", "小", "多", "少", "高", "长", "短", "快", "慢", "贵",
        "便宜", "好", "坏", "重要", "容易", "难", "简单", "方便", "干净",
        "新", "旧", "老", "年轻", "漂亮", "聪明", "认真", "努力", "奇怪",
        "新鲜", "有名", "一样", "相同", "突然", "当然", "一般", "真",
        "极", "差", "清楚", "明白", "近", "远", "久",
    ],
)

add(
    "entertainment",
    [
        "电影", "音乐", "唱歌", "跳舞", "游戏", "旅游", "爬山", "踢",
        "跑步", "游泳", "打篮球", "表演", "玩", "运动", "画", "故事", "新闻",
    ],
)

add(
    "school",
    [
        "学校", "教室", "课", "考试", "复习", "练习", "作业", "成绩",
        "年级", "词语", "句子", "历史", "数学", "体育", "文化",
        "普通话", "汉语", "水平", "字", "意思",
    ],
)

add(
    "work",
    [
        "工作", "上班", "公司", "会议", "机会", "订单", "生产", "质检",
        "部署", "延期", "供应商", "请假", "办公室", "打算",
    ],
)

add(
    "verb",
    [
        "去", "来", "走", "坐", "站", "住", "做", "看", "看见", "听",
        "写", "读", "买", "卖", "穿", "用", "拿", "放", "开", "关",
        "睡觉", "起床", "休息", "教", "懂", "知道", "帮助", "帮忙", "送",
        "给", "借", "换", "找", "选择", "决定", "准备", "打扫", "洗",
        "洗澡", "刷", "搬", "带", "举行", "参加", "检查", "解决", "发现",
        "注意", "记得", "忘记", "相信", "以为", "觉得", "希望", "需要",
        "愿意", "应该", "能", "可以", "会", "要", "想", "让", "使",
        "遇到", "经过", "出现", "提高", "变化", "表示", "迟到", "进",
        "出", "到", "回", "完成", "完", "讲", "接", "敢", "骑", "要求",
    ],
)

add(
    "grammar",
    [
        "的", "了", "吗", "呢", "吧", "着", "得", "和", "跟", "或者",
        "但是", "所以", "因为", "而且", "虽然", "然后", "如果", "还是",
        "不", "没", "也", "都", "很", "太", "非常", "几乎", "才", "就",
        "把", "被", "从", "向", "离", "为", "为了", "除了", "根据",
        "关于", "比", "比较", "地", "只", "其实", "越",
    ],
)


def fallback_topic(part_of_speech: str | None) -> str:
    pos = (part_of_speech or "").lower()
    tags = set(pos.split(","))
    if "r" in tags:
        return "pronoun"
    if "m" in tags or "q" in tags:
        return "number"
    if "t" in tags:
        return "time"
    if "f" in tags:
        return "direction"
    if "a" in tags or "an" in tags or "ad" in tags:
        return "adjective"
    if any(t in tags for t in ("v", "vn")):
        return "verb"
    if "n" in tags or "ns" in tags or "nz" in tags or "nr" in tags:
        return "other"
    if any(t in tags for t in ("d", "c", "p", "u", "y", "e", "b", "g")):
        return "grammar"
    return "other"


def main() -> None:
    db = SessionLocal()
    try:
        rows = db.query(Vocabulary).all()
        counts: dict[str, int] = {}
        unmatched = 0
        for v in rows:
            topic = HANZI_TOPIC.get(v.hanzi)
            if not topic:
                topic = fallback_topic(v.part_of_speech)
                unmatched += 1
            v.topic = topic
            counts[topic] = counts.get(topic, 0) + 1
        db.commit()

        print(f"Tagged {len(rows)} vocab rows. Explicit hanzi matches: {len(rows) - unmatched}, fallback: {unmatched}")
        for topic_id, label in TOPICS:
            n = counts.get(topic_id, 0)
            if n:
                print(f"  {topic_id:14s} {label:28s} {n}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
