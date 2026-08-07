import type { Metadata } from "next";
import { Geist_Mono } from "next/font/google";
import PwaRegister from "@/components/PwaRegister";
import "./globals.css";

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
    <html lang="en" className={geistMono.variable}>
      <body>
        {children}
        <PwaRegister />
      </body>
    </html>
  );
}
