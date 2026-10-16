"use client";

import React, { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { TorusKnot, Sphere, MeshDistortMaterial } from "@react-three/drei";
import * as THREE from "three";

export default function ChromeRibbon({ scrollY }: { scrollY: number }) {
  const ribbonRef = useRef<THREE.Mesh>(null);
  const sphereRef1 = useRef<THREE.Mesh>(null);
  const sphereRef2 = useRef<THREE.Mesh>(null);

  const chromeMaterial = new THREE.MeshPhysicalMaterial({
    color: "#07090A", // Dark base
    roughness: 0,     // Perfectly smooth
    metalness: 1,     // Fully metallic
    clearcoat: 1,     // Glassy sheen
    clearcoatRoughness: 0,
    reflectivity: 1,
    ior: 1.5,
  });

  useFrame((state) => {
    if (ribbonRef.current) {
      ribbonRef.current.rotation.x = state.clock.elapsedTime * 0.1;
      ribbonRef.current.rotation.y = state.clock.elapsedTime * 0.15;
      
      // Scroll zoom effect for the ribbon
      ribbonRef.current.scale.setScalar(1 + scrollY * 2);
      // Push ribbon slightly back as you scroll
      ribbonRef.current.position.z = scrollY * -5;
    }

    if (sphereRef1.current && sphereRef2.current) {
      // Background spheres floating and zooming
      sphereRef1.current.position.y = Math.sin(state.clock.elapsedTime) * 1 + 2;
      sphereRef2.current.position.y = Math.cos(state.clock.elapsedTime) * 1 - 2;
      
      // Dramatic zoom on scroll
      const sphereScale = 1 + scrollY * 4;
      sphereRef1.current.scale.setScalar(sphereScale);
      sphereRef2.current.scale.setScalar(sphereScale);
      
      sphereRef1.current.rotation.x += 0.01;
      sphereRef2.current.rotation.y += 0.01;
    }
  });

  return (
    <group>
      {/* Central Liquid Chrome Torus Knot (Ribbon/Spiral) */}
      <TorusKnot ref={ribbonRef} args={[2, 0.4, 256, 64]} material={chromeMaterial} />
      
      {/* Floating Distorted Spheres */}
      <Sphere ref={sphereRef1} args={[0.8, 64, 64]} position={[-4, 2, -2]}>
        <MeshDistortMaterial color="#00E5FF" metalness={0.8} roughness={0.2} distort={0.4} speed={2} />
      </Sphere>
      
      <Sphere ref={sphereRef2} args={[1.2, 64, 64]} position={[4, -2, -3]}>
        <MeshDistortMaterial color="#FF3EB5" metalness={0.8} roughness={0.2} distort={0.5} speed={1.5} />
      </Sphere>
    </group>
  );
}
