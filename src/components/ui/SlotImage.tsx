"use client";

import { useEffect, useId, useRef, useState } from "react";

export type ArtTone = "forest" | "dawn" | "fog";

const tones: Record<ArtTone, { sky: [string, string]; far: string; mid: string; near: string; sun: string }> = {
  dawn: { sky: ["#fff6ea", "#f4d6b2"], far: "#e2c3a3", mid: "#b2ae8c", near: "#506b4e", sun: "#fff3d6" },
  forest: { sky: ["#eaf2ec", "#b9d3c1"], far: "#a6c1ae", mid: "#5f8a73", near: "#1c4a3d", sun: "#f4fbe0" },
  fog: { sky: ["#f0f3f0", "#cdd6d0"], far: "#b3bfb8", mid: "#7f918a", near: "#2f433d", sun: "#ffffff" },
};

/** Layered-mountain illustration shown while a photo is missing. */
export function MistArt({ tone = "forest", className = "" }: { tone?: ArtTone; className?: string }) {
  const uid = useId().replace(/:/g, "");
  const c = tones[tone];
  return (
    <svg viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" className={className} aria-hidden>
      <defs>
        <linearGradient id={`sky${uid}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={c.sky[0]} />
          <stop offset="1" stopColor={c.sky[1]} />
        </linearGradient>
        <radialGradient id={`sun${uid}`} cx="0.7" cy="0.32" r="0.45">
          <stop offset="0" stopColor={c.sun} stopOpacity="0.95" />
          <stop offset="1" stopColor={c.sun} stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="400" height="300" fill={`url(#sky${uid})`} />
      <rect width="400" height="300" fill={`url(#sun${uid})`} />
      <path d="M0 190 90 120l60 50 70-85 80 90 60-45 40 30v40H0Z" fill={c.far} opacity=".75" />
      <path d="M0 230 70 165l55 40 80-62 70 70 55-40 70 45v32H0Z" fill={c.mid} opacity=".9" />
      <path d="M0 270c60-34 120-40 190-20s140 18 210-8v58H0Z" fill={c.near} />
    </svg>
  );
}

type Props = {
  /** Path of the photo (see lib/images.ts). A missing file is fine. */
  src?: string;
  alt: string;
  /** Mood of the placeholder illustration */
  tone?: ArtTone;
  /** true → nothing is rendered if the photo is missing (optional gallery photos) */
  optional?: boolean;
  priority?: boolean;
  className?: string;
  /** CSS object-position, e.g. "50% 30%" to choose the focal point */
  position?: string;
};

// The caller sets the positioning in className: "relative ..." or "absolute inset-0 ...".
export function SlotImage({ src, alt, tone = "forest", optional = false, priority = false, className = "", position }: Props) {
  const [failed, setFailed] = useState(false);
  const ref = useRef<HTMLImageElement>(null);

  // The image may fail before React hydrates; catch that case too.
  useEffect(() => {
    const el = ref.current;
    if (el && el.complete && el.naturalWidth === 0) setFailed(true);
  }, [src]);

  if (optional && (failed || !src)) return null;

  return (
    <div className={`overflow-hidden ${className}`}>
      {!optional && <MistArt tone={tone} className="absolute inset-0 size-full" />}
      {src && !failed && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          ref={ref}
          src={src}
          alt={alt}
          loading={priority ? "eager" : "lazy"}
          decoding="async"
          onError={() => setFailed(true)}
          style={position ? { objectPosition: position } : undefined}
          className="absolute inset-0 size-full object-cover"
        />
      )}
    </div>
  );
}
