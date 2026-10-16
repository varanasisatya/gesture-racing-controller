"use client";

import React, { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { MeshDistortMaterial, Sphere } from "@react-three/drei";
import * as THREE from "three";

export default function AbstractNeuralWeb() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!meshRef.current) return;
    
    // Slow, organic rotation
    meshRef.current.rotation.x += 0.001;
    meshRef.current.rotation.y += 0.002;

    // Smoothly track mouse position to slightly tilt the shape
    const targetX = (state.pointer.x * Math.PI) / 6;
    const targetY = (state.pointer.y * Math.PI) / 6;

    meshRef.current.rotation.x += 0.02 * (targetY - meshRef.current.rotation.x);
    meshRef.current.rotation.y += 0.02 * (targetX - meshRef.current.rotation.y);
  });

  return (
    <group>
      {/* Subtle ambient light for dark surfaces */}
      <ambientLight intensity={0.4} color="#07090A" />
      
      {/* Acid Lime Light */}
      <directionalLight position={[10, 10, 5]} intensity={2.5} color="#DFFF3F" />
      {/* Electric Cyan Light */}
      <directionalLight position={[-10, -10, -5]} intensity={3.5} color="#00F5FF" />
      {/* Supporting Blue Fill */}
      <pointLight position={[0, -5, 5]} intensity={1.5} color="#38BDF8" />

      {/* Main Glass/Liquid Blob (Manus style) */}
      <Sphere ref={meshRef} args={[1.5, 64, 64]} scale={1.2}>
        <MeshDistortMaterial
          color="#0F1315" // Dark surface color
          attach="material"
          distort={0.4}
          speed={1.5}
          roughness={0.1}
          metalness={0.9}
          clearcoat={1}
          clearcoatRoughness={0.1}
          envMapIntensity={2.5}
        />
      </Sphere>
    </group>
  );
}
