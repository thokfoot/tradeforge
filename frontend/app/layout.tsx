import type { Metadata } from "next";
import { Geist_Mono, Inter } from "next/font/google";
import PwaRegister from "@/components/PwaRegister";
import TauriNotifyInit from "@/components/TauriNotifyInit";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Trade Forge",
  description:
    "Paper trading + backtesting for India, US and Crypto markets (free verified data).",
  manifest: "/manifest.webmanifest",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${geistMono.variable}`}>
      <body>
        {children}
        <PwaRegister />
        <TauriNotifyInit />
      </body>
    </html>
  );
}
