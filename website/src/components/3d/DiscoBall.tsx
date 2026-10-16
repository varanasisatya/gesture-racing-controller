"use client";

import React, { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Icosahedron } from "@react-three/drei";
import * as THREE from "three";

export default function DiscoBall({ scrollY }: { scrollY: number }) {
  const ballRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (ballRef.current) {
      // Fast, constant rotation for the disco ball
      ballRef.current.rotation.y = state.clock.elapsedTime * 0.8;
      ballRef.current.rotation.z = state.clock.elapsedTime * 0.2;
      
      // Scroll effect: move ball up or down slightly
      ballRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.2 + (scrollY * 2);
    }
  });

  return (
    <group position={[0, 0, 0]}>
      {/* 
        Using Icosahedron with detail 6 generates thousands of faces.
        Combined with flatShading, it creates a true 4K realistic mirror ball.
      */}
      <Icosahedron ref={ballRef} args={[2.5, 6]}>
        <meshPhysicalMaterial 
          color="#ffffff"
          metalness={1}
          roughness={0.1}
          flatShading={true} 
          clearcoat={1}
          clearcoatRoughness={0.1}
          envMapIntensity={5}
        />
      </Icosahedron>
    </group>
  );
}
