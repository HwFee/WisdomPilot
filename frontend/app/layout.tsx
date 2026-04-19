import type { Metadata } from "next";
import "./globals.css";
import { AIContextProvider } from "@/contexts/AIContext";

export const metadata: Metadata = {
  title: "GAI 编程教学平台",
  description: "基于生成式AI的程序设计类课程实践教学系统",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh"
      suppressHydrationWarning
      className="h-full antialiased"
    >
      <head></head>
      <body className="h-full bg-gray-50 font-sans"><AIContextProvider>{children}</AIContextProvider></body>
    </html>
  );
}
