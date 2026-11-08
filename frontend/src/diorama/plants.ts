import { BufferGeometry, Color, Float32BufferAttribute, Vector3 } from "three";
import { range, rng, type Random } from "./noise";

// Procedural crop geometry in metres, base at y = 0. Vertex colours carry a little baked
// occlusion near the base so plants read as rooted without a separate AO pass.

class Builder {
  positions: number[] = [];
  colors: number[] = [];
  indices: number[] = [];

  vertex(p: Vector3, c: Color) {
    this.positions.push(p.x, p.y, p.z);
    this.colors.push(c.r, c.g, c.b);
    return this.positions.length / 3 - 1;
  }

  tri(a: number, b: number, c: number) {
    this.indices.push(a, b, c);
  }

  build(): BufferGeometry {
    const geometry = new BufferGeometry();
    geometry.setAttribute("position", new Float32BufferAttribute(this.positions, 3));
    geometry.setAttribute("color", new Float32BufferAttribute(this.colors, 3));
    geometry.setIndex(this.indices);
    geometry.computeVertexNormals();
    geometry.computeBoundingSphere();
    return geometry;
  }
}

const UP = new Vector3(0, 1, 0);
const tmpColor = new Color();

function shade(base: Color, tip: Color, t: number, baseShade: number, out = tmpColor) {
  out.copy(base).lerp(tip, Math.pow(t, 0.85));
  const occlusion = 1 - baseShade * (1 - smoothstep(0, 0.3, t));
  return out.multiplyScalar(occlusion);
}

function smoothstep(a: number, b: number, x: number) {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
}

interface LeafSpec {
  origin: Vector3;
  azimuth: number;
  tilt: number;
  bend: number;
  bendPower?: number;
  length: number;
  width: number;
  segments: number;
  fold: number;
  twist?: number;
  profile: (t: number) => number;
  base: Color;
  tip: Color;
  baseShade: number;
  midrib?: number;
}

/** A tapered, slightly folded blade swept along a curve that leans out and droops. */
function leaf(builder: Builder, spec: LeafSpec) {
  const { origin, azimuth, tilt, bend, length, width, segments, fold, profile } = spec;
  const power = spec.bendPower ?? 1.6;
  const step = length / segments;
  const point = origin.clone();
  const side0 = new Vector3(-Math.sin(azimuth), 0, Math.cos(azimuth));
  let previous: [number, number, number] | null = null;
  const color = new Color();
  const midColor = new Color();
  for (let i = 0; i <= segments; i++) {
    const t = i / segments;
    const angle = tilt + bend * Math.pow(t, power);
    const dir = new Vector3(Math.sin(angle) * Math.cos(azimuth), Math.cos(angle), Math.sin(angle) * Math.sin(azimuth));
    const side = side0.clone().applyAxisAngle(dir, (spec.twist ?? 0) * t);
    const normal = new Vector3().crossVectors(side, dir).normalize();
    const w = width * profile(t);
    shade(spec.base, spec.tip, t, spec.baseShade, color);
    midColor.copy(color).multiplyScalar(1 + (spec.midrib ?? 0.06));
    const left = point.clone().addScaledVector(side, -w / 2);
    const right = point.clone().addScaledVector(side, w / 2);
    const mid = point.clone().addScaledVector(normal, -fold * w);
    const ids: [number, number, number] = [builder.vertex(left, color), builder.vertex(mid, midColor), builder.vertex(right, color)];
    if (previous) {
      const [l0, m0, r0] = previous;
      const [l1, m1, r1] = ids;
      builder.tri(l0, m0, l1);
      builder.tri(m0, m1, l1);
      builder.tri(m0, r0, m1);
      builder.tri(r0, r1, m1);
    }
    previous = ids;
    point.addScaledVector(dir, step);
  }
}

/** A thin tube along a polyline, used for stalks, petioles and panicle axes. */
function tube(builder: Builder, points: Vector3[], radii: number[], colors: Color[], radial = 5) {
  const rings: number[][] = [];
  for (let i = 0; i < points.length; i++) {
    const forward = (i < points.length - 1 ? points[i + 1].clone().sub(points[i]) : points[i].clone().sub(points[i - 1])).normalize();
    const helper = Math.abs(forward.y) > 0.95 ? new Vector3(1, 0, 0) : UP;
    const a = new Vector3().crossVectors(forward, helper).normalize();
    const b = new Vector3().crossVectors(forward, a).normalize();
    const ring: number[] = [];
    for (let k = 0; k < radial; k++) {
      const theta = (k / radial) * Math.PI * 2;
      const p = points[i].clone().addScaledVector(a, Math.cos(theta) * radii[i]).addScaledVector(b, Math.sin(theta) * radii[i]);
      ring.push(builder.vertex(p, colors[i]));
    }
    rings.push(ring);
  }
  for (let i = 0; i < rings.length - 1; i++) {
    for (let k = 0; k < radial; k++) {
      const a = rings[i][k];
      const b = rings[i][(k + 1) % radial];
      const c = rings[i + 1][k];
      const d = rings[i + 1][(k + 1) % radial];
      builder.tri(a, c, b);
      builder.tri(b, c, d);
    }
  }
}

