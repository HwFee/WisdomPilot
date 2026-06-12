import type { Metadata } from "next";
import { ArenaPageClient } from "./page-client";

export const metadata: Metadata = {
  title: "竞技场 - 智码领航",
  description: "与其他学习者切磋，在实战中检验知识掌握程度",
};

export default function Page() {
  return <ArenaPageClient />;
}
