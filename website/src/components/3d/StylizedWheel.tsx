"use client";

import React, { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Torus, Cylinder, Sphere } from "@react-three/drei";
import * as THREE from "three";

export default function StylizedWheel() {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!groupRef.current) return;
    
    // Constant rotation for the steering wheel
    groupRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.5) * 0.5;

    // React to mouse for tilt
    const targetX = (state.pointer.x * Math.PI) / 4;
    const targetY = (state.pointer.y * Math.PI) / 4;
    
    groupRef.current.rotation.x += 0.05 * (-targetY - groupRef.current.rotation.x);
    groupRef.current.rotation.y += 0.05 * (targetX - groupRef.current.rotation.y);
  });

  const materialDark = new THREE.MeshPhysicalMaterial({
    color: "#0F1315",
    roughness: 0.2,
    metalness: 0.8,
    clearcoat: 1,
  });

  const materialLime = new THREE.MeshStandardMaterial({
    color: "#DFFF3F",
    emissive: "#DFFF3F",
    emissiveIntensity: 2,
    toneMapped: false,
  });
  
  const materialCyan = new THREE.MeshStandardMaterial({
    color: "#00F5FF",
    emissive: "#00F5FF",
    emissiveIntensity: 2,
    toneMapped: false,
    wireframe: true,
  });

  return (
    <group ref={groupRef} scale={1.5}>
      {/* Outer Wheel Ring */}
      <Torus args={[2, 0.15, 32, 64]} material={materialDark} />
      
      {/* Glowing Inner Tech Ring */}
      <Torus args={[1.7, 0.02, 16, 64]} material={materialCyan} />
      
      {/* Center Hub */}
      <Sphere args={[0.4, 32, 32]} material={materialDark} />
      
      {/* Left Grip Indicator */}
      <mesh position={[-1.9, 0, 0]} material={materialLime}>
        <capsuleGeometry args={[0.16, 0.8, 4, 16]} />
      </mesh>
      
      {/* Right Grip Indicator */}
      <mesh position={[1.9, 0, 0]} material={materialLime}>
        <capsuleGeometry args={[0.16, 0.8, 4, 16]} />
      </mesh>

      {/* Spokes */}
      <Cylinder args={[0.05, 0.05, 1.6, 16]} position={[-0.9, 0, 0]} rotation={[0, 0, Math.PI / 2]} material={materialDark} />
      <Cylinder args={[0.05, 0.05, 1.6, 16]} position={[0.9, 0, 0]} rotation={[0, 0, Math.PI / 2]} material={materialDark} />
      <Cylinder args={[0.05, 0.05, 1.5, 16]} position={[0, -0.8, 0]} material={materialDark} />
    </group>
  );
}
