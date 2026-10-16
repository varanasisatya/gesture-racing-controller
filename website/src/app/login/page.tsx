import type { Metadata } from "next";
import { LoginForm } from "@/components/LoginForm";

export const metadata: Metadata = {
  title: "Player Sign In — Gesture Racing",
  description: "Sign in to your Gesture Racing player account.",
};

export default function LoginPage() {
  return <LoginForm/>;
}
