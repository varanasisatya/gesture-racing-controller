import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { GamepadCursor } from "@/components/ui/GamepadCursor";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Gesture Racing — Drive by Instinct",
  description:
    "Turn hand gestures into real-time racing controls. An open source webcam-powered gesture controller built with OpenCV and MediaPipe.",
  keywords: ["gesture controller", "hand tracking", "racing game", "MediaPipe", "OpenCV", "touchless gaming"],
  openGraph: {
    title: "Gesture Racing — Drive by Instinct",
    description: "Your hands are the wheel. A webcam is the controller.",
    type: "website",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      data-scroll-behavior="smooth"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}<GamepadCursor/></body>
    </html>
  );
}
