export const BEIJING_DAY_FORMATTER = new Intl.DateTimeFormat("zh-CN", {
  timeZone: "Asia/Shanghai",
  year: "numeric",
  month: "numeric",
  day: "numeric",
});

const BEIJING_TIME_FORMATTER = new Intl.DateTimeFormat("zh-CN", {
  timeZone: "Asia/Shanghai",
  hour: "2-digit",
  minute: "2-digit",
});

const BEIJING_DATETIME_FORMATTER = new Intl.DateTimeFormat("zh-CN", {
  timeZone: "Asia/Shanghai",
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function normalizeDateStr(dateStr: string): string {
  if (!dateStr.endsWith("Z") && !dateStr.includes("+") && !dateStr.includes("T")) {
    return dateStr.replace(" ", "T") + "Z";
  }
  if (dateStr.includes("T") && !dateStr.endsWith("Z") && !dateStr.includes("+")) {
    return dateStr + "Z";
  }
  return dateStr;
}

export function formatDate(dateStr: string): string {
  const normalizedDateStr = normalizeDateStr(dateStr);
  const date = new Date(normalizedDateStr);
  const now = new Date();

  const dateBeijingStr = BEIJING_DAY_FORMATTER.format(date);
  const nowBeijingStr = BEIJING_DAY_FORMATTER.format(now);

  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (dateBeijingStr === nowBeijingStr) {
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours === 0) {
      const minutes = Math.floor(diff / (1000 * 60));
      if (minutes < 1) return "刚刚";
      return `${minutes}分钟前`;
    }
    return `${hours}小时前`;
  }
  if (days === 1 || (days === 0 && dateBeijingStr !== nowBeijingStr)) {
    return "昨天 " + BEIJING_TIME_FORMATTER.format(date);
  }
  if (days < 7) {
    return `${days}天前`;
  }
  return BEIJING_DATETIME_FORMATTER.format(date);
}
