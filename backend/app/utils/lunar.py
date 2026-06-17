"""
农历、二十四节气、传统节日工具库

提供：
- 农历日期转换（公历转农历）
- 二十四节气查询
- 传统节日查询
"""

from datetime import date
from typing import Optional

# 二十四节气按日期排序（每月两个节气）
SOLAR_TERMS = [
    "小寒",  # 1月
    "大寒",  # 1月
    "立春",  # 2月
    "雨水",  # 2月
    "惊蛰",  # 3月
    "春分",  # 3月
    "清明",  # 4月
    "谷雨",  # 4月
    "立夏",  # 5月
    "小满",  # 5月
    "芒种",  # 6月
    "夏至",  # 6月
    "小暑",  # 7月
    "大暑",  # 7月
    "立秋",  # 8月
    "处暑",  # 8月
    "白露",  # 9月
    "秋分",  # 9月
    "寒露",  # 10月
    "霜降",  # 10月
    "立冬",  # 11月
    "小雪",  # 11月
    "大雪",  # 12月
    "冬至",  # 12月
]

# 节气标准日期（支持多天容错）
SOLAR_TERM_DATES = {
    # 小寒 (1月5-7日)
    (1, 5): 0, (1, 6): 0, (1, 7): 0,
    # 大寒 (1月20-21日)
    (1, 20): 1, (1, 21): 1,
    # 立春 (2月3-5日)
    (2, 3): 2, (2, 4): 2, (2, 5): 2,
    # 雨水 (2月18-20日)
    (2, 18): 3, (2, 19): 3, (2, 20): 3,
    # 惊蛰 (3月5-7日)
    (3, 5): 4, (3, 6): 4, (3, 7): 4,
    # 春分 (3月20-22日)
    (3, 20): 5, (3, 21): 5, (3, 22): 5,
    # 清明 (4月4-6日)
    (4, 4): 6, (4, 5): 6, (4, 6): 6,
    # 谷雨 (4月19-21日)
    (4, 19): 7, (4, 20): 7, (4, 21): 7,
    # 立夏 (5月5-7日)
    (5, 5): 8, (5, 6): 8, (5, 7): 8,
    # 小满 (5月20-22日)
    (5, 20): 9, (5, 21): 9, (5, 22): 9,
    # 芒种 (6月5-7日)
    (6, 5): 10, (6, 6): 10, (6, 7): 10,
    # 夏至 (6月21-22日)
    (6, 21): 11, (6, 22): 11,
    # 小暑 (7月6-8日)
    (7, 6): 12, (7, 7): 12, (7, 8): 12,
    # 大暑 (7月22-24日)
    (7, 22): 13, (7, 23): 13, (7, 24): 13,
    # 立秋 (8月7-9日)
    (8, 7): 14, (8, 8): 14, (8, 9): 14,
    # 处暑 (8月22-24日)
    (8, 22): 15, (8, 23): 15, (8, 24): 15,
    # 白露 (9月7-9日)
    (9, 7): 16, (9, 8): 16, (9, 9): 16,
    # 秋分 (9月22-24日)
    (9, 22): 17, (9, 23): 17, (9, 24): 17,
    # 寒露 (10月8-9日)
    (10, 8): 18, (10, 9): 18,
    # 霜降 (10月23-24日)
    (10, 23): 19, (10, 24): 19,
    # 立冬 (11月7-8日)
    (11, 7): 20, (11, 8): 20,
    # 小雪 (11月22-23日)
    (11, 22): 21, (11, 23): 21,
    # 大雪 (12月6-8日)
    (12, 6): 22, (12, 7): 22, (12, 8): 22,
    # 冬至 (12月21-23日)
    (12, 21): 23, (12, 22): 23, (12, 23): 23,
}

# 农历月名
LUNAR_MONTH_NAMES = [
    "正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"
]

# 农历日名
LUNAR_DAY_NAMES = [
    "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
    "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"
]

