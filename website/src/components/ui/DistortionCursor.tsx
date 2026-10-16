"use client";

import { useEffect, useState } from "react";
import { motion, useSpring } from "framer-motion";

export function DistortionCursor() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);

  useEffect(() => {
    const updateMousePosition = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
      
      // Check if hovering over interactive elements
      const target = e.target as HTMLElement;
      if (target.tagName.toLowerCase() === 'button' || target.closest('button')) {
        setIsHovering(true);
      } else {
        setIsHovering(false);
      }
    };

    window.addEventListener("mousemove", updateMousePosition);
    return () => window.removeEventListener("mousemove", updateMousePosition);
  }, []);

  const springConfig = { damping: 25, stiffness: 300, mass: 0.5 };
  const cursorX = useSpring(mousePosition.x - (isHovering ? 60 : 40), springConfig);
  const cursorY = useSpring(mousePosition.y - (isHovering ? 60 : 40), springConfig);

  return (
    <>
      <motion.div
        className="fixed top-0 left-0 z-50 pointer-events-none rounded-full flex items-center justify-center mix-blend-difference backdrop-invert backdrop-blur-[2px]"
        style={{
          x: cursorX,
          y: cursorY,
          width: isHovering ? 120 : 80,
          height: isHovering ? 120 : 80,
          border: "2px solid #C8FF00",
          backgroundColor: isHovering ? "rgba(200, 255, 0, 0.1)" : "transparent",
        }}
      />
      
      {/* Tiny center dot */}
      <motion.div
        className="fixed top-0 left-0 z-50 pointer-events-none rounded-full bg-[#00E5FF] mix-blend-difference"
        style={{
          x: mousePosition.x - 4,
          y: mousePosition.y - 4,
          width: 8,
          height: 8,
        }}
      />
    </>
  );
}
