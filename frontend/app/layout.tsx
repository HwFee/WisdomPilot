import type { Metadata } from "next";
import { Inter, Space_Grotesk, Noto_Sans_SC } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const notoSansSC = Noto_Sans_SC({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-noto-sans-sc",
  display: "swap",
});

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
      className={`${inter.variable} ${spaceGrotesk.variable} ${notoSansSC.variable} h-full antialiased`}
    >
      <body className="h-full font-sans">
        <script
          dangerouslySetInnerHTML={{
            __html: `try{if(localStorage.getItem('deck-theme')==='light'){document.documentElement.setAttribute('data-theme','light')}}catch(e){}`,
          }}
        />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
