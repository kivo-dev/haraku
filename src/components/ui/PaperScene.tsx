/**
 * Paper-cut landscape used as the background of the app pages.
 * Layers from back to front: sky + sun, drifting clouds, cream/brown mountains,
 * blue sea with moving waves and a little boat, green pastures with forest,
 * and the cream paper sheet that the page content sits on (same colour as mist-200).
 * Pure SVG + CSS animation (see globals.css); respects "reduce motion".
 */
const W = 1440;
const H = 640;

const SKY = ["#fdf4e3", "#f8e2c0"];
const CREAM = "#fbf1dc";
const MOUNTAIN_FAR = "#ecd7b3";
const MOUNTAIN_MID = "#c9a073";
const MOUNTAIN_NEAR = "#a67549";
const SEA = ["#7bbad3", "#5aa3c4", "#3f86aa"];
const GRASS = ["#9bb86d", "#6f9c5b"];
const TREE = ["#3f7d4c", "#2f6a40"];
const PAPER = ["#f7edd9", "#f1e4cb"];

type Pt = [number, number];

const ridge = (pts: Pt[], bottom = H + 20) =>
  `M${pts[0][0]} ${bottom}${pts.map(([x, y]) => ` L${x} ${y}`).join("")} L${pts[pts.length - 1][0]} ${bottom}Z`;

/** A strip of waves wide enough to slide by one wavelength without showing a gap. */
function wave(y: number, amp: number, wl = 240) {
  let d = `M-${wl} ${y} Q${-wl + wl / 4} ${y - amp} ${-wl + wl / 2} ${y}`;
  for (let x = -wl + wl / 2 + wl / 2; x <= W + wl * 2; x += wl / 2) d += ` T${x} ${y}`;
  return `${d} V${H + 20} H-${wl}Z`;
}

/** Paper pine tree: three stacked triangles. */
function Tree({ x, y, s = 1, fill }: { x: number; y: number; s?: number; fill: string }) {
  const w = 22 * s;
  const h = 26 * s;
  return (
    <g fill={fill}>
      <polygon points={`${x},${y - h * 2.1} ${x - w * 0.55},${y - h * 1.25} ${x + w * 0.55},${y - h * 1.25}`} />
      <polygon points={`${x},${y - h * 1.6} ${x - w * 0.8},${y - h * 0.65} ${x + w * 0.8},${y - h * 0.65}`} />
      <polygon points={`${x},${y - h * 1.05} ${x - w},${y} ${x + w},${y}`} />
    </g>
  );
}

function Cloud({ y, scale, duration, delay }: { y: number; scale: number; duration: number; delay: number }) {
  const shape = "M0 46a22 22 0 0 1 22-22 30 30 0 0 1 58-6 24 24 0 0 1 40 14 18 18 0 0 1 2 36H18A18 18 0 0 1 0 46Z";
  return (
    <g transform={`translate(0 ${y}) scale(${scale})`}>
      <g className="drift" style={{ animationDuration: `${duration}s`, animationDelay: `-${delay}s` }}>
        <path d={shape} fill="#ecd7b3" transform="translate(0 6)" />
        <path d={shape} fill="#fffaf0" />
      </g>
    </g>
  );
}

const farPeaks: Pt[] = [
  [-20, 410], [110, 330], [200, 372], [330, 280], [450, 380], [560, 335], [690, 430],
  [820, 340], [950, 250], [1070, 372], [1190, 318], [1310, 388], [1460, 300],
];
const midPeaks: Pt[] = [
  [-20, 480], [90, 405], [190, 450], [310, 372], [430, 458], [560, 425], [640, 490],
  [800, 486], [900, 430], [1010, 392], [1130, 452], [1250, 385], [1360, 450], [1460, 410],
];
const nearPeaks: Pt[] = [
  [-20, 520], [60, 450], [140, 500], [250, 430], [360, 520], [440, 540],
  [1000, 540], [1100, 470], [1210, 520], [1320, 440], [1460, 500],
];

const hillLeft: Pt[] = [[-20, 660], [-20, 520], [90, 488], [210, 536], [340, 506], [470, 566], [620, 660]];
const hillLeftFront: Pt[] = [[-20, 660], [-20, 566], [130, 544], [270, 590], [420, 612], [520, 660]];
const hillRight: Pt[] = [[1460, 660], [1460, 505], [1340, 470], [1220, 522], [1100, 494], [960, 566], [820, 660]];
const hillRightFront: Pt[] = [[1460, 660], [1460, 560], [1320, 540], [1180, 590], [1030, 612], [930, 660]];

