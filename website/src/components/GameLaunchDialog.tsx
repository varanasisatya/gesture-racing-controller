"use client";

import { useEffect, useRef, useState, type CSSProperties } from "react";
import { ArrowRight, Camera, Check, CircleAlert, ExternalLink, Hand, LoaderCircle, X } from "lucide-react";
import { FilesetResolver, HandLandmarker, type HandLandmarkerResult } from "@mediapipe/tasks-vision";

type LaunchGame = { name: string; genre: string; keys: string; url: string; accent: string; icon: string; actionLabel?: string; actionKey?: string };

const connections: [number, number][] = [
  [0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],
  [9,13],[13,14],[14,15],[15,16],[13,17],[17,18],[18,19],[19,20],[0,17],
];

function distance(a: {x:number;y:number}, b: {x:number;y:number}) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function jointAngle(a: {x:number;y:number}, b: {x:number;y:number}, c: {x:number;y:number}) {
  const ab = { x: a.x - b.x, y: a.y - b.y };
  const cb = { x: c.x - b.x, y: c.y - b.y };
  const divisor = Math.hypot(ab.x, ab.y) * Math.hypot(cb.x, cb.y);
  if (!divisor) return 0;
  return Math.acos(Math.max(-1, Math.min(1, (ab.x * cb.x + ab.y * cb.y) / divisor))) * 180 / Math.PI;
}

function detectPose(result: HandLandmarkerResult): string {
  const hands = result.landmarks ?? [];
  if (hands.length >= 2) return "TWO HANDS";
  if (!hands[0]) return "none";
  const lm = hands[0];
  const extended = [[5,6,8],[9,10,12],[13,14,16],[17,18,20]].map(([mcp,pip,tip]) => jointAngle(lm[mcp],lm[pip],lm[tip]) > 145 && distance(lm[tip],lm[0]) > distance(lm[pip],lm[0]) * 1.01);
  const count = extended.filter(Boolean).length;
  const thumbJointAngle = jointAngle(lm[2],lm[3],lm[4]);
  const thumbExtended = distance(lm[4],lm[2]) > distance(lm[3],lm[2]) * 1.05 || thumbJointAngle > 135 && distance(lm[4],lm[0]) > distance(lm[3],lm[0]) * 1.01;
  const thumbDeltaY = lm[2].y - lm[4].y;
  const thumbDeltaX = lm[4].x - lm[2].x;
  const thumbIsVertical = Math.abs(thumbDeltaY) > Math.abs(thumbDeltaX) * .82;
  const thumbPose = thumbIsVertical ? (thumbDeltaY >= 0 ? "THUMB UP" : "THUMB DOWN") : (thumbDeltaX < 0 ? "THUMB RIGHT" : "THUMB LEFT");
  const indexVector = { x:lm[8].x-lm[6].x, y:lm[8].y-lm[6].y };
  const indexPose = indexVector.y < -.02 && Math.abs(indexVector.y) > Math.abs(indexVector.x) * .65 ? "POINT UP" : Math.abs(indexVector.x) > Math.abs(indexVector.y) * .9 ? (indexVector.x < 0 ? "POINT RIGHT" : "POINT LEFT") : "POINT";
  const curledOthers = !extended[1] && !extended[2] && !extended[3];
  if (thumbExtended && thumbIsVertical && count <= 1) return thumbPose;
  if (count >= 4) return "OPEN PALM";
  if (extended[0] && curledOthers) return indexPose;
  if (count === 0 && !thumbExtended) return "FIST";
  return "HAND READY";
}

const controls = [
  { id:"POINT UP", icon:"☝", label:"Index finger points up", detail:"Extend only your index finger upward to move forward.", key:"FORWARD · ↑ / W" },
  { id:"OPEN PALM", icon:"🖐", label:"Open palm", detail:"Show your open hand to accelerate forward.", key:"FORWARD · ↑ / W" },
  { id:"THUMB UP", icon:"👍", label:"Thumb points up", detail:"Hold your thumb upright for the game’s mapped action.", key:"NITRO · SPACE" },
  { id:"THUMB DOWN", icon:"👇", label:"Thumb points down", detail:"Point your thumb downward to reverse.", key:"REVERSE · ↓ / S" },
  { id:"FIST", icon:"✊", label:"Close your fist", detail:"Close your hand to brake or stop.", key:"BRAKE · ↓ / S" },
  { id:"POINT LEFT", icon:"←", label:"Index finger points left", detail:"Extend only your index finger horizontally to the left.", key:"TURN LEFT · ← / A" },
  { id:"POINT RIGHT", icon:"→", label:"Index finger points right", detail:"Extend only your index finger horizontally to the right.", key:"TURN RIGHT · → / D" },
];