/** Flat ovate leaflet, slightly cupped, facing roughly upwards. */
function leaflet(builder: Builder, base: Vector3, forward: Vector3, up: Vector3, length: number, width: number, color: Color, cup: number) {
  const side = new Vector3().crossVectors(forward, up).normalize();
  const n = 10;
  const tipColor = color.clone().multiplyScalar(1.06);
  const centre = base.clone().addScaledVector(forward, length * 0.45).addScaledVector(up, cup * width * 0.5);
  const c = builder.vertex(centre, tipColor);
  const rim: number[] = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    // Ovate outline: wider towards the base, pointed tip.
    const along = (Math.cos(a) * 0.5 + 0.5) * length;
    const across = Math.sin(a) * width * 0.5 * (1 - 0.35 * Math.pow(Math.cos(a) * 0.5 + 0.5, 2));
    const p = base.clone().addScaledVector(forward, along).addScaledVector(side, across);
    rim.push(builder.vertex(p, color));
  }
  for (let i = 0; i < n; i++) builder.tri(c, rim[i], rim[(i + 1) % n]);
}

// ---- Palette (sRGB references from the art direction, converted to linear by Color) ----
const P = {
  riceBase: new Color("#4C5E2F"),
  riceTip: new Color("#8C9550"),
  panicle: new Color("#A99F5E"),
  panicleTip: new Color("#B9A766"),
  cornLeafBase: new Color("#3F5636"),
  cornLeafTip: new Color("#6F7F45"),
  cornStalk: new Color("#6A7A42"),
  tassel: new Color("#B39A60"),
  husk: new Color("#8C9858"),
  silk: new Color("#8A6440"),
  soyStem: new Color("#5E6B36"),
  soyLeaf: new Color("#4E6A35"),
  soyLeafLight: new Color("#647347"),
  grassBase: new Color("#55603A"),
  grassTip: new Color("#8F9459"),
};

const riceProfile = (t: number) => Math.pow(Math.sin(Math.PI * Math.min(1, 0.08 + t * 0.94)), 0.55) * (1 - 0.15 * t);
const cornProfile = (t: number) => (t < 0.08 ? 0.45 + t * 6 : Math.pow(Math.sin(Math.PI * (0.06 + t * 0.94)), 0.7));
const grassProfile = (t: number) => 1 - t * 0.92;

export function riceHill(seed: number): BufferGeometry {
  const random = rng(seed);
  const b = new Builder();
  const blades = 14 + Math.floor(random() * 5);
  for (let i = 0; i < blades; i++) {
    const azimuth = random() * Math.PI * 2;
    const origin = new Vector3(Math.cos(azimuth) * 0.01, 0, Math.sin(azimuth) * 0.01);
    leaf(b, {
      origin,
      azimuth,
      tilt: range(random, 0.03, 0.3),
      bend: range(random, 0.18, 0.85),
      length: range(random, 0.42, 0.74),
      width: range(random, 0.013, 0.018),
      segments: 7,
      fold: 0.2,
      twist: range(random, -0.6, 0.6),
      profile: riceProfile,
      base: P.riceBase,
      tip: P.riceTip.clone().lerp(P.riceBase, range(random, 0, 0.35)),
      baseShade: 0.45,
    });
  }
  // Panicles: an upright culm that arches over at the top, carrying the grain head.
  const panicles = 2 + Math.floor(random() * 3);
  for (let i = 0; i < panicles; i++) {
    const azimuth = random() * Math.PI * 2;
    const lean = range(random, 0.05, 0.18);
    const height = range(random, 0.68, 0.84);
    const points: Vector3[] = [];
    const radii: number[] = [];
    const colors: Color[] = [];
    for (let k = 0; k <= 6; k++) {
      const t = k / 6;
      points.push(new Vector3(Math.cos(azimuth) * lean * t * height, t * height, Math.sin(azimuth) * lean * t * height));
      radii.push(0.0032 * (1 - t * 0.4));
      colors.push(shade(P.riceBase, P.riceTip, t, 0.4).clone());
    }
    tube(b, points, radii, colors, 4);
    leaf(b, {
      origin: points[points.length - 1],
      azimuth,
      tilt: range(random, 0.5, 0.8),
      bend: range(random, 1.5, 2.1),
      bendPower: 1.2,
      length: range(random, 0.2, 0.26),
      width: 0.022,
      segments: 6,
      fold: 0.35,
      profile: (t) => Math.pow(Math.sin(Math.PI * (0.12 + t * 0.88)), 0.6),
      base: P.panicle,
      tip: P.panicleTip,
      baseShade: 0,
      midrib: 0.1,
    });
  }
  return b.build();
}

