"use client";

import { useEffect, useState } from "react";
import { motion, useMotionValue, useReducedMotion } from "framer-motion";
import { Gamepad2 } from "lucide-react";

export function GamepadCursor() {
  const reduce = useReducedMotion();
  const x = useMotionValue(-40);
  const y = useMotionValue(-40);
  const [hovering, setHovering] = useState(false);

  useEffect(() => {
    const move = (event: PointerEvent) => {
      if (event.pointerType === "touch") return;
      x.set(event.clientX - 11);
      y.set(event.clientY - 11);
      const overInteractive = event.target instanceof Element && Boolean(event.target.closest("a,button,[role='button']"));
      setHovering((current) => current === overInteractive ? current : overInteractive);
    };
    window.addEventListener("pointermove", move, { passive: true });
    return () => window.removeEventListener("pointermove", move);
  }, [x, y]);

  return <motion.div className="gamepad-cursor" aria-hidden="true" style={{ x, y }} animate={{ scale: hovering ? 1.08 : 1 }} transition={{ duration: reduce ? 0 : .08, ease: "linear" }}><span className="gamepad-cursor__halo"/><Gamepad2 size={16} strokeWidth={1.8}/><i className="gamepad-cursor__spark gamepad-cursor__spark--one"/><i className="gamepad-cursor__spark gamepad-cursor__spark--two"/></motion.div>;
}
