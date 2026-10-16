"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

function Wheel({ reduced }: { reduced: boolean }) {
  const wheel = useRef<THREE.Group>(null);
  const hub = useRef<THREE.Mesh>(null);
  const spokes = useMemo(() => [0, (Math.PI * 2) / 3, (Math.PI * 4) / 3], []);

  useFrame(({ clock }) => {
    if (!wheel.current || reduced) return;
    const time = clock.elapsedTime;
    wheel.current.rotation.z = Math.sin(time * 0.55) * 0.16;
    wheel.current.rotation.y = Math.sin(time * 0.35) * 0.1;
    if (hub.current) hub.current.rotation.z = Math.sin(time * 0.55) * -0.16;
  });

  return (
    <group ref={wheel} rotation={[0.13, -0.16, -0.08]}>
      <mesh>
        <torusGeometry args={[1.04, 0.065, 12, 96]} />
        <meshStandardMaterial color="#d3fc51" metalness={0.72} roughness={0.24} emissive="#31420d" emissiveIntensity={0.45} />
      </mesh>
      <mesh>
        <torusGeometry args={[0.88, 0.012, 8, 96]} />
        <meshBasicMaterial color="#66e6de" transparent opacity={0.7} />
      </mesh>
      {spokes.map((angle) => (
        <mesh key={angle} position={[Math.sin(angle) * 0.43, Math.cos(angle) * 0.43, 0]} rotation={[0, 0, -angle]}>
          <boxGeometry args={[0.105, 0.82, 0.11]} />
          <meshStandardMaterial color="#eaf0e1" metalness={0.7} roughness={0.3} />
        </mesh>
      ))}
      <mesh ref={hub}>
        <cylinderGeometry args={[0.28, 0.32, 0.16, 8]} />
        <meshStandardMaterial color="#151c22" metalness={0.8} roughness={0.26} emissive="#173c38" emissiveIntensity={0.4} />
      </mesh>
      <mesh position={[0, 0, 0.1]}>
        <circleGeometry args={[0.14, 32]} />
        <meshBasicMaterial color="#66e6de" />
      </mesh>
    </group>
  );
}

export function RacingWheel3D({ reduced }: { reduced: boolean }) {
  return (
    <div className="racing-wheel-3d" aria-hidden="true">
      <Canvas camera={{ position: [0, 0, 4.1], fov: 38 }} dpr={[1, 1.35]} gl={{ alpha: true, antialias: true, powerPreference: "low-power" }}>
        <ambientLight intensity={1.2} />
        <directionalLight position={[3, 4, 5]} intensity={2.2} color="#f2ffdc" />
        <pointLight position={[-3, -1, 3]} intensity={12} color="#66e6de" distance={8} />
        <Wheel reduced={reduced} />
      </Canvas>
    </div>
  );
}