export function cornPlant(seed: number): BufferGeometry {
  const random = rng(seed);
  const b = new Builder();
  const height = range(random, 1.95, 2.2);
  const lean = new Vector3(range(random, -0.04, 0.04), 0, range(random, -0.04, 0.04));
  const stalkAt = (t: number) => new Vector3(lean.x * t * t * height, t * height, lean.z * t * t * height);
  const stalk: Vector3[] = [];
  const radii: number[] = [];
  const colors: Color[] = [];
  for (let k = 0; k <= 12; k++) {
    const t = k / 12;
    stalk.push(stalkAt(t * 0.9));
    radii.push(0.019 * (1 - t * 0.55));
    colors.push(shade(P.cornStalk.clone().multiplyScalar(0.85), P.cornStalk, t, 0.35).clone());
  }
  tube(b, stalk, radii, colors, 6);

  const leaves = 11 + Math.floor(random() * 3);
  const phase = random() * Math.PI * 2;
  for (let i = 0; i < leaves; i++) {
    const t = 0.08 + (i / leaves) * 0.78;
    const node = stalkAt(t * 0.9);
    const azimuth = phase + i * Math.PI + range(random, -0.35, 0.35);
    const middle = 1 - Math.abs(t - 0.45) * 1.4;
    leaf(b, {
      origin: node.clone().add(new Vector3(Math.cos(azimuth) * 0.012, 0, Math.sin(azimuth) * 0.012)),
      azimuth,
      tilt: range(random, 0.45, 0.75),
      bend: range(random, 0.9, 1.55) * (0.75 + 0.35 * t),
      bendPower: 1.5,
      length: Math.max(0.42, 0.95 * middle + range(random, -0.06, 0.06)),
      width: range(random, 0.065, 0.085),
      segments: 14,
      fold: 0.12,
      twist: range(random, -0.5, 0.5),
      profile: cornProfile,
      base: P.cornLeafBase,
      tip: P.cornLeafTip.clone().lerp(P.tassel, range(random, 0, 0.12)),
      baseShade: 0.3,
      midrib: 0.14,
    });
  }

  // Tassel branches at the top.
  const top = stalkAt(0.9);
  const spike = [top.clone(), top.clone().add(new Vector3(0, 0.22, 0))];
  tube(b, spike, [0.006, 0.002], [P.tassel, P.tassel], 4);
  const branches = 7 + Math.floor(random() * 4);
  for (let i = 0; i < branches; i++) {
    const azimuth = random() * Math.PI * 2;
    leaf(b, {
      origin: top.clone().add(new Vector3(0, range(random, 0.02, 0.12), 0)),
      azimuth,
      tilt: range(random, 0.35, 0.8),
      bend: range(random, 0.5, 1.0),
      length: range(random, 0.14, 0.24),
      width: 0.008,
      segments: 4,
      fold: 0,
      profile: (t) => 1 - t * 0.6,
      base: P.tassel.clone().multiplyScalar(0.92),
      tip: P.tassel,
      baseShade: 0,
    });
  }

  // One ear in its husk with a silk tuft.
  const earT = range(random, 0.42, 0.5);
  const earBase = stalkAt(earT * 0.9);
  const earAz = phase + range(random, 0.4, 1.2);
  const earDir = new Vector3(Math.sin(0.42) * Math.cos(earAz), Math.cos(0.42), Math.sin(0.42) * Math.sin(earAz));
  const earPoints: Vector3[] = [];
  const earRadii: number[] = [];
  const earColors: Color[] = [];
  for (let k = 0; k <= 6; k++) {
    const t = k / 6;
    earPoints.push(earBase.clone().addScaledVector(earDir, 0.03 + t * 0.2));
    earRadii.push(0.03 * Math.pow(Math.sin(Math.PI * (0.15 + t * 0.8)), 0.6));
    earColors.push(P.husk.clone().multiplyScalar(0.92 + t * 0.12));
  }
  tube(b, earPoints, earRadii, earColors, 7);
  const silkBase = earPoints[earPoints.length - 1];
  for (let i = 0; i < 4; i++) {
    leaf(b, {
      origin: silkBase,
      azimuth: earAz + range(random, -0.8, 0.8),
      tilt: range(random, 0.5, 0.9),
      bend: range(random, 0.6, 1.2),
      length: range(random, 0.05, 0.08),
      width: 0.006,
      segments: 3,
      fold: 0,
      profile: (t) => 1 - t * 0.7,
      base: P.silk,
      tip: P.silk,
      baseShade: 0,
    });
  }
  return b.build();
}