export function PaperScene() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[30rem] overflow-hidden md:h-[40rem]"
    >
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMax slice" className="size-full">
        <defs>
          <linearGradient id="paper-sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={SKY[0]} />
            <stop offset="1" stopColor={SKY[1]} />
          </linearGradient>
        </defs>

        <rect width={W} height={H} fill="url(#paper-sky)" />

        {/* Sun: three paper discs */}
        <circle cx="1000" cy="215" r="120" fill="#fbe6c2" opacity="0.7" />
        <circle cx="1000" cy="215" r="84" fill="#f9d9a0" />
        <circle cx="1000" cy="215" r="58" fill="#f6c677" />

        <Cloud y={110} scale={1} duration={150} delay={20} />
        <Cloud y={190} scale={0.7} duration={190} delay={110} />
        <Cloud y={60} scale={0.8} duration={170} delay={70} />

        {/* Mountains: cream far, brown mid */}
        <g className="paper-layer">
          <path d={ridge(farPeaks)} fill={MOUNTAIN_FAR} />
          {/* snow caps on the highest peaks */}
          <polygon points="950,250 918,292 940,286 954,304 972,286 986,294" fill={CREAM} />
          <polygon points="330,280 300,318 320,312 334,330 352,312 366,320" fill={CREAM} />
          <polygon points="1190,318 1166,348 1182,344 1194,356 1208,344 1220,350" fill={CREAM} />
        </g>
        <g className="paper-layer">
          <path d={ridge(midPeaks)} fill={MOUNTAIN_MID} />
        </g>
        <g className="paper-layer">
          <path d={ridge(nearPeaks)} fill={MOUNTAIN_NEAR} />
        </g>

        {/* Sea */}
        <rect x="0" y="486" width={W} height={H} fill={SEA[0]} />
        <g className="wave" style={{ animationDuration: "26s" }}>
          <path d={wave(508, 9)} fill={SEA[0]} />
        </g>
        <g className="wave" style={{ animationDuration: "19s", animationDirection: "reverse" }}>
          <path d={wave(538, 11)} fill={SEA[1]} />
        </g>
        <g className="wave" style={{ animationDuration: "14s" }}>
          <path d={wave(572, 12)} fill={SEA[2]} />
        </g>

        {/* Paper boat */}
        <g transform="translate(704 528)">
          <g className="bob">
            <path d="M-30 0H30L20 13H-20Z" fill="#b8683f" />
            <path d="M-2 -38V-3L-26 -3Z" fill="#e9b872" />
            <path d="M3 -42V-3L26 -3Z" fill="#fffaf0" />
          </g>
        </g>

        {/* Green pastures and forest */}
        <g className="paper-layer">
          <path d={ridge(hillLeft)} fill={GRASS[0]} />
          <path d={ridge(hillRight)} fill={GRASS[0]} />
          {[[70, 505, 1], [150, 520, 0.8], [235, 538, 1.1], [330, 530, 0.9], [405, 556, 0.8]].map(([x, y, s]) => (
            <Tree key={`l${x}`} x={x} y={y} s={s} fill={TREE[0]} />
          ))}
          {[[1380, 490, 1], [1300, 506, 0.9], [1215, 528, 1.1], [1120, 516, 0.8], [1040, 540, 0.9]].map(([x, y, s]) => (
            <Tree key={`r${x}`} x={x} y={y} s={s} fill={TREE[0]} />
          ))}
        </g>
        <g className="paper-layer">
          <path d={ridge(hillLeftFront)} fill={GRASS[1]} />
          <path d={ridge(hillRightFront)} fill={GRASS[1]} />
          {[[40, 568, 1.2], [140, 566, 1], [250, 590, 1.3], [350, 604, 1]].map(([x, y, s]) => (
            <Tree key={`lf${x}`} x={x} y={y} s={s} fill={TREE[1]} />
          ))}
          {[[1400, 562, 1.2], [1300, 560, 1], [1190, 586, 1.3], [1090, 602, 1]].map(([x, y, s]) => (
            <Tree key={`rf${x}`} x={x} y={y} s={s} fill={TREE[1]} />
          ))}
        </g>

        {/* The paper sheet the page sits on (last colour = page background) */}
        <g className="paper-layer">
          <path
            d={`M-20 ${H + 20} V604 C200 574 380 612 600 594 S1000 574 1200 602 S1380 590 1460 598 V${H + 20}Z`}
            fill={PAPER[0]}
          />
        </g>
        <path d={`M-20 ${H + 20} V622 C300 604 600 632 900 616 S1300 624 1460 614 V${H + 20}Z`} fill={PAPER[1]} />
      </svg>
    </div>
  );
}
