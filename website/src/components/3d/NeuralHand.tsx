"use client";

import React, { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { Sphere } from "@react-three/drei";
import * as THREE from "three";

// Rough normalized coordinates for a 3D hand (MediaPipe skeleton structure)
const HAND_POINTS = [
  [0, -2, 0], // 0: Wrist
  [-1, -1, 0.5], [-1.5, 0, 0.8], [-1.8, 1, 1], [-2, 2, 1.2], // Thumb
  [-0.5, 0, 0], [-0.7, 1.5, -0.2], [-0.8, 2.5, -0.4], [-0.9, 3.5, -0.5], // Index
  [0, 0.2, -0.1], [0, 1.8, -0.3], [0, 2.8, -0.5], [0, 3.8, -0.6], // Middle
  [0.5, 0, -0.2], [0.7, 1.6, -0.4], [0.8, 2.6, -0.6], [0.9, 3.5, -0.7], // Ring
  [1, -0.2, -0.3], [1.2, 1.2, -0.5], [1.3, 2, -0.6], [1.4, 2.8, -0.7], // Pinky
];

const CONNECTIONS = [
  [0,1], [1,2], [2,3], [3,4],
  [0,5], [5,6], [6,7], [7,8],
  [5,9], [9,10], [10,11], [11,12],
  [9,13], [13,14], [14,15], [15,16],
  [13,17], [17,18], [18,19], [19,20],
  [0,17]
];

export default function NeuralHand({ scrollY }: { scrollY: number }) {
  const groupRef = useRef<THREE.Group>(null);
  const nodesRef = useRef<THREE.Group>(null);

  // Colors
  const chromeMaterial = new THREE.MeshPhysicalMaterial({
    color: "#0F1315",
    roughness: 0.1,
    metalness: 1,
    clearcoat: 1,
  });

  const neonPinkMaterial = new THREE.MeshStandardMaterial({
    color: "#FF3EB5",
    emissive: "#FF3EB5",
    emissiveIntensity: 2,
    toneMapped: false,
  });
  
  const neonCyanMaterial = new THREE.MeshStandardMaterial({
    color: "#00E5FF",
    emissive: "#00E5FF",
    emissiveIntensity: 2,
    toneMapped: false,
  });

  // Calculate midpoints and lengths for cylinders
  const lines = useMemo(() => {
    return CONNECTIONS.map(([start, end]) => {
      const p1 = new THREE.Vector3(...HAND_POINTS[start]);
      const p2 = new THREE.Vector3(...HAND_POINTS[end]);
      const distance = p1.distanceTo(p2);
      const position = p1.clone().lerp(p2, 0.5);
      
      // Calculate rotation to align cylinder with the two points
      const quaternion = new THREE.Quaternion();
      const up = new THREE.Vector3(0, 1, 0);
      const direction = new THREE.Vector3().subVectors(p2, p1).normalize();
      quaternion.setFromUnitVectors(up, direction);
      const euler = new THREE.Euler().setFromQuaternion(quaternion);
      
      return { position, rotation: [euler.x, euler.y, euler.z], length: distance };
    });
  }, []);

  useFrame((state) => {
    if (!groupRef.current || !nodesRef.current) return;
    
    // Smooth mouse follow
    const targetX = (state.pointer.x * Math.PI) / 4;
    const targetY = (state.pointer.y * Math.PI) / 4;
    
    groupRef.current.rotation.x += 0.05 * (-targetY - groupRef.current.rotation.x);
    groupRef.current.rotation.y += 0.05 * (targetX - groupRef.current.rotation.y);

    // Idle floating animation
    groupRef.current.position.y = Math.sin(state.clock.elapsedTime) * 0.2;

    // Scroll-based explosion effect
    // As scrollY increases (0 to 1), the nodes shatter outward
    const shatterFactor = scrollY * 5; // How far they fly apart
    
    nodesRef.current.children.forEach((child, index) => {
      // It's a sphere node or a line connection? We only scatter spheres for cool effect
      if (child.userData.isNode) {
        const originalPos = new THREE.Vector3(...HAND_POINTS[index]);
        // Push outward from center
        const pushDir = originalPos.clone().normalize();
        
        // Add some chaos
        pushDir.x += Math.sin(index + state.clock.elapsedTime) * 0.5;
        pushDir.y += Math.cos(index - state.clock.elapsedTime) * 0.5;
        
        child.position.lerp(
          originalPos.clone().add(pushDir.multiplyScalar(shatterFactor)),
          0.1
        );
      }
    });
  });

  return (
    <group ref={groupRef} scale={0.8} position={[0, -0.5, 0]}>
      <group ref={nodesRef}>
        {/* Render Spheres for Landmarks */}
        {HAND_POINTS.map((pos, i) => {
          // Highlight tips (4, 8, 12, 16, 20) with Cyan, Wrist with Pink
          const isTip = [4, 8, 12, 16, 20].includes(i);
          const isWrist = i === 0;
          const material = isTip ? neonCyanMaterial : isWrist ? neonPinkMaterial : chromeMaterial;
          const radius = isTip || isWrist ? 0.2 : 0.15;
          
          return (
            <Sphere 
              key={`node-${i}`} 
              args={[radius, 32, 32]} 
              position={pos as [number, number, number]} 
              material={material}
              userData={{ isNode: true }}
            />
          );
        })}

        {/* Render Connections */}
        {lines.map((line, i) => (
          <mesh 
            key={`line-${i}`} 
            position={line.position.toArray()} 
            rotation={line.rotation as [number, number, number]}
          >
            <cylinderGeometry args={[0.02, 0.02, line.length, 8]} />
            <meshStandardMaterial 
              color="#8B5CFF" 
              emissive="#8B5CFF" 
              emissiveIntensity={1} 
              transparent 
              opacity={0.6} 
            />
          </mesh>
        ))}
      </group>
    </group>
  );
}