export function GameLaunchDialog({ game, onClose, onEnter }: { game: LaunchGame; onClose: () => void; onEnter: () => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const landmarkerRef = useRef<HandLandmarker | null>(null);
  const frameRef = useRef<number | null>(null);
  const lastFrameRef = useRef(-1);
  const lastDetectAtRef = useRef(0);
  const mountedRef = useRef(false);
  const [cameraState, setCameraState] = useState<"idle"|"loading"|"ready"|"error">("idle");
  const [cameraMessage, setCameraMessage] = useState("Camera stays on this device. Nothing is recorded or uploaded.");
  const [pose, setPose] = useState("none");

  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      streamRef.current?.getTracks().forEach((track) => track.stop());
      landmarkerRef.current?.close();
    };
  }, []);

  const startCamera = async () => {
    if (cameraState === "loading" || cameraState === "ready") return;
    setCameraState("loading");
    setCameraMessage("Requesting camera access…");
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error("This browser cannot access a camera. Open the site on localhost or HTTPS.");
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } }, audio: false });
      if (!mountedRef.current) { stream.getTracks().forEach((track) => track.stop()); return; }
      streamRef.current = stream;
      const video = videoRef.current;
      if (!video) throw new Error("Camera preview could not be opened.");
      video.srcObject = stream;
      await video.play();
      if (!mountedRef.current) { stream.getTracks().forEach((track) => track.stop()); return; }
      setCameraMessage("Loading the on-device hand tracker…");
      const vision = await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.1.0/wasm");
      const trackerOptions = {
        runningMode: "VIDEO" as const, numHands: 2,
        minHandDetectionConfidence: 0.68, minHandPresenceConfidence: 0.68, minTrackingConfidence: 0.62,
      };
      let landmarker: HandLandmarker;
      try {
        landmarker = await HandLandmarker.createFromOptions(vision, {
          ...trackerOptions, baseOptions: { modelAssetPath: "/models/hand_landmarker.task", delegate: "GPU" },
        });
      } catch {
        landmarker = await HandLandmarker.createFromOptions(vision, {
          ...trackerOptions, baseOptions: { modelAssetPath: "/models/hand_landmarker.task", delegate: "CPU" },
        });
      }
      if (!mountedRef.current) { landmarker.close(); stream.getTracks().forEach((track) => track.stop()); return; }
      landmarkerRef.current = landmarker;
      setCameraState("ready");
      setCameraMessage("Live hand landmarks are being checked on this device.");
      const render = () => {
        const currentVideo = videoRef.current;
        const canvas = canvasRef.current;
        const task = landmarkerRef.current;
        if (currentVideo && canvas && task && currentVideo.readyState >= 2) {
          const now = performance.now();
          if (currentVideo.currentTime !== lastFrameRef.current && now - lastDetectAtRef.current >= 58) {
            lastFrameRef.current = currentVideo.currentTime;
            lastDetectAtRef.current = now;
            const result = task.detectForVideo(currentVideo, now);
            setPose(detectPose(result));
            const width = currentVideo.videoWidth;
            const height = currentVideo.videoHeight;
            if (width && height) {
              if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
              const ctx = canvas.getContext("2d");
              if (ctx) {
                ctx.clearRect(0,0,width,height);
                result.landmarks?.forEach((hand) => {
                  ctx.lineWidth = Math.max(2,width/280);
                  ctx.strokeStyle = game.accent;
                  ctx.shadowColor = game.accent;
                  ctx.shadowBlur = 9;
                  connections.forEach(([a,b]) => { ctx.beginPath();ctx.moveTo(hand[a].x*width,hand[a].y*height);ctx.lineTo(hand[b].x*width,hand[b].y*height);ctx.stroke(); });
                  ctx.shadowBlur = 0;
                  hand.forEach((point,index) => { ctx.beginPath();ctx.fillStyle = [4,8,12,16,20].includes(index) ? "#fff6bf" : game.accent;ctx.arc(point.x*width,point.y*height,index===0?4:3,0,Math.PI*2);ctx.fill(); });
                });
              }
            }
          }
        }
        frameRef.current = requestAnimationFrame(render);
      };
      frameRef.current = requestAnimationFrame(render);
    } catch (cause) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      landmarkerRef.current?.close();
      landmarkerRef.current = null;
      const message = cause instanceof Error ? cause.message : "Camera setup failed. You can still review the controls and enter the game.";
      if (mountedRef.current) {
        setCameraState("error");
        setCameraMessage(message);
      }
    }
  };

  const matchingControl = controls.find((control) => control.id === pose);
  const enter = () => { onEnter(); onClose(); };

  return <div className="launch-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="launch-dialog" role="dialog" aria-modal="true" aria-labelledby="launch-title" style={{"--launch-accent":game.accent} as CSSProperties}>
      <header className="launch-dialog__header"><span className="launch-dialog__eyebrow"><span className="live-dot"/> PRE-RACE CHECK / {game.genre}</span><button className="launch-dialog__close" type="button" aria-label="Close controls" onClick={onClose}><X size={18}/></button></header>
      <div className="launch-dialog__intro"><span className="launch-dialog__game-icon">{game.icon}</span><div><h2 id="launch-title">Controls before launch<span>.</span></h2><p>{game.name} is selected. Check your hand positions, then open the game.</p></div></div>
      <div className="launch-dialog__body">
        <div className="launch-controls"><div className="launch-subhead"><span>YOUR GESTURE MAP</span><span>{controls.length} INPUTS</span></div>{controls.map((control,index)=><div key={control.id} className={`launch-control ${pose===control.id?"launch-control--live":""}`}><span className="launch-control__number">{String(index+1).padStart(2,"0")}</span><span className="launch-control__pose">{control.icon}</span><span className="launch-control__copy"><strong>{control.label}</strong><small>{control.id==="THUMB UP"&&game.actionLabel?`Hold your thumb upright for ${game.actionLabel}.`:control.detail}</small></span><span className="launch-control__key">{control.id==="THUMB UP"&&game.actionKey?game.actionKey:control.key}</span>{pose===control.id&&<span className="launch-control__check"><Check size={13}/> LIVE</span>}</div>)}<p className="launch-controls__hint"><Hand size={15}/> Keep one full hand in frame, fingers separated, and light the hand from the front. Show the gesture until it is highlighted LIVE.</p></div>
        <aside className="camera-check"><div className="camera-check__top"><span><Camera size={14}/> LIVE CAMERA CHECK</span><span className={`camera-check__status camera-check__status--${cameraState}`}>{cameraState==="ready"?"TRACKING":cameraState==="loading"?"STARTING":cameraState==="error"?"OFFLINE":"STANDBY"}</span></div><div className={`camera-check__view ${cameraState==="ready"?"camera-check__view--active":""}`}><video ref={videoRef} muted playsInline aria-label="Mirrored live camera preview"/><canvas ref={canvasRef} aria-hidden="true"/>{cameraState!=="ready"&&<div className="camera-check__empty"><span>{cameraState==="error"?<CircleAlert size={22}/>:cameraState==="loading"?<LoaderCircle className="launch-spin" size={22}/>:<Camera size={22}/>}</span><strong>{cameraState==="error"?"Camera not connected":cameraState==="loading"?"Getting the camera ready":"See your hand live"}</strong><small>{cameraState==="error"?"Review the guide or retry camera access.":"Enable the preview to check your framing and gestures."}</small></div>}<span className="camera-check__corner camera-check__corner--a"/><span className="camera-check__corner camera-check__corner--b"/><span className="camera-check__scan"/></div><div className={`camera-check__pose ${matchingControl?"camera-check__pose--match":""}`}><span><i/>{cameraState==="ready"?(matchingControl?`DETECTED · ${matchingControl.label.toUpperCase()}`:pose==="none"?"NO HAND IN FRAME":pose==="TWO HANDS"?"BOTH HANDS TRACKED":pose=== "HAND READY"?"HAND TRACKED · TRY A SHOWN POSE":`DETECTED · ${pose}`):cameraState==="error"?"PREVIEW UNAVAILABLE":"WAITING FOR CAMERA"}</span>{matchingControl&&<Check size={15}/>}</div><p className="camera-check__privacy">{cameraMessage}</p></aside>
      </div>
      <footer className="launch-dialog__footer"><button className="camera-enable" type="button" onClick={startCamera} disabled={cameraState==="loading"||cameraState==="ready"}>{cameraState==="ready"?<><Check size={15}/> CAMERA READY</>:cameraState==="loading"?<><LoaderCircle className="launch-spin" size={15}/> STARTING CAMERA</>:<><Camera size={15}/> {cameraState==="error"?"RETRY CAMERA":"ENABLE LIVE CAMERA"}</>}</button><button className="enter-game" type="button" onClick={enter}>ENTER GAME <ArrowRight size={16}/><ExternalLink size={13}/></button></footer>
    </section>
  </div>;
}