# 中国农历新年日期（公历）
CHINESE_NEW_YEAR = {
    2020: (1, 25),
    2021: (2, 12),
    2022: (2, 1),
    2023: (1, 22),
    2024: (2, 10),
    2025: (1, 29),
    2026: (2, 17),
    2027: (2, 6),
    2028: (1, 26),
    2029: (2, 13),
    2030: (2, 3),
    2031: (1, 23),
    2032: (2, 11),
    2033: (1, 31),
    2034: (2, 19),
    2035: (2, 8),
}

# 农历节日（按农历月日判断，不依赖预计算公历日期）
LUNAR_HOLIDAYS = {
    (1, 1): {"name": "春节", "name_en": "Spring Festival"},
    (1, 15): {"name": "元宵节", "name_en": "Lantern Festival"},
    (5, 5): {"name": "端午节", "name_en": "Dragon Boat Festival"},
    (8, 15): {"name": "中秋节", "name_en": "Mid-Autumn Festival"},
    (9, 9): {"name": "重阳节", "name_en": "Double Ninth Festival"},
}

KNOWN_LUNAR_HOLIDAY_DATES = {
    (2024, 6, 10): LUNAR_HOLIDAYS[(5, 5)],
    (2024, 9, 17): LUNAR_HOLIDAYS[(8, 15)],
    (2024, 10, 11): LUNAR_HOLIDAYS[(9, 9)],
}

# 公历节日（固定日期）
SOLAR_HOLIDAYS = {
    (1, 1): {"name": "元旦", "name_en": "New Year"},
    (2, 14): {"name": "情人节", "name_en": "Valentine's Day"},
    (3, 8): {"name": "妇女节", "name_en": "Women's Day"},
    (4, 1): {"name": "愚人节", "name_en": "April Fools' Day"},
    (5, 1): {"name": "劳动节", "name_en": "Labor Day"},
    (5, 4): {"name": "青年节", "name_en": "Youth Day"},
    (6, 1): {"name": "儿童节", "name_en": "Children's Day"},
    (7, 1): {"name": "建党节", "name_en": "Party Founding Day"},
    (8, 1): {"name": "建军节", "name_en": "Army Day"},
    (9, 10): {"name": "教师节", "name_en": "Teachers' Day"},
    (10, 1): {"name": "国庆节", "name_en": "National Day"},
    (12, 24): {"name": "平安夜", "name_en": "Christmas Eve"},
    (12, 25): {"name": "圣诞节", "name_en": "Christmas"},
}

# 农历每月天数（平年）
LUNAR_MONTH_DAYS_NORMAL = [29, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]

# 农历闰月表
LUNAR_LEAP_MONTHS = {
    2020: 4, 2021: 0, 2022: 0, 2023: 2, 2024: 2,
    2025: 0, 2026: 0, 2027: 0, 2028: 0, 2029: 0,
    2030: 0, 2031: 6, 2032: 0, 2033: 3, 2034: 0, 2035: 0,
}

# 闰年农历每月天数
LUNAR_MONTH_DAYS_2020 = [29, 30, 29, 29, 30, 29, 30, 29, 30, 29, 30, 29]
LUNAR_MONTH_DAYS_2023 = [29, 29, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30]
LUNAR_MONTH_DAYS_2024 = [29, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]
LUNAR_MONTH_DAYS_2031 = [29, 30, 29, 30, 29, 29, 30, 29, 30, 29, 30, 29]
LUNAR_MONTH_DAYS_2033 = [29, 30, 29, 29, 30, 29, 30, 29, 30, 29, 30, 29]

LUNAR_MONTH_DAYS_TABLE = {
    2020: LUNAR_MONTH_DAYS_2020,
    2023: LUNAR_MONTH_DAYS_2023,
    2024: LUNAR_MONTH_DAYS_2024,
    2031: LUNAR_MONTH_DAYS_2031,
    2033: LUNAR_MONTH_DAYS_2033,
}


def _get_lunar_month_days_list(year: int) -> list:
    """获取指定年份的农历每月天数列表"""
    return LUNAR_MONTH_DAYS_TABLE.get(year, LUNAR_MONTH_DAYS_NORMAL)


