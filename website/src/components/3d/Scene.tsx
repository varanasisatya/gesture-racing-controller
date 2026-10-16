"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, ScrollControls, useScroll } from "@react-three/drei";
import DiscoBall from "./DiscoBall";
import { useState, useRef } from "react";
import * as THREE from "three";

function SceneContent() {
  const scroll = useScroll();
  const [scrollY, setScrollY] = useState(0);
  const lightsRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    setScrollY(scroll.offset);
    if (lightsRef.current) {
      // Rotate the lights around the disco ball rapidly to create sweeping reflections
      lightsRef.current.rotation.y = state.clock.elapsedTime * 1.5;
      lightsRef.current.rotation.z = state.clock.elapsedTime * 0.8;
      lightsRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.5);
    }
  });

  return (
    <>
      <DiscoBall scrollY={scrollY} />
      <Environment preset="studio" />
      <ambientLight intensity={0.1} color="#07090A" />
      
      <group ref={lightsRef}>
        <pointLight position={[5, 0, 0]} intensity={10} color="#FF3EB5" distance={20} />
        <pointLight position={[-5, 0, 0]} intensity={10} color="#C8FF00" distance={20} />
        <pointLight position={[0, 0, 5]} intensity={10} color="#00E5FF" distance={20} />
        <pointLight position={[0, 5, -5]} intensity={10} color="#8B5CFF" distance={20} />
      </group>
    </>
  );
}

export default function Scene() {
  return (
    <div className="absolute inset-0 z-0 pointer-events-none h-[120vh]">
      <Canvas camera={{ position: [0, 0, 8], fov: 45 }}>
        <ScrollControls pages={3} damping={0.1}>
          <SceneContent />
        </ScrollControls>
      </Canvas>
    </div>
  );
}
