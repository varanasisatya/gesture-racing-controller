"use client";

import { motion } from "framer-motion";

interface KineticMarqueeProps {
  text: string;
  direction?: "left" | "right";
  speed?: number;
  color?: string;
  outline?: boolean;
}

export function KineticMarquee({ text, direction = "left", speed = 20, color = "#F5F5F0", outline = false }: KineticMarqueeProps) {
  return (
    <div className="relative flex overflow-hidden whitespace-nowrap py-2 w-full select-none pointer-events-none">
      <motion.div
        className="flex whitespace-nowrap"
        animate={{
          x: direction === "left" ? ["0%", "-50%"] : ["-50%", "0%"],
        }}
        transition={{
          repeat: Infinity,
          ease: "linear",
          duration: speed,
        }}
      >
        <span 
          className={`text-[12vw] font-black uppercase tracking-tighter mx-4 ${outline ? 'text-transparent' : ''}`}
          style={{ 
            color: outline ? "transparent" : color,
            WebkitTextStroke: outline ? `2px ${color}` : "none" 
          }}
        >
          {text} • {text} • {text} • {text} • {text} • {text} • 
        </span>
        <span 
          className={`text-[12vw] font-black uppercase tracking-tighter mx-4 ${outline ? 'text-transparent' : ''}`}
          style={{ 
            color: outline ? "transparent" : color,
            WebkitTextStroke: outline ? `2px ${color}` : "none" 
          }}
        >
          {text} • {text} • {text} • {text} • {text} • {text} • 
        </span>
      </motion.div>
    </div>
  );
}
