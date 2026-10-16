"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, Eye, EyeOff, Gamepad2, LockKeyhole, Mail } from "lucide-react";

export function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);
  const [notice, setNotice] = useState(false);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setNotice(true);
  };

  return <main className="login-page">
    <div className="login-grain" aria-hidden="true"/>
    <header className="login-header">
      <Link className="brand" href="/" aria-label="Gesture Racing home"><span className="brand__mark"><i/><i/><i/><i/></span><span>GESTURE<span className="brand__light"> / RACING</span></span></Link>
      <Link className="login-back" href="/"><ArrowLeft size={14}/> BACK TO THE TRACK</Link>
    </header>
    <section className="login-layout">
      <div className="login-story">
        <span className="login-eyebrow"><i/> PLAYER ACCESS / 01</span>
        <h1>Your next<br/>lap starts <em>here.</em></h1>
        <p>One small move can change the whole race. Get back to your gesture-powered world.</p>
        <div className="login-stats" aria-label="Project highlights"><span><strong>21</strong><small>HAND LANDMARKS</small></span><i/><span><strong>0</strong><small>EXTRA CONTROLLERS</small></span></div>
        <div className="login-orbit" aria-hidden="true"><span className="login-orbit__ring login-orbit__ring--outer"/><span className="login-orbit__ring login-orbit__ring--inner"/><span className="login-orbit__core"><Gamepad2 size={35}/></span><i className="login-orbit__spark login-orbit__spark--one"/><i className="login-orbit__spark login-orbit__spark--two"/></div>
        <span className="login-story__foot">YOUR HANDS ARE THE WHEEL <b>✳</b> PLAY BY INSTINCT</span>
      </div>
      <div className="login-card-wrap">
        <div className="login-card__top"><span>PLAYER PORTAL</span><span>01 / SIGN IN</span></div>
        <div className="login-card">
          <div className="login-card__icon"><LockKeyhole size={20}/></div>
          <span className="login-card__eyebrow">WELCOME BACK, PLAYER</span>
          <h2>Pick up where<br/>you <em>left off.</em></h2>
          <p className="login-card__intro">Sign in to your player account.</p>
          <form onSubmit={handleSubmit}>
            <label htmlFor="login-email">EMAIL ADDRESS</label>
            <div className="login-input"><Mail size={16}/><input id="login-email" name="email" type="email" autoComplete="email" placeholder="you@example.com" required onChange={()=>setNotice(false)}/></div>
            <div className="login-password-label"><label htmlFor="login-password">PASSWORD</label><span>8+ CHARACTERS</span></div>
            <div className="login-input"><LockKeyhole size={16}/><input id="login-password" name="password" type={showPassword?"text":"password"} autoComplete="current-password" placeholder="Enter your password" minLength={8} required onChange={()=>setNotice(false)}/><button className="login-password-toggle" type="button" aria-label={showPassword?"Hide password":"Show password"} onClick={()=>setShowPassword((show)=>!show)}>{showPassword?<EyeOff size={16}/>:<Eye size={16}/>}</button></div>
            <button className="login-submit" type="submit">SIGN IN <ArrowRight size={16}/></button>
          </form>
          {notice&&<p className="login-notice" role="status">Sign-in is not connected yet. Your details were not sent or saved.</p>}
          <p className="login-privacy">Account access is not set up on this site yet. This form stays on this device.</p>
          <div className="login-divider"><span/><b>PLAYER NOTE</b><span/></div>
          <Link className="login-home-link" href="/#games">Explore games without an account <ArrowRight size={14}/></Link>
        </div>
        <div className="login-card__bottom"><span>CAMERA PERMISSIONS STAY YOUR CHOICE</span><span>GR / 2026</span></div>
      </div>
    </section>
    <footer className="login-footer"><span>GESTURE / RACING</span><span>BUILT FOR THE WAY YOU MOVE</span><Link href="/">BACK TO HOME ↑</Link></footer>
  </main>;
}
