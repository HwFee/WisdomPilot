import type { Metadata } from "next";
import { MasteryPathPageClient } from "./page-client";

export const metadata: Metadata = {
  title: "学习路径 - 智码领航",
  description: "系统化的编程学习路径，AI 辅助闯关",
};

export default function Page() {
  return <MasteryPathPageClient />;
}