export function soyPlant(seed: number): BufferGeometry {
  const random = rng(seed);
  const b = new Builder();
  const height = range(random, 0.6, 0.78);
  const stems: { base: Vector3; azimuth: number; lean: number; height: number }[] = [
    { base: new Vector3(0, 0, 0), azimuth: random() * Math.PI * 2, lean: range(random, 0.02, 0.1), height },
  ];
  const branches = 2 + Math.floor(random() * 2);
  for (let i = 0; i < branches; i++) {
    stems.push({
      base: new Vector3(0, range(random, 0.06, 0.16), 0),
      azimuth: random() * Math.PI * 2,
      lean: range(random, 0.3, 0.55),
      height: height * range(random, 0.55, 0.78),
    });
  }
  const leafColor = new Color();
  for (const stem of stems) {
    const dir = new Vector3(Math.sin(stem.lean) * Math.cos(stem.azimuth), Math.cos(stem.lean), Math.sin(stem.lean) * Math.sin(stem.azimuth));
    const points: Vector3[] = [];
    const radii: number[] = [];
    const colors: Color[] = [];
    for (let k = 0; k <= 5; k++) {
      const t = k / 5;
      points.push(stem.base.clone().addScaledVector(dir, t * stem.height).add(new Vector3(0, 0, range(random, -0.006, 0.006))));
      radii.push(0.0055 * (1 - t * 0.5));
      colors.push(shade(P.soyStem.clone().multiplyScalar(0.8), P.soyStem, t, 0.3).clone());
    }
    tube(b, points, radii, colors, 4);
    const nodes = 4 + Math.floor(random() * 3);
    for (let n = 0; n < nodes; n++) {
      const t = 0.3 + (n / Math.max(1, nodes - 1)) * 0.7;
      const node = stem.base.clone().addScaledVector(dir, t * stem.height);
      const azimuth = stem.azimuth + n * 2.4 + range(random, -0.4, 0.4);
      // Upper petioles spread outward so no trifoliate stands above the canopy on a bare stalk.
      const rise = t > 0.8 ? range(random, 0.9, 1.25) : range(random, 0.55, 0.95);
      const petioleDir = new Vector3(Math.sin(rise) * Math.cos(azimuth), Math.cos(rise), Math.sin(rise) * Math.sin(azimuth));
      const petioleLength = range(random, 0.07, 0.13);
      const tip = node.clone().addScaledVector(petioleDir, petioleLength);
      tube(b, [node, tip], [0.0025, 0.0018], [P.soyStem, P.soyStem], 3);
      const forward = new Vector3(petioleDir.x, petioleDir.y * 0.25 - 0.08, petioleDir.z).normalize();
      const up = new Vector3().crossVectors(new Vector3().crossVectors(forward, UP), forward).normalize();
      if (up.y < 0) up.negate();
      leafColor.copy(P.soyLeaf).lerp(P.soyLeafLight, range(random, 0, 0.7)).multiplyScalar(0.82 + t * 0.22);
      const length = range(random, 0.085, 0.115);
      const width = length * range(random, 0.56, 0.68);
      leaflet(b, tip, forward, up, length, width, leafColor, range(random, 0.05, 0.25));
      for (const turn of [-1.05, 1.05]) {
        const lateral = forward.clone().applyAxisAngle(up, turn + range(random, -0.15, 0.15));
        leaflet(b, tip, lateral, up, length * 0.86, width * 0.9, leafColor, range(random, 0.05, 0.25));
      }
    }
  }
  return b.build();
}

export function grassTuft(seed: number): BufferGeometry {
  const random = rng(seed);
  const b = new Builder();
  const blades = 6 + Math.floor(random() * 4);
  for (let i = 0; i < blades; i++) {
    const azimuth = random() * Math.PI * 2;
    leaf(b, {
      origin: new Vector3(Math.cos(azimuth) * 0.01, 0, Math.sin(azimuth) * 0.01),
      azimuth,
      tilt: range(random, 0.15, 0.7),
      bend: range(random, 0.2, 0.9),
      length: range(random, 0.05, 0.13),
      width: 0.007,
      segments: 3,
      fold: 0,
      profile: grassProfile,
      base: P.grassBase,
      tip: P.grassTip.clone().lerp(P.grassBase, range(random, 0, 0.5)),
      baseShade: 0.35,
    });
  }
  return b.build();
}

export type { Random };