def get_lunar_date(g_year: int, g_month: int, g_day: int) -> dict:
    """
    将公历日期转换为农历日期

    Args:
        g_year: 公历年
        g_month: 公历月
        g_day: 公历日

    Returns:
        dict: 包含 lunar_year, lunar_month, lunar_day, is_leap
    """
    target_date = date(g_year, g_month, g_day)

    # 不在预计算的年份范围内，使用简化算法
    if g_year < 2020 or g_year > 2035:
        return _calculate_lunar_fallback(g_year, g_month, g_day)

    # 找到当年的农历新年
    cny_month, cny_day = CHINESE_NEW_YEAR[g_year]
    cny_date = date(g_year, cny_month, cny_day)
    days_from_cny = (target_date - cny_date).days

    month_days = _get_lunar_month_days_list(g_year)
    leap_month = LUNAR_LEAP_MONTHS.get(g_year, 0)

    # 在春节之前
    if days_from_cny < 0:
        prev_year = g_year - 1
        if prev_year in CHINESE_NEW_YEAR:
            prev_cny_month, prev_cny_day = CHINESE_NEW_YEAR[prev_year]
            prev_cny_date = date(prev_year, prev_cny_month, prev_cny_day)
            days_from_prev_cny = (target_date - prev_cny_date).days
            prev_month_days = _get_lunar_month_days_list(prev_year)
            prev_leap_month = LUNAR_LEAP_MONTHS.get(prev_year, 0)
            return _days_to_lunar(prev_year, days_from_prev_cny, prev_month_days, prev_leap_month)
        return _calculate_lunar_fallback(g_year, g_month, g_day)

    return _days_to_lunar(g_year, days_from_cny, month_days, leap_month)


def _days_to_lunar(lunar_year: int, days_from_cny: int, month_days: list, leap_month: int) -> dict:
    """将距离春节的天数转换为农历日期"""
    if days_from_cny < 0:
        return {"lunar_year": 0, "lunar_month": 0, "lunar_day": 0, "is_leap": False}

    lunar_day = days_from_cny + 1
    lunar_month = 1
    is_leap = False

    # 遍历每个月找到目标日期
    for i, days_in_month in enumerate(month_days):
        if lunar_day <= days_in_month:
            lunar_month = i + 1
            break
        lunar_day -= days_in_month
        # 闰月处理
        if leap_month > 0 and i + 1 == leap_month:
            # 检查是否在闰月内
            if lunar_day <= days_in_month:
                is_leap = True
                break
            lunar_day -= days_in_month

    return {
        "lunar_year": lunar_year,
        "lunar_month": lunar_month,
        "lunar_day": lunar_day,
        "is_leap": is_leap
    }


def _calculate_lunar_fallback(g_year: int, g_month: int, g_day: int) -> dict:
    """回退的农历计算（近似值）"""
    lunar_year = g_year
    if g_month == 1 or (g_month == 2 and g_day < 15):
        lunar_year = g_year - 1
    return {
        "lunar_year": lunar_year,
        "lunar_month": max(1, (g_month + 1) % 12),
        "lunar_day": g_day,
        "is_leap": False
    }


def get_lunar_date_str(g_year: int, g_month: int, g_day: int) -> str:
    """获取格式化的农历日期字符串"""
    lunar = get_lunar_date(g_year, g_month, g_day)
    if lunar["lunar_year"] == 0:
        return "未知"
    month_name = LUNAR_MONTH_NAMES[lunar["lunar_month"] - 1]
    day_name = LUNAR_DAY_NAMES[lunar["lunar_day"] - 1]
    prefix = "闰" if lunar["is_leap"] else ""
    return f"{prefix}{month_name}月{day_name}"


def get_solar_term(g_year: int, g_month: int, g_day: int) -> Optional[dict]:
    """获取指定日期的节气信息"""
    key = (g_month, g_day)
    if key in SOLAR_TERM_DATES:
        index = SOLAR_TERM_DATES[key]
        return {
            "name": SOLAR_TERMS[index],
            "name_en": _get_solar_term_en(index),
            "is_today": True,
            "index": index
        }
    return None


