import type { Metadata } from "next";
import { CockpitDashboard } from "@/components/CockpitDashboard";

export const metadata: Metadata = {
  title: "Live Cockpit — Gesture Racing",
  description: "A browser-based gesture controller dashboard with live hand tracking and an offline racing simulator.",
};

export default function DashboardPage() {
  return <CockpitDashboard/>;
}
