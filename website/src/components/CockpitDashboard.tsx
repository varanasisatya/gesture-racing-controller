"use client";

import { useCallback, useEffect, useRef, useState, type CSSProperties, type FormEvent, type KeyboardEvent } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Activity, ArrowDownRight, ArrowLeft, ArrowUpRight, AudioLines, Camera, Cable, Check, Crosshair, Focus, Gamepad2, Hand, Gauge, LoaderCircle, Maximize2, Plus, RotateCcw, ShieldCheck, Square, X, Zap } from "lucide-react";
import { FilesetResolver, HandLandmarker, type HandLandmarkerResult } from "@mediapipe/tasks-vision";

type DriveAction = "IDLE" | "LEFT" | "RIGHT" | "GAS" | "BRAKE" | "REVERSE" | "ACTION";
type ControlState = { steering: "STRAIGHT" | "LEFT" | "RIGHT"; pedal: "IDLE" | "GAS" | "BRAKE" | "REVERSE"; nitro: boolean };
const idleControls: ControlState = { steering:"STRAIGHT", pedal:"IDLE", nitro:false };
type ControlMode = "racing" | "runner" | "arcade" | "air_mouse";
type Profile = { id: string; name: string; genre: string; icon: string; url: string; mode: ControlMode; accent: string; controls: [string, string, string][] };

const defaultProfiles: Profile[] = [
  { id:"circuit", name:"Circuit Racing", genre:"CIRCUIT RACING", icon:"🏁", url:"https://www.crazygames.com/game/circuit-racing", mode:"racing", accent:"#d3fc51", controls:[["Index point up","Accelerate / forward","↑ / W"],["Thumb up","Nitro","SPACE"],["Thumb down","Reverse","↓ / S"],["Closed fist","Brake / stop","↓ / S"],["Index point left","Turn left","← / A"],["Index point right","Turn right","→ / D"]] },
  { id:"rally", name:"Rally Racer Dirt", genre:"OFFROAD RACING", icon:"🚙", url:"https://www.crazygames.com/game/rally-racer-dirt", mode:"racing", accent:"#68e6de", controls:[["Index point up","Accelerate / forward","↑ / W"],["Thumb up","Nitro","SPACE"],["Thumb down","Reverse","↓ / S"],["Closed fist","Brake / stop","↓ / S"],["Index point left","Turn left","← / A"],["Index point right","Turn right","→ / D"]] },
  { id:"night-city", name:"Night City Racing", genre:"CITY RACING", icon:"🌃", url:"https://www.crazygames.com/game/night-city-racing", mode:"arcade", accent:"#f679c7", controls:[["Index point up","Accelerate / forward","↑ / W"],["Thumb up","Nitro","SHIFT"],["Thumb down","Reverse","↓ / S"],["Closed fist","Brake / stop","↓ / S"],["Index point left","Turn left","← / A"],["Index point right","Turn right","→ / D"]] },
  { id:"moto-x3m", name:"Moto X3M", genre:"STUNT BIKE RACING", icon:"🏍️", url:"https://www.crazygames.com/game/moto-x3m", mode:"racing", accent:"#ff9d57", controls:[["Index point up","Accelerate / forward","↑ / W"],["Thumb up","Nitro","SPACE"],["Thumb down","Reverse / brake","↓ / S"],["Closed fist","Brake / stop","↓ / S"],["Index point left","Turn left / tilt","← / A"],["Index point right","Turn right / tilt","→ / D"]] },
  { id:"drift-hunters", name:"Drift Hunters", genre:"DRIFT RACING", icon:"🛞", url:"https://www.crazygames.com/game/drift-hunters", mode:"racing", accent:"#68e6de", controls:[["Index point up","Accelerate / forward","↑ / W"],["Thumb up","Nitro","SPACE"],["Thumb down","Reverse","↓ / S"],["Closed fist","Brake / handbrake","SPACE"],["Index point left","Turn left","← / A"],["Index point right","Turn right","→ / D"]] },
  { id:"crazy-grand-prix", name:"Crazy Grand Prix", genre:"FORMULA RACING", icon:"🏎️", url:"https://www.crazygames.com/game/crazy-grand-prix", mode:"racing", accent:"#b49aff", controls:[["Index point up","Accelerate / forward","↑ / W"],["Thumb up","Nitro","SPACE"],["Thumb down","Reverse","↓ / S"],["Closed fist","Brake / stop","↓ / S"],["Index point left","Turn left","← / A"],["Index point right","Turn right","→ / D"]] },
  { id:"real-car-driving", name:"Real Car Driving", genre:"3D CITY SIMULATOR", icon:"🚗", url:"https://www.crazygames.com/game/real-car-driving", mode:"racing", accent:"#68e6de", controls:[["Index point up","Accelerate / forward","↑ / W"],["Thumb up","Handbrake (SPACE)","SPACE"],["Thumb down","Reverse","↓ / S"],["Closed fist","Brake / stop","↓ / S"],["Index point left","Turn left","← / A"],["Index point right","Turn right","→ / D"]] },
  { id:"runner", name:"Endless Runner", genre:"ARCADE RUNNER", icon:"🏃", url:"https://www.crazygames.com", mode:"runner", accent:"#b49aff", controls:[["Swipe / thumb left","Dodge left","← Left Arrow"],["Swipe / thumb right","Dodge right","→ Right Arrow"],["Swipe up / open palm","Jump","↑ Up Arrow"],["Swipe down / fist","Slide","↓ Down Arrow"]] },
];

