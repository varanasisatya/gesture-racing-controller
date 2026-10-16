"use client";

import React, { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

export default function AmbientRibbon({ scrollY }: { scrollY: number }) {
  const ribbonRef = useRef<THREE.Mesh>(null);
  const ribbonRef2 = useRef<THREE.Mesh>(null);

  // Generate a smooth curve spanning across the screen
  const curve = useMemo(() => {
    const points = [];
    for (let i = -10; i <= 10; i += 0.5) {
      points.push(new THREE.Vector3(i, Math.sin(i) * 2, 0));
    }
    return new THREE.CatmullRomCurve3(points);
  }, []);

  const chromeMaterial = new THREE.MeshPhysicalMaterial({
    color: "#07090A", 
    roughness: 0.1,    
    metalness: 1,      
    clearcoat: 1,      
    clearcoatRoughness: 0,
    reflectivity: 1,
  });

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    
    if (ribbonRef.current && ribbonRef2.current) {
      // Flowing wave animation
      ribbonRef.current.position.y = Math.sin(t * 0.5) * 0.5;
      ribbonRef.current.rotation.x = Math.sin(t * 0.2) * 0.2;
      
      ribbonRef2.current.position.y = Math.cos(t * 0.4) * -0.5 - 2;
      ribbonRef2.current.rotation.x = Math.cos(t * 0.3) * 0.2;

      // Scroll effect: Move the ribbons down and twist them
      ribbonRef.current.position.y -= scrollY * 5;
      ribbonRef2.current.position.y -= scrollY * 3;
      ribbonRef.current.rotation.z = scrollY * 2;
      ribbonRef2.current.rotation.z = -scrollY * 2;
    }
  });

  return (
    <group position={[0, 0, -2]}>
      {/* Ribbon 1 */}
      <mesh ref={ribbonRef}>
        <tubeGeometry args={[curve, 128, 0.4, 32, false]} />
        <primitive object={chromeMaterial} attach="material" />
      </mesh>
      
      {/* Ribbon 2 (thinner, offsetting) */}
      <mesh ref={ribbonRef2} position={[0, -2, -1]}>
        <tubeGeometry args={[curve, 128, 0.2, 32, false]} />
        <primitive object={chromeMaterial} attach="material" />
      </mesh>
    </group>
  );
}
