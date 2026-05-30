"""Tests for Lunar Calendar Utilities"""

import pytest
from datetime import date, datetime


class TestLunarDate:
    """Test lunar date conversion"""

    def test_convert_gregorian_to_lunar_basic(self):
        """Should convert Gregorian date to lunar date"""
        from app.utils.lunar import get_lunar_date

        # 2024-02-10 is Chinese New Year (Spring Festival) - the start of lunar 2024
        lunar = get_lunar_date(2024, 2, 10)
        assert lunar["lunar_year"] == 2024
        assert lunar["lunar_month"] == 1
        assert lunar["lunar_day"] == 1

    def test_convert_gregorian_to_lunar_new_year_2025(self):
        """2025 Chinese New Year is 2025-01-29"""
        from app.utils.lunar import get_lunar_date

        lunar = get_lunar_date(2025, 1, 29)
        assert lunar["lunar_year"] == 2025
        assert lunar["lunar_month"] == 1
        assert lunar["lunar_day"] == 1

    def test_lunar_date_format(self):
        """Should return properly formatted lunar date string"""
        from app.utils.lunar import get_lunar_date_str

        # 2024-02-10 is lunar 2024-1-1
        lunar_str = get_lunar_date_str(2024, 2, 10)
        assert "正月初一" in lunar_str or "农历" in lunar_str

    def test_leap_month(self):
        """Should handle leap months correctly"""
        from app.utils.lunar import get_lunar_date

        # 2024 has a leap month (闰二月)
        lunar = get_lunar_date(2024, 3, 24)
        assert "is_leap" in lunar


class TestSolarTerms:
    """Test 24 solar terms (二十四节气)"""

    def test_get_solar_term_lichun(self):
        """Should return solar term for Lichun (立春)"""
        from app.utils.lunar import get_solar_term

        # 立春 is typically Feb 3-4
        term = get_solar_term(2024, 2, 4)
        assert term is not None
        assert "立春" in term["name"]

    def test_get_solar_term_xiaohan(self):
        """Should return solar term for Minor Cold (小寒)"""
        from app.utils.lunar import get_solar_term

        # 小寒 is typically Jan 5-7
        term = get_solar_term(2024, 1, 6)
        assert term is not None
        assert "小寒" in term["name"]

    def test_get_solar_term_dahanyin(self):
        """Should return solar term for Major Cold (大寒)"""
        from app.utils.lunar import get_solar_term

        # 大寒 is typically Jan 20-21
        term = get_solar_term(2024, 1, 20)
        assert term is not None
        assert "大寒" in term["name"]

    def test_get_solar_term_chunfen(self):
        """Should return solar term for Spring Equinox (春分)"""
        from app.utils.lunar import get_solar_term

        # 春分 is typically Mar 20-21
        term = get_solar_term(2024, 3, 20)
        assert term is not None
        assert "春分" in term["name"]

    def test_get_solar_term_qiufen(self):
        """Should return solar term for Autumn Equinox (秋分)"""
        from app.utils.lunar import get_solar_term

        # 秋分 is typically Sep 22-24
        term = get_solar_term(2024, 9, 23)
        assert term is not None
        assert "秋分" in term["name"]

    def test_get_solar_term_dongzhi(self):
        """Should return solar term for Winter Solstice (冬至)"""
        from app.utils.lunar import get_solar_term

        # 冬至 is typically Dec 21-23
        term = get_solar_term(2024, 12, 21)
        assert term is not None
        assert "冬至" in term["name"]

    def test_get_solar_term_today_highlight(self):
        """Should correctly identify today's solar term for highlighting"""
        from app.utils.lunar import get_solar_term_today

        today = date.today()
        term = get_solar_term_today(today.year, today.month, today.day)
        # Either returns today's term or None if no term today
        assert term is None or "name" in term

    def test_all_solar_terms_listed(self):
        """All 24 solar terms should be available"""
        from app.utils.lunar import SOLAR_TERMS

        expected_terms = [
            "小寒", "大寒", "立春", "雨水", "惊蛰", "春分",
            "清明", "谷雨", "立夏", "小满", "芒种", "夏至",
            "小暑", "大暑", "立秋", "处暑", "白露", "秋分",
            "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"
        ]
        assert len(SOLAR_TERMS) == 24
        for term in expected_terms:
            assert term in SOLAR_TERMS


class TestChineseHolidays:
    """Test traditional Chinese holidays (传统节日)"""

    def test_get_holiday_spring_festival(self):
        """Should identify Spring Festival (春节)"""
        from app.utils.lunar import get_holiday

        # 2024-02-10 is Chinese New Year (Spring Festival)
        holiday = get_holiday(2024, 2, 10)
        assert holiday is not None
        assert "春节" in holiday["name"] or "过年" in holiday["name"]

    def test_get_holiday_qingming(self):
        """2024-04-04 is Qingming Festival (清明节)"""
        from app.utils.lunar import get_holiday

        holiday = get_holiday(2024, 4, 4)
        assert holiday is not None
        assert "清明" in holiday["name"]

    def test_get_holiday_dragon_boat(self):
        """2024-06-10 is Dragon Boat Festival (端午节)"""
        from app.utils.lunar import get_holiday

        holiday = get_holiday(2024, 6, 10)
        assert holiday is not None
        assert "端午" in holiday["name"]

    def test_get_holiday_mid_autumn(self):
        """2024-09-17 is Mid-Autumn Festival (中秋节)"""
        from app.utils.lunar import get_holiday

        holiday = get_holiday(2024, 9, 17)
        assert holiday is not None
        assert "中秋" in holiday["name"]

    def test_get_holiday_double_ninth(self):
        """2024-10-11 is Double Ninth Festival (重阳节)"""
        from app.utils.lunar import get_holiday

        holiday = get_holiday(2024, 10, 11)
        assert holiday is not None
        assert "重阳" in holiday["name"]

    def test_get_holiday_none(self):
        """Should return None for non-holiday dates"""
        from app.utils.lunar import get_holiday

        # A random Tuesday
        holiday = get_holiday(2024, 5, 14)
        assert holiday is None

    def test_get_holidays_in_range(self):
        """Should return all holidays in a date range"""
        from app.utils.lunar import get_holidays_in_range

        holidays = get_holidays_in_range(2024, 1, 1, 2024, 12, 31)
        assert len(holidays) > 0
        # Some holiday should be in there
        assert any("节" in h["name"] or " Festival" in h.get("name_en", "") for h in holidays)


class TestCheckinDetails:
    """Test combined check-in details"""

    def test_get_checkin_details(self):
        """Should return combined lunar, solar term, and holiday info"""
        from app.utils.lunar import get_checkin_details

        # 2024-02-10 is Spring Festival
        details = get_checkin_details(2024, 2, 10)

        assert "lunar" in details
        assert "solar_term" in details
        assert "holiday" in details
        assert "lunar_str" in details

    def test_get_checkin_details_full(self):
        """Should return complete check-in details with formatted strings"""
        from app.utils.lunar import get_checkin_details_full

        details = get_checkin_details_full(2024, 2, 10)

        assert details["lunar_str"] is not None
        assert details["solar_term_str"] is not None or details["solar_term_str"] == ""
        assert details["holiday_str"] is not None or details["holiday_str"] == ""