const handLinks: [number, number][] = [[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[17,18],[18,19],[19,20],[0,17]];
const distance = (a: {x:number;y:number}, b: {x:number;y:number}) => Math.hypot(a.x-b.x,a.y-b.y);
const angle = (a: {x:number;y:number}, b: {x:number;y:number}, c: {x:number;y:number}) => {
  const ab={x:a.x-b.x,y:a.y-b.y}, cb={x:c.x-b.x,y:c.y-b.y}, d=Math.hypot(ab.x,ab.y)*Math.hypot(cb.x,cb.y);
  return d ? Math.acos(Math.max(-1,Math.min(1,(ab.x*cb.x+ab.y*cb.y)/d)))*180/Math.PI : 0;
};

function readSinglePose(lm: HandLandmarkerResult["landmarks"][number], directionalDeadzone: number) {
  const fingers=[[5,6,8],[9,10,12],[13,14,16],[17,18,20]].map(([m,p,t])=>angle(lm[m],lm[p],lm[t])>145&&distance(lm[t],lm[0])>distance(lm[p],lm[0])*1.01);
  const count=fingers.filter(Boolean).length;
  const palm=Math.max(distance(lm[5],lm[17]),.001);
  const pinch=distance(lm[4],lm[8])<palm*.34;
  const thumbJointAngle=angle(lm[2],lm[3],lm[4]);
  const thumbExtension=distance(lm[4],lm[2])>distance(lm[3],lm[2])*1.05||thumbJointAngle>135&&distance(lm[4],lm[0])>distance(lm[3],lm[0])*1.01;
  const thumbTip=lm[4],thumbBase=lm[2],thumbDeltaY=thumbBase.y-thumbTip.y,thumbDeltaX=thumbTip.x-thumbBase.x;
  const thumbVertical=Math.abs(thumbDeltaY)>Math.abs(thumbDeltaX)*.82;
  const thumbDirection=thumbVertical?(thumbDeltaY>=0?"THUMB UP":"THUMB DOWN"):(thumbDeltaX<0?"THUMB RIGHT":"THUMB LEFT");
  const indexVector={x:lm[8].x-lm[6].x,y:lm[8].y-lm[6].y};
  const horizontalDeviation=Math.atan2(Math.abs(indexVector.y),Math.abs(indexVector.x))*180/Math.PI;
  const indexPoint=indexVector.y<-.02&&Math.abs(indexVector.y)>Math.abs(indexVector.x)*.65?"POINT UP":horizontalDeviation<=directionalDeadzone?(indexVector.x<0?"POINT RIGHT":"POINT LEFT"):"POINT";
  const curledOthers=!fingers[1]&&!fingers[2]&&!fingers[3];
  const pose=thumbExtension&&thumbVertical&&count<=1?thumbDirection:count>=4?"OPEN PALM":pinch?"PINCH":fingers[0]&&curledOthers?indexPoint:count===0&&!thumbExtension?"FIST":fingers[0]&&count===2?"PEACE":"HAND READY";
  return {pose,fingers:count,rawAngle:Math.atan2(lm[9].y-lm[0].y,lm[9].x-lm[0].x)*180/Math.PI+90};
}

function readPose(result: HandLandmarkerResult, directionalDeadzone = 25) {
  const hands=result.landmarks??[];
  if(!hands.length)return {pose:"NO HAND",poses:[] as string[],hands:0,fingers:0,rawAngle:90,steer:0};
  const readings=hands.map(hand=>readSinglePose(hand,directionalDeadzone));
  const first=readings[0];
  const pose=readings.length>1?"TWO HANDS":first.pose;
  const averageX=hands.reduce((sum,hand)=>sum+hand[0].x,0)/hands.length;
  return {pose,poses:readings.map(reading=>reading.pose),hands:hands.length,fingers:readings.reduce((sum,reading)=>sum+reading.fingers,0),rawAngle:first.rawAngle,steer:Math.max(-45,Math.min(45,(.5-averageX)*90))};
}

function controlsForPoses(poses: string[], mode: ControlMode): ControlState {
  if(mode==="air_mouse")return {...idleControls,nitro:poses.includes("PINCH")};
  const steeringPoses=poses.filter(pose=>pose==="POINT LEFT"||pose==="POINT RIGHT");
  const steering: ControlState["steering"]=steeringPoses.length===1?(steeringPoses[0]==="POINT LEFT"?"LEFT":"RIGHT"):"STRAIGHT";
  const pedal: ControlState["pedal"]=poses.includes("FIST")?"BRAKE":poses.includes("THUMB DOWN")?"REVERSE":poses.some(pose=>pose==="POINT UP"||pose==="OPEN PALM")?"GAS":"IDLE";
  return {steering,pedal,nitro:poses.includes("THUMB UP")};
}

function primaryAction(controls: ControlState): DriveAction {
  if(controls.pedal!=="IDLE")return controls.pedal;
  if(controls.nitro)return "ACTION";
  return controls.steering==="STRAIGHT"?"IDLE":controls.steering;
}

function describeControls(controls: ControlState): string {
  const labels:string[]=[];
  if(controls.pedal!=="IDLE")labels.push(controls.pedal);
  if(controls.steering!=="STRAIGHT")labels.push(controls.steering);
  if(controls.nitro)labels.push("NITRO");
  return labels.length?labels.join(" + "):"READY";
}

const formatTime=(seconds:number)=>`${String(Math.floor(seconds/60)).padStart(2,"0")}:${String(seconds%60).padStart(2,"0")}`;

export function CockpitDashboard() {
  const videoRef=useRef<HTMLVideoElement>(null), canvasRef=useRef<HTMLCanvasElement>(null), pipCanvasRef=useRef<HTMLCanvasElement>(null), pipVideoRef=useRef<HTMLVideoElement>(null), pipStreamRef=useRef<MediaStream|null>(null), streamRef=useRef<MediaStream|null>(null), trackerRef=useRef<HandLandmarker|null>(null), frameRef=useRef<number|null>(null), mountedRef=useRef(false), lastFrameRef=useRef(-1), rawAngleRef=useRef(90), lastActionRef=useRef<DriveAction>("IDLE"), audioRef=useRef<AudioContext|null>(null), simRef=useRef<HTMLDivElement>(null), calibrateTimerRef=useRef<number|null>(null), calibrationSamplesRef=useRef({active:false,sum:0,count:0}), poseCandidateRef=useRef({key:"",frames:0}), stableHandPosesRef=useRef<string[]>([]), bridgeRef=useRef({connected:false,lastAction:"IDLE" as DriveAction,lastControls:"",gameId:"circuit",lastSentAt:0,busy:false});
  const [profiles,setProfiles]=useState(defaultProfiles),[profileId,setProfileId]=useState(defaultProfiles[0].id),[cameraState,setCameraState]=useState<"idle"|"loading"|"ready"|"error">("idle"),[cameraError,setCameraError]=useState(""),[devices,setDevices]=useState<MediaDeviceInfo[]>([]),[deviceId,setDeviceId]=useState(""),[pose,setPose]=useState("NO HAND"),[handCount,setHandCount]=useState(0),[fingerCount,setFingerCount]=useState(0),[confidence,setConfidence]=useState(0),[steer,setSteer]=useState(0),[speed,setSpeed]=useState(0),[angleReadout,setAngleReadout]=useState(0),[neutral,setNeutral]=useState(90),[deadzone,setDeadzone]=useState(25),[fps,setFps]=useState(0),[latency,setLatency]=useState(0),[latencyHistory,setLatencyHistory]=useState<number[]>(Array(24).fill(0)),[controllerOn,setControllerOn]=useState(false),[bridgeConnected,setBridgeConnected]=useState(false),[action,setAction]=useState<DriveAction>("IDLE"),[counts,setCounts]=useState({LEFT:0,RIGHT:0,GAS:0,BRAKE:0,REVERSE:0,ACTION:0}),[elapsed,setElapsed]=useState(0),[audioOn,setAudioOn]=useState(false),[calibrating,setCalibrating]=useState(false),[customOpen,setCustomOpen]=useState(false),[notice,setNotice]=useState(""),[newName,setNewName]=useState(""),[newUrl,setNewUrl]=useState("");
  const profile=profiles.find(item=>item.id===profileId)??profiles[0];
  const liveRef=useRef({controllerOn,mode:profile.mode,gameId:profile.id,deadzone,neutral,audioOn});
  useEffect(()=>{liveRef.current={controllerOn,mode:profile.mode,gameId:profile.id,deadzone,neutral,audioOn};},[controllerOn,profile.mode,profile.id,deadzone,neutral,audioOn]);

  const sendDesktopControl=useCallback((next:DriveAction,enabled:boolean,force=false,gameId="circuit",controls?:ControlState)=>{
    const state=bridgeRef.current,now=performance.now();
    const nextControls=enabled?(controls??(next==="IDLE"?idleControls:{...idleControls,steering:next==="LEFT"||next==="RIGHT"?next:"STRAIGHT",pedal:next==="GAS"||next==="BRAKE"||next==="REVERSE"?next:"IDLE",nitro:next==="ACTION"})):idleControls;
    const controlsKey=JSON.stringify(nextControls);
    if(!state.connected||state.busy||(!force&&enabled&&controlsKey===state.lastControls&&gameId===state.gameId&&now-state.lastSentAt<180))return;
    state.busy=true;state.lastAction=enabled?next:"IDLE";state.lastControls=controlsKey;state.gameId=gameId;state.lastSentAt=now;
    void fetch("http://127.0.0.1:8765/control",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action:enabled?next:"IDLE",controls:nextControls,enabled,game:gameId}),cache:"no-store"})
      .then(response=>{if(!response.ok)throw new Error("The desktop bridge stopped responding.");})
      .catch(()=>{state.connected=false;setBridgeConnected(false);setControllerOn(false);setNotice("Desktop game link lost. Reopen run_web_bridge.bat and reconnect.");})
      .finally(()=>{state.busy=false;});
  },[]);

  const connectDesktopBridge=async()=>{
    try{const response=await fetch("http://127.0.0.1:8765/health",{cache:"no-store"});if(!response.ok)throw new Error();const status=await response.json();if(status.ok!==true)throw new Error();bridgeRef.current.connected=true;setBridgeConnected(true);setNotice("Desktop link ready. Launch the game, focus its play area, then start the controller.");}
    catch{bridgeRef.current.connected=false;setBridgeConnected(false);setNotice("Desktop link unavailable. Start run_web_bridge.bat and allow local network access if your browser asks.");}
  };

  const playTone=useCallback((next:DriveAction)=>{
    const ctx=audioRef.current;
    if(!liveRef.current.audioOn||!ctx||ctx.state!=="running")return;
    const oscillator=ctx.createOscillator(),gain=ctx.createGain();
    oscillator.type="sine";oscillator.frequency.value=next==="ACTION"?880:next==="BRAKE"||next==="REVERSE"?190:next==="LEFT"||next==="RIGHT"?400:560;
    gain.gain.setValueAtTime(.025,ctx.currentTime);gain.gain.exponentialRampToValueAtTime(.001,ctx.currentTime+.1);
    oscillator.connect(gain);gain.connect(ctx.destination);oscillator.start();oscillator.stop(ctx.currentTime+.1);
  },[]);

  const stopCamera=useCallback((reset=true)=>{
    sendDesktopControl("IDLE",false,true);
    if(document.pictureInPictureElement===pipVideoRef.current)void document.exitPictureInPicture().catch(()=>undefined);
    pipStreamRef.current?.getTracks().forEach(track=>track.stop());pipStreamRef.current=null;
    if(pipVideoRef.current)pipVideoRef.current.srcObject=null;
    if(frameRef.current!==null)cancelAnimationFrame(frameRef.current);frameRef.current=null;
    streamRef.current?.getTracks().forEach(track=>track.stop());streamRef.current=null;
    trackerRef.current?.close();trackerRef.current=null;
    if(videoRef.current)videoRef.current.srcObject=null;
    if(reset){setCameraState("idle");setPose("NO HAND");setHandCount(0);setFingerCount(0);setConfidence(0);setFps(0);setLatency(0);setLatencyHistory(Array(24).fill(0));setAction("IDLE");setSteer(0);lastActionRef.current="IDLE";}
  },[sendDesktopControl]);

  useEffect(()=>{mountedRef.current=true;return()=>{mountedRef.current=false;stopCamera(false);if(calibrateTimerRef.current!==null)window.clearTimeout(calibrateTimerRef.current);if(audioRef.current)void audioRef.current.close();};},[stopCamera]);

  const startCamera=useCallback(async(requestedId="")=>{
    stopCamera(false);setCameraState("loading");setCameraError("");setNotice("Requesting camera permission. The preview is processed in this browser.");
    try{
      if(!navigator.mediaDevices?.getUserMedia)throw new Error("Camera access requires HTTPS or localhost in a supported browser.");
      const stream=await navigator.mediaDevices.getUserMedia({video:requestedId?{deviceId:{exact:requestedId},width:{ideal:960},height:{ideal:540}}:{facingMode:"user",width:{ideal:960},height:{ideal:540}},audio:false});
      if(!mountedRef.current){stream.getTracks().forEach(track=>track.stop());return;}
      streamRef.current=stream;lastActionRef.current="IDLE";const video=videoRef.current;if(!video)throw new Error("Camera preview is not available.");video.srcObject=stream;await video.play();if(!mountedRef.current){stream.getTracks().forEach(track=>track.stop());return;}
      const available=await navigator.mediaDevices.enumerateDevices();if(mountedRef.current){const cameras=available.filter(item=>item.kind==="videoinput");setDevices(cameras);setDeviceId(stream.getVideoTracks()[0]?.getSettings().deviceId??cameras[0]?.deviceId??"");}
      setNotice("Loading the on-device hand tracker…");
      const vision=await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.1.0/wasm");
      const options={runningMode:"VIDEO" as const,numHands:2,minHandDetectionConfidence:.66,minHandPresenceConfidence:.62,minTrackingConfidence:.58};
      let tracker:HandLandmarker;
      try{tracker=await HandLandmarker.createFromOptions(vision,{...options,baseOptions:{modelAssetPath:"/models/hand_landmarker.task",delegate:"GPU"}});}
      catch{tracker=await HandLandmarker.createFromOptions(vision,{...options,baseOptions:{modelAssetPath:"/models/hand_landmarker.task",delegate:"CPU"}});}
      if(!mountedRef.current){tracker.close();stream.getTracks().forEach(track=>track.stop());return;}
      trackerRef.current=tracker;setCameraState("ready");setNotice("Live tracking is on. Camera frames stay in this browser.");
      let measureStart=performance.now(),frames=0,lastTelemetryAt=0;
      const draw=()=>{
        const currentVideo=videoRef.current,currentCanvas=canvasRef.current,currentTracker=trackerRef.current;
        if(currentVideo&&currentCanvas&&currentTracker&&currentVideo.readyState>=2&&currentVideo.currentTime!==lastFrameRef.current){
          lastFrameRef.current=currentVideo.currentTime;const now=performance.now(),begin=now;const result=currentTracker.detectForVideo(currentVideo,now);const inference=performance.now()-begin;const reading=readPose(result,liveRef.current.deadzone);const confidenceScores=(result.handedness??[]).map(hand=>hand[0]?.score??0);const confidenceScore=reading.hands&&confidenceScores.length?Math.round(Math.max(...confidenceScores)*100):0;rawAngleRef.current=reading.rawAngle;if(calibrationSamplesRef.current.active&&reading.hands){calibrationSamplesRef.current.sum+=reading.rawAngle;calibrationSamplesRef.current.count+=1;}
          const poseKey=reading.poses.join("|");if(!reading.hands){poseCandidateRef.current={key:"",frames:0};stableHandPosesRef.current=[];}else if(poseCandidateRef.current.key===poseKey){poseCandidateRef.current.frames+=1;if(poseCandidateRef.current.frames>=2)stableHandPosesRef.current=reading.poses;}else poseCandidateRef.current={key:poseKey,frames:1};
          const stablePoses=stableHandPosesRef.current;
          const combinedControls=controlsForPoses(stablePoses,liveRef.current.mode);
          setPose(reading.hands>1?`TWO HANDS · ${describeControls(combinedControls)}`:stablePoses[0]??"NO HAND");setHandCount(reading.hands);setFingerCount(reading.fingers);setConfidence(confidenceScore);setSteer(reading.steer);setAngleReadout(Math.round(reading.rawAngle-liveRef.current.neutral));setLatency(Math.round(inference*10)/10);if(now-lastTelemetryAt>=250){setLatencyHistory(samples=>[...samples.slice(1),inference]);lastTelemetryAt=now;}
          const next=primaryAction(combinedControls);
          sendDesktopControl(next,liveRef.current.controllerOn,false,liveRef.current.gameId,combinedControls);
          if(liveRef.current.controllerOn&&next!==lastActionRef.current){if(next!=="IDLE"){setCounts(value=>({...value,[next]:value[next]+1}));playTone(next);}lastActionRef.current=next;setAction(next);}
          const width=currentVideo.videoWidth,height=currentVideo.videoHeight;if(width&&height){if(currentCanvas.width!==width||currentCanvas.height!==height){currentCanvas.width=width;currentCanvas.height=height;}const context=currentCanvas.getContext("2d");if(context){context.clearRect(0,0,width,height);result.landmarks?.forEach(hand=>{context.lineWidth=Math.max(2,width/320);context.strokeStyle=profile.accent;context.shadowColor=profile.accent;context.shadowBlur=8;handLinks.forEach(([a,b])=>{context.beginPath();context.moveTo(hand[a].x*width,hand[a].y*height);context.lineTo(hand[b].x*width,hand[b].y*height);context.stroke();});context.shadowBlur=0;hand.forEach((point,index)=>{context.beginPath();context.fillStyle=[4,8,12,16,20].includes(index)?"#fff9dc":profile.accent;context.arc(point.x*width,point.y*height,index===0?4:3,0,Math.PI*2);context.fill();});});}
            const pipCanvas=pipCanvasRef.current,pipContext=pipCanvas?.getContext("2d");if(pipCanvas&&pipContext){if(pipCanvas.width!==width||pipCanvas.height!==height){pipCanvas.width=width;pipCanvas.height=height;}pipContext.save();pipContext.setTransform(-1,0,0,1,width,0);pipContext.drawImage(currentVideo,0,0,width,height);result.landmarks?.forEach(hand=>{pipContext.lineWidth=Math.max(2,width/320);pipContext.strokeStyle=profile.accent;pipContext.shadowColor=profile.accent;pipContext.shadowBlur=8;handLinks.forEach(([a,b])=>{pipContext.beginPath();pipContext.moveTo(hand[a].x*width,hand[a].y*height);pipContext.lineTo(hand[b].x*width,hand[b].y*height);pipContext.stroke();});pipContext.shadowBlur=0;hand.forEach((point,index)=>{pipContext.beginPath();pipContext.fillStyle=[4,8,12,16,20].includes(index)?"#fff9dc":profile.accent;pipContext.arc(point.x*width,point.y*height,index===0?4:3,0,Math.PI*2);pipContext.fill();});});pipContext.restore();}}
          frames++;if(now-measureStart>=1000){setFps(Math.round(frames*1000/(now-measureStart)));frames=0;measureStart=now;}
        }
        frameRef.current=requestAnimationFrame(draw);
      };
      frameRef.current=requestAnimationFrame(draw);
    }catch(error){stopCamera(false);if(mountedRef.current){setCameraState("error");setCameraError(error instanceof Error?error.message:"Could not start the camera.");setNotice("Camera is off. Use the offline track with keyboard controls.");}}
  },[playTone,profile.accent,sendDesktopControl,stopCamera]);

  useEffect(()=>{if(controllerOn){const timer=window.setInterval(()=>{setElapsed(value=>value+1);setSpeed(value=>action==="GAS"?Math.min(240,value+14):action==="ACTION"?Math.min(240,value+28):action==="BRAKE"||action==="REVERSE"?Math.max(0,value-22):Math.max(0,value-3));},1000);return()=>window.clearInterval(timer);}},[controllerOn,action]);
  useEffect(()=>{if(!controllerOn)sendDesktopControl("IDLE",false,true);},[controllerOn,sendDesktopControl]);
  useEffect(()=>{const onKey=(event:globalThis.KeyboardEvent)=>{if(event.code==="Space"&&!(event.target instanceof HTMLInputElement)&&!(event.target instanceof HTMLSelectElement)&&!(event.target instanceof HTMLTextAreaElement)){event.preventDefault();setControllerOn(value=>!value);}};window.addEventListener("keydown",onKey);return()=>window.removeEventListener("keydown",onKey);},[]);

  const setDrive=(next:DriveAction)=>{setAction(next);if(next==="LEFT")setSteer(-28);else if(next==="RIGHT")setSteer(28);else if(next==="IDLE")setSteer(0);if(next!=="IDLE"&&next!==lastActionRef.current){setCounts(value=>({...value,[next]:value[next]+1}));playTone(next);}lastActionRef.current=next;};
  const onTrackKey=(event:KeyboardEvent<HTMLDivElement>)=>{const key=event.key.toLowerCase(),map:Record<string,DriveAction>={arrowleft:"LEFT",a:"LEFT",arrowright:"RIGHT",d:"RIGHT",arrowup:"GAS",w:"GAS",arrowdown:"REVERSE",s:"REVERSE"};if(map[key]){event.preventDefault();if(controllerOn)setDrive(map[key]);}};
  const calibrate=()=>{if(!handCount){setNotice("Show a hand to the camera before calibration.");return;}calibrationSamplesRef.current={active:true,sum:0,count:0};setCalibrating(true);setNotice("Hold your hand comfortably still for 3 seconds to set the angle reference.");if(calibrateTimerRef.current!==null)window.clearTimeout(calibrateTimerRef.current);calibrateTimerRef.current=window.setTimeout(()=>{const sample=calibrationSamplesRef.current;sample.active=false;if(sample.count){const calibrated=sample.sum/sample.count;setNeutral(calibrated);setAngleReadout(0);setNotice("Angle reference calibrated. Point gestures still control the game.");}else setNotice("Calibration missed the hand. Try again with your hand in frame.");setCalibrating(false);},3000);};
  const toggleAudio=async()=>{try{if(!audioRef.current)audioRef.current=new AudioContext();if(audioRef.current.state==="suspended")await audioRef.current.resume();setAudioOn(value=>!value);}catch{setNotice("Audio is unavailable in this browser.");}};
  const togglePip=async()=>{try{const video=pipVideoRef.current as (HTMLVideoElement&{requestPictureInPicture?:()=>Promise<PictureInPictureWindow>})|null,canvas=pipCanvasRef.current;if(!video||!canvas||!video.requestPictureInPicture||!canvas.captureStream)throw new Error("Annotated picture-in-picture is not supported in this browser.");if(document.pictureInPictureElement===video){await document.exitPictureInPicture();return;}if(!pipStreamRef.current){pipStreamRef.current=canvas.captureStream(24);video.srcObject=pipStreamRef.current;}if(video.paused)await video.play();await video.requestPictureInPicture();}catch(error){setNotice(error instanceof Error?error.message:"Could not open the annotated camera preview.");}};
  const focusTrack=()=>{simRef.current?.scrollIntoView({behavior:"smooth",block:"center"});simRef.current?.focus({preventScroll:true});setNotice("Offline track focused. Use arrow keys or WASD while controller is running.");};
  const addProfile=(event:FormEvent<HTMLFormElement>)=>{event.preventDefault();try{const parsed=new URL(newUrl);if(parsed.protocol!=="https:")throw new Error();const added:Profile={id:`custom-${Date.now()}`,name:newName.trim(),genre:"CUSTOM PROFILE",icon:"🎮",url:parsed.href,mode:"racing",accent:"#b49aff",controls:[["Index point up","Accelerate / forward","↑ / W"],["Thumb up","Nitro","SPACE"],["Thumb down","Reverse","↓ / S"],["Closed fist","Brake / stop","↓ / S"],["Index point left","Turn left","← / A"],["Index point right","Turn right","→ / D"]]};if(!added.name)throw new Error();setProfiles(list=>[...list,added]);setProfileId(added.id);setCustomOpen(false);setNewName("");setNewUrl("");setNotice(`${added.name} profile added for this session.`);}catch{setNotice("Enter a profile name and a valid HTTPS game URL.");}};
  const launch=()=>{if(!profile.url){setNotice("This profile has no game link yet.");return;}if(bridgeConnected&&cameraState==="ready"){setControllerOn(true);setNotice("Game input is armed. Keep the cockpit visible beside the game and click the game area to focus it.");}else setNotice("For hand controls, enable the camera and connect the desktop game link before playing.");window.open(profile.url,"_blank","noopener,noreferrer");};
  const resetSession=()=>{setCounts({LEFT:0,RIGHT:0,GAS:0,BRAKE:0,REVERSE:0,ACTION:0});setElapsed(0);setSpeed(0);setAction("IDLE");setSteer(0);lastActionRef.current="IDLE";};

  return <main className="cockpit-page" style={{"--cockpit-accent":profile.accent} as CSSProperties}>
    <header className="cockpit-nav"><Link className="brand" href="/" aria-label="Gesture Racing home"><span className="brand__mark"><i/><i/><i/><i/></span><span>GESTURE<span className="brand__light"> / RACING</span></span></Link><nav aria-label="Main navigation"><Link href="/#system">The system</Link><Link href="/#games">Games</Link><Link href="/#playground">Try it</Link><Link className="cockpit-nav__current" href="/dashboard">Cockpit</Link></nav><Link className="cockpit-nav__return" href="/"><ArrowUpRight size={14}/> BACK TO THE PROJECT</Link></header>
    <section className="cockpit-intro"><div className="cockpit-intro__copy"><div className="eyebrow"><span className="eyebrow__dot"/> LIVE INPUT / LOCAL CAMERA</div><h1>Your hands,<br/><em>in control.</em></h1><p>Bring your hands into frame. Watch each movement become a command, then try the track below.</p></div><div className="cockpit-intro__aside"><div className="cockpit-intro__state"><span className={cameraState==="ready"?"cockpit-pulse cockpit-pulse--live":"cockpit-pulse"}/><span>{cameraState==="ready"?"CAMERA LINKED":cameraState==="loading"?"CONNECTING":"READY WHEN YOU ARE"}</span></div><div className="cockpit-intro__numbers"><div><strong>01</strong><small>CAMERA</small></div><i/><div><strong>21</strong><small>HAND POINTS</small></div><i/><div><strong>0</strong><small>UPLOADS</small></div></div><span className="cockpit-intro__note">YOUR CAMERA FEED STAYS ON THIS DEVICE</span></div></section>
    <div className="cockpit-toolbar"><label className="cockpit-camera-select"><span>CAMERA</span><select aria-label="Select camera" value={deviceId} onChange={event=>{setDeviceId(event.target.value);if(cameraState==="ready")void startCamera(event.target.value);}} disabled={!devices.length}><option value="">{devices.length?"Choose camera":"No camera selected"}</option>{devices.map((device,index)=><option key={device.deviceId} value={device.deviceId}>{device.label||`Camera ${index+1}`}</option>)}</select></label><button className={`cockpit-toolbar__chip ${bridgeConnected?"is-on":""}`} type="button" onClick={()=>void connectDesktopBridge()}><Cable size={13}/> {bridgeConnected?"GAME LINK READY":"CONNECT GAME"}</button><button className={`cockpit-toolbar__chip ${audioOn?"is-on":""}`} type="button" onClick={()=>void toggleAudio()}><AudioLines size={13}/> SOUND {audioOn?"ON":"OFF"}</button><button className="cockpit-toolbar__chip" type="button" onClick={()=>void togglePip()} disabled={cameraState!=="ready"}><Maximize2 size={12}/> FLOAT CAMERA</button><span className="cockpit-chip cockpit-chip--green"><Activity size={13}/> {cameraState==="ready"?`${fps||0} FPS`:"FPS —"}</span><span className="cockpit-chip cockpit-chip--pink">{cameraState==="ready"?`${latency.toFixed(1)} ms INFERENCE`:"LATENCY —"}</span></div>
    <div className="cockpit-content">
      <section className="cockpit-left">
        <div className={`cockpit-camera ${cameraState==="ready"?"cockpit-camera--live":""}`}><video ref={videoRef} muted playsInline aria-label="Live camera preview"/><canvas ref={canvasRef} aria-hidden="true"/><canvas ref={pipCanvasRef} className="cockpit-pip-canvas" aria-hidden="true"/><video ref={pipVideoRef} className="cockpit-pip-source" muted playsInline aria-label="Annotated floating camera preview"/>{cameraState!=="ready"&&<div className="cockpit-camera__placeholder"><span className="cockpit-camera__icon">{cameraState==="loading"?<LoaderCircle className="cockpit-spin" size={25}/>:cameraState==="error"?<X size={24}/>:<Camera size={25}/>}</span><strong>{cameraState==="loading"?"STARTING CAMERA":cameraState==="error"?"CAMERA OFFLINE":"VISION FEED / STANDBY"}</strong><small>{cameraState==="error"?cameraError:"Enable the camera to preview your hands and live gesture tracking."}</small>{cameraState!=="loading"&&<button type="button" onClick={()=>void startCamera(deviceId)}><Camera size={14}/> {cameraState==="error"?"RETRY CAMERA":"ENABLE CAMERA"}</button>}</div>}<div className="cockpit-camera__overlay"><span><i/> {cameraState==="ready"?"CAMERA LIVE":"VISION PIPELINE"}</span><span>{cameraState==="ready"?"LOCAL PROCESSING":"21 LANDMARKS / HAND"}</span></div></div>
        <div className="cockpit-games"><div className="cockpit-panel__title"><Gamepad2 size={13}/> NEURAL GAME LAUNCHER & PROFILES <button className="cockpit-icon-button" type="button" aria-label="Add game profile" onClick={()=>setCustomOpen(true)}><Plus size={15}/></button></div><div className="cockpit-game-row"><select aria-label="Game profile" value={profileId} onChange={event=>setProfileId(event.target.value)}>{profiles.map(item=><option key={item.id} value={item.id}>{item.icon} {item.name}</option>)}</select><span className="cockpit-game-tag">{profile.genre}</span></div><div className="cockpit-game-actions"><button type="button" className="cockpit-button cockpit-button--purple" onClick={launch}><ArrowUpRight size={13}/> LAUNCH GAME</button><button type="button" className="cockpit-button" onClick={focusTrack}><Focus size={13}/> FOCUS TRACK</button><button type="button" className="cockpit-button cockpit-button--plus" onClick={()=>setCustomOpen(true)}><Plus size={14}/> ADD GAME</button></div>
          <div className="cockpit-control-profile"><div className="cockpit-panel__title">CONTROL PROFILE <span>▣ {profile.name}</span></div><div className="cockpit-control-grid">{[...profile.controls,["Open palm","Accelerate / forward","↑ / W"] as [string,string,string]].map(([gesture,action,key])=><div className="cockpit-control-tile" key={`${gesture}-${action}`}><strong><Hand size={12}/> {gesture}</strong><span>➜ {action}</span><small>{key}</small></div>)}</div></div>
        </div>
      </section>
      <section className="cockpit-right">
        <div className="cockpit-panel cockpit-neural"><div className="cockpit-panel__title"><Zap size={12}/> WHAT THE CAMERA SEES <span>LOCAL, LIVE ANALYSIS</span></div><motion.div key={pose} className={`cockpit-neural__pose ${handCount?"cockpit-neural__pose--found":""}`} initial={{opacity:.4,y:5}} animate={{opacity:1,y:0}} transition={{duration:.2}}><Hand size={24}/><strong>{handCount?pose:"NO HAND IN FRAME"}</strong></motion.div><div className="cockpit-neural__foot"><div><span className={controllerOn?"cockpit-status cockpit-status--active":"cockpit-status"}>{controllerOn?"CONTROLLER ON":"CONTROLLER OFF"}</span><span className="cockpit-status">{handCount} HAND{handCount===1?"":"S"}</span><span className="cockpit-status">{fingerCount}/4 FINGERS</span></div><span>ANGLE: {handCount?`${angleReadout>=0?"+":""}${angleReadout}°`:"--°"} (NEUTRAL {Math.round(neutral)}°)</span></div><div className="cockpit-metric-strip"><div className="cockpit-live-metric"><span>TRACKER CONFIDENCE</span><div className="cockpit-confidence"><motion.i animate={{width:`${confidence}%`}} transition={{type:"spring",stiffness:150,damping:22}}/><b>{cameraState==="ready"&&handCount?`${confidence}%`:"—"}</b></div></div><div className="cockpit-live-metric cockpit-live-metric--latency"><span>INFERENCE / FRAME</span><div><strong>{cameraState==="ready"?latency.toFixed(1):"—"}<small>{cameraState==="ready"?"ms":"ms"}</small></strong><svg viewBox="0 0 120 30" role="img" aria-label="Recent measured hand tracking inference time"><polyline points={latencyHistory.map((value,index)=>`${index*120/(latencyHistory.length-1)},${28-Math.min(24,value/2)}`).join(" ")}/></svg></div></div><div className="cockpit-live-metric"><span>CAMERA RATE</span><div><strong>{cameraState==="ready"?fps||"…":"—"}<small>fps</small></strong><span className="cockpit-metric-caption">{cameraState==="ready"?"measured":"awaiting camera"}</span></div></div></div></div>
        <div className="cockpit-panel cockpit-orientation"><div className="cockpit-panel__title"><Crosshair size={12}/> ORIENTATION RADAR & STEERING TELEMETRY</div><div className="cockpit-orientation__body"><div className="cockpit-radar"><i className="cockpit-radar__cross cockpit-radar__cross--h"/><i className="cockpit-radar__cross cockpit-radar__cross--v"/><i className="cockpit-radar__sweep" style={{transform:`rotate(${steer*2}deg)`}}/><span/><b/></div><div className="cockpit-orientation__data"><small>CYBER STEERING ANGLE</small><strong>{handCount?`${steer>=0?"+":""}${Math.round(steer)}°`:"--.-°"}</strong><div className="cockpit-orientation__actions"><button type="button" onClick={calibrate} disabled={!handCount}>{calibrating?<><LoaderCircle size={12} className="cockpit-spin"/> CALIBRATING</>:<><Zap size={12}/> 1-CLICK CALIBRATE (3s)</>}</button><button type="button" onClick={focusTrack}><ArrowLeft size={12}/> OFFLINE TRACK</button></div><small className="cockpit-neutral">{handCount?`Neutral calibrated: ${Math.round(neutral)}°`:"Show your hand to calibrate neutral."}</small></div></div></div>
        <div className="cockpit-panel cockpit-master"><div className="cockpit-panel__title"><Gamepad2 size={12}/> MASTER CONTROLLER <span>[SPACEBAR = START / STOP]</span></div><div className="cockpit-master__actions">{!bridgeConnected&&<button type="button" className="cockpit-button cockpit-bridge-connect" onClick={()=>void connectDesktopBridge()}><Cable size={13}/> CONNECT GAME LINK</button>}<button type="button" className={`cockpit-start ${controllerOn?"cockpit-start--active":""}`} onClick={()=>{setControllerOn(true);setNotice(bridgeConnected?"Gesture input is live. Keep the game focused and your hand in frame.":"Practice track started. Connect the desktop game link to control an external game.");}} disabled={controllerOn}><span>▶</span> {controllerOn?"CONTROLLER RUNNING":bridgeConnected?"START GAME INPUT":"START PRACTICE"}</button><button type="button" className="cockpit-stop" onClick={()=>setControllerOn(false)} disabled={!controllerOn}><Square size={12} fill="currentColor"/> STOP</button><span className={`cockpit-master__state ${controllerOn?"is-running":""}`}><i/> {controllerOn?bridgeConnected?"GAME INPUT LIVE":"PRACTICE ONLY":"STANDBY"}</span></div>{bridgeConnected&&<p className="cockpit-bridge-hint">Desktop link ready · one hand can hold throttle while the other steers or activates nitro. Click the game to focus it.</p>}<label className="cockpit-deadzone"><span>Steering Deadzone (± deg): <b>{deadzone}°</b></span><input type="range" min="5" max="40" step="1" value={deadzone} onChange={event=>setDeadzone(Number(event.target.value))}/></label></div>
        <div className="cockpit-panel cockpit-session"><div className="cockpit-panel__title"><Gauge size={12}/> SESSION ACTIVITY <button className="cockpit-icon-button" type="button" aria-label="Reset telemetry" onClick={resetSession}><RotateCcw size={12}/></button></div><div className="cockpit-counts">{(["LEFT","RIGHT","GAS","ACTION","REVERSE","BRAKE"] as const).map((key,index)=><div key={key} style={{"--count-color":["var(--cyan)","var(--pink)","var(--lime)","var(--violet)","var(--orange)","var(--pink)"][index]} as CSSProperties}><small>{key}</small><motion.strong key={counts[key]} initial={{y:5,opacity:.35}} animate={{y:0,opacity:1}} transition={{duration:.18}}>{counts[key]}</motion.strong></div>)}</div><div className="cockpit-session__foot"><span>SESSION TIME <b>{formatTime(elapsed)}</b></span><span>{cameraState==="ready"?"CAMERA TRACKING":"KEYBOARD SIMULATION"}</span></div></div>
        <div className="cockpit-panel cockpit-simulator"><div className="cockpit-panel__title"><Gauge size={12}/> PRACTICE TRACK <span>IN-PAGE SIMULATION · NOT A GAME FEED</span></div><div className="cockpit-track" ref={simRef} tabIndex={0} role="application" aria-label="Offline racing track. Start the controller, then use arrow keys or WASD to drive." onKeyDown={onTrackKey} onBlur={()=>setDrive("IDLE")}><div className="cockpit-track__stars"/><div className="cockpit-track__road"><div className="cockpit-track__lane"/><motion.div className="cockpit-track__car" animate={{x:steer*2.2,rotate:steer*.35}} transition={{type:"spring",stiffness:180,damping:20}}><span/>{action==="ACTION"&&<i/>}</motion.div></div><div className="cockpit-track__readout"><span>SIM SPEED <b>{String(Math.round(speed)).padStart(3,"0")} km/h</b></span><span>LAST INPUT <b>{action}</b></span></div></div><div className="cockpit-track-controls"><button aria-label="Steer left" type="button" onClick={()=>controllerOn&&setDrive("LEFT")}><ArrowDownRight size={15}/></button><button aria-label="Steer right" type="button" onClick={()=>controllerOn&&setDrive("RIGHT")}><ArrowUpRight size={15}/></button><button type="button" onClick={()=>controllerOn&&setDrive("GAS")}>↑ GAS</button><button type="button" onClick={()=>controllerOn&&setDrive("BRAKE")}>↓ BRAKE</button><button type="button" onClick={()=>controllerOn&&setDrive("ACTION")}>✳ ACTION</button><span>{controllerOn?"CONTROLS LIVE":"START CONTROLLER TO DRIVE"}</span></div></div>
      </section>
    </div>
    <footer className="cockpit-footer"><LinkHome/> <span><ShieldCheck size={12}/> CAMERA PROCESSING STAYS IN THIS BROWSER · NO VIDEO UPLOAD</span><span>GESTURE / RACING · LIVE COCKPIT</span></footer>
    {notice&&<div className="cockpit-toast" role="status"><span>{notice}</span><button type="button" aria-label="Dismiss message" onClick={()=>setNotice("")}><X size={13}/></button></div>}
    {customOpen&&<div className="cockpit-modal-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)setCustomOpen(false);}}><section className="cockpit-modal" role="dialog" aria-modal="true" aria-labelledby="add-profile-title"><button className="cockpit-modal__close" type="button" onClick={()=>setCustomOpen(false)} aria-label="Close add profile"><X size={16}/></button><span className="cockpit-panel__title"><Plus size={13}/> CUSTOM PROFILE</span><h2 id="add-profile-title">Add a game.</h2><p>Save a game link and use the standard racing gesture map for this session.</p><form onSubmit={addProfile}><label>PROFILE NAME<input required value={newName} onChange={event=>setNewName(event.target.value)} placeholder="My favorite racer"/></label><label>HTTPS GAME URL<input required type="url" value={newUrl} onChange={event=>setNewUrl(event.target.value)} placeholder="https://example.com/game"/></label><div><button className="cockpit-button" type="button" onClick={()=>setCustomOpen(false)}>CANCEL</button><button className="cockpit-button cockpit-button--purple" type="submit"><Check size={13}/> SAVE PROFILE</button></div></form></section></div>}
  </main>;
}

function LinkHome(){return <Link href="/" className="cockpit-back"><ArrowLeft size={13}/> BACK TO GESTURE RACING</Link>;}
