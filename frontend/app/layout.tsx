import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "智码领航",
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
      <body className="h-full bg-gray-50 font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
