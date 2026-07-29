"""
时区感知的日期时间辅助函数。

在 WisdomPilot 后端中，所有时间戳统一使用 UTC（协调世界时）存储，
在需要展示时再按用户时区转换。这样可以避免以下常见问题：
- 服务器部署在不同时区导致时间不一致
- 夏令时切换导致时间跳变
- 用户跨时区使用平台时数据错乱

本模块提供标准化的 UTC 时间获取方法，确保全项目时间基准统一。
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    返回当前的 UTC 时间（带时区信息）。

    返回的 datetime 对象携带 timezone.utc 时区信息，而非"朴素"（naive）
    datetime。带时区的 datetime 在与数据库交互、跨时区比较时更安全。

    Returns:
        datetime: 当前 UTC 时间，时区为 timezone.utc。

    使用场景:
        - 为数据库模型的时间戳字段赋默认值
        - 记录事件发生时间（如掌握度事件、交易时间）
        - 计算时间间隔（如两次提交之间的间隔）
    """
    # datetime.now(tz) 返回带指定时区的当前时间
    # 如果不加 tz 参数，返回的是 naive datetime，容易引发时区 bug
    return datetime.now(timezone.utc)