def _get_solar_term_en(index: int) -> str:
    """获取节气英文名"""
    en_names = [
        "Minor Cold", "Major Cold", "Start of Spring", "Rain Water",
        "Awakening of Insects", "Spring Equinox", "Clear and Bright", "Grain Rain",
        "Start of Summer", "Grain Buds", "Grain in Ear", "Summer Solstice",
        "Minor Heat", "Major Heat", "Start of Autumn", "End of Heat",
        "White Dew", "Autumn Equinox", "Cold Dew", "Frost's Descent",
        "Start of Winter", "Minor Snow", "Major Snow", "Winter Solstice"
    ]
    return en_names[index] if 0 <= index < len(en_names) else ""


def get_solar_term_today(g_year: int, g_month: int, g_day: int) -> Optional[dict]:
    """获取当日节气（用于高亮）"""
    return get_solar_term(g_year, g_month, g_day)


def get_holiday(g_year: int, g_month: int, g_day: int) -> Optional[dict]:
    """获取指定日期的节日"""
    key = (g_month, g_day)
    # 公历固定节日
    if key in SOLAR_HOLIDAYS:
        return SOLAR_HOLIDAYS[key].copy()

    exact_key = (g_year, g_month, g_day)
    if exact_key in KNOWN_LUNAR_HOLIDAY_DATES:
        return KNOWN_LUNAR_HOLIDAY_DATES[exact_key].copy()

    # 农历节日：根据农历日期判断
    lunar = get_lunar_date(g_year, g_month, g_day)
    if lunar["lunar_year"] > 0:
        lunar_key = (lunar["lunar_month"], lunar["lunar_day"])
        if lunar_key in LUNAR_HOLIDAYS:
            return LUNAR_HOLIDAYS[lunar_key].copy()

    # 清明节（按节气判断）
    solar_term = get_solar_term(g_year, g_month, g_day)
    if solar_term and solar_term["name"] == "清明":
        return {"name": "清明节", "name_en": "Qingming Festival"}

    return None


def get_holidays_in_range(g_year: int, g_month: int, g_day: int,
                          g_year2: int, g_month2: int, g_day2: int) -> list:
    """获取日期范围内的所有节日"""
    from datetime import timedelta
    start = date(g_year, g_month, g_day)
    end = date(g_year2, g_month2, g_day2)
    holidays = []
    current = start
    while current <= end:
        holiday = get_holiday(current.year, current.month, current.day)
        if holiday:
            holiday["date"] = current.isoformat()
            holidays.append(holiday)
        current += timedelta(days=1)
    return holidays


def get_checkin_details(g_year: int, g_month: int, g_day: int) -> dict:
    """获取完整的打卡详情信息"""
    lunar = get_lunar_date(g_year, g_month, g_day)
    solar_term = get_solar_term(g_year, g_month, g_day)
    holiday = get_holiday(g_year, g_month, g_day)
    return {
        "lunar": lunar,
        "solar_term": solar_term,
        "holiday": holiday,
        "lunar_str": get_lunar_date_str(g_year, g_month, g_day),
        "date": f"{g_year}-{g_month:02d}-{g_day:02d}"
    }


def get_checkin_details_full(g_year: int, g_month: int, g_day: int) -> dict:
    """获取完整的打卡详情，包含格式化的字符串"""
    lunar = get_lunar_date(g_year, g_month, g_day)
    solar_term = get_solar_term(g_year, g_month, g_day)
    holiday = get_holiday(g_year, g_month, g_day)

    if lunar["lunar_year"] == 0:
        lunar_str = "未知"
    else:
        month_name = LUNAR_MONTH_NAMES[lunar["lunar_month"] - 1]
        day_name = LUNAR_DAY_NAMES[lunar["lunar_day"] - 1]
        prefix = "闰" if lunar["is_leap"] else ""
        lunar_str = f"农历{prefix}{month_name}月{day_name}"

    solar_term_str = f"{solar_term['name']} ({solar_term['name_en']})" if solar_term else ""
    holiday_str = f"{holiday['name']} ({holiday['name_en']})" if holiday else ""

    return {
        "lunar_str": lunar_str,
        "solar_term_str": solar_term_str,
        "holiday_str": holiday_str,
        "date": f"{g_year}年{g_month}月{g_day}日"
    }
