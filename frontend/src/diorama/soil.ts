import {
  BufferGeometry,
  CanvasTexture,
  Color,
  Float32BufferAttribute,
  Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  PlaneGeometry,
  SRGBColorSpace,
  Vector2,
  type Texture,
} from "three";
import { fbm } from "./noise";

// One field plot cut out of a larger sawah: 4 × 3 m surface, 1 m soil profile (0–100 cm, the
// SoilGrids depth range). Bunds (pematang) run along the back and left edges only, so the
// front and right faces read as cuts through the field rather than a tray.
export const PLOT = { width: 4, depth: 3, soil: 1, bundHeight: 0.15 };

const halfW = PLOT.width / 2;
const halfD = PLOT.depth / 2;

function bundProfile(distance: number) {
  if (distance < 0.08) return 1;
  if (distance > 0.32) return 0;
  return 0.5 + 0.5 * Math.cos((Math.PI * (distance - 0.08)) / 0.24);
}

export function bundAmount(x: number, z: number) {
  return Math.max(bundProfile(z + halfD), bundProfile(x + halfW));
}

/** Surface height (m) at a point on the plot: bunds plus small clods. */
export function surfaceHeight(x: number, z: number) {
  const bund = bundAmount(x, z) * PLOT.bundHeight * (0.94 + 0.12 * fbm(x * 2.2 + 7, z * 2.2));
  const clods = (fbm(x * 6.5 + 3.1, z * 6.5 - 1.7) - 0.5) * 0.024 + (fbm(x * 21, z * 21) - 0.5) * 0.009;
  return bund + clods;
}

/** Planting area clear of the bunds and slightly inside the cut faces. */
export const PLANTING = { minX: -halfW + 0.38, maxX: halfW - 0.16, minZ: -halfD + 0.38, maxZ: halfD - 0.16 };

function topGeometry() {
  const geometry = new PlaneGeometry(PLOT.width, PLOT.depth, 200, 150);
  geometry.rotateX(-Math.PI / 2);
  const position = geometry.getAttribute("position");
  for (let i = 0; i < position.count; i++) {
    position.setY(i, surfaceHeight(position.getX(i), position.getZ(i)));
  }
  geometry.computeVertexNormals();
  return geometry;
}

/** Vertical cut face along one edge; its top follows the surface heightfield exactly. */
function wallGeometry(side: "front" | "back" | "left" | "right") {
  const samples = side === "front" || side === "back" ? 200 : 150;
  const positions: number[] = [];
  const normals: number[] = [];
  const uvs: number[] = [];
  const indices: number[] = [];
  const normal = { front: [0, 0, 1], back: [0, 0, -1], left: [-1, 0, 0], right: [1, 0, 0] }[side];
  for (let i = 0; i <= samples; i++) {
    const t = i / samples;
    let x: number;
    let z: number;
    if (side === "front") [x, z] = [-halfW + t * PLOT.width, halfD];
    else if (side === "back") [x, z] = [halfW - t * PLOT.width, -halfD];
    else if (side === "right") [x, z] = [halfW, halfD - t * PLOT.depth];
    else [x, z] = [-halfW, -halfD + t * PLOT.depth];
    const top = surfaceHeight(x, z);
    const length = (side === "front" || side === "back" ? PLOT.width : PLOT.depth) * t;
    positions.push(x, top, z, x, -PLOT.soil, z);
    normals.push(...normal, ...normal);
    uvs.push(length, top, length, -PLOT.soil);
    if (i > 0) {
      const a = (i - 1) * 2;
      indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
    }
  }
  const geometry = new BufferGeometry();
  geometry.setAttribute("position", new Float32BufferAttribute(positions, 3));
  geometry.setAttribute("normal", new Float32BufferAttribute(normals, 3));
  geometry.setAttribute("uv", new Float32BufferAttribute(uvs, 2));
  geometry.setIndex(indices);
  return geometry;
}

// ---- Materials ------------------------------------------------------------------

const NOISE_GLSL = /* glsl */ `
float fsHash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123); }
float fsNoise(vec2 p) {
  vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
  float a = fsHash(i), b = fsHash(i + vec2(1.0, 0.0)), c = fsHash(i + vec2(0.0, 1.0)), d = fsHash(i + vec2(1.0, 1.0));
  return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}
float fsFbm(vec2 p) {
  float s = 0.0; float a = 0.5;
  for (int i = 0; i < 4; i++) { s += a * fsNoise(p); p *= 2.03; a *= 0.5; }
  return s;
}
`;

export interface SoilMaterials {
  top: MeshStandardMaterial;
  wall: MeshStandardMaterial;
  applyTextures(textures: SoilTextures): void;
}

export interface SoilTextures {
  fieldDiffuse: Texture;
  fieldNormal: Texture;
  fieldArm: Texture;
  profileDiffuse: Texture;
  profileNormal: Texture;
}

export function createSoilMaterials(): SoilMaterials {
  const top = new MeshStandardMaterial({ color: new Color("#655845"), roughness: 0.97, metalness: 0 });

  // Horizon colours for an illustrative lowland profile: darker puddled topsoil, a denser
  // plough pan, then lighter subsoil with iron mottles. Illustration only, not measured.
  const uniforms = {
    uAp: { value: new Color("#4E4338") },
    uPan: { value: new Color("#5B5248") },
    uB: { value: new Color("#7F6F5D") },
    uBC: { value: new Color("#8A7B68") },
    uRust: { value: new Color("#8C6646") },
    uSurface: { value: new Color("#5E5345") },
    uDetailMean: { value: 0.0601 },
    uHasDetail: { value: 0 },
  };
  const wall = new MeshStandardMaterial({ color: 0xffffff, roughness: 0.96, metalness: 0 });
  wall.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vSoil;")
      .replace("#include <begin_vertex>", "#include <begin_vertex>\nvSoil = position;");
    shader.fragmentShader = shader.fragmentShader
      .replace(
        "#include <common>",
        `#include <common>
varying vec3 vSoil;
uniform vec3 uAp; uniform vec3 uPan; uniform vec3 uB; uniform vec3 uBC; uniform vec3 uRust; uniform vec3 uSurface;
uniform float uDetailMean; uniform float uHasDetail;
${NOISE_GLSL}`,
      )
      .replace(
        "#include <map_fragment>",
        `float detail = 1.0;
#ifdef USE_MAP
  vec4 sampledDiffuseColor = texture2D( map, vMapUv );
  float lum = dot( sampledDiffuseColor.rgb, vec3( 0.2126, 0.7152, 0.0722 ) );
  detail = mix( 1.0, clamp( lum / uDetailMean, 0.62, 1.45 ), 0.7 * uHasDetail );
#endif
  float depth = clamp( -vSoil.y, 0.0, 1.2 );
  float along = vSoil.x * 1.0 + vSoil.z * 1.37;
  float b1 = 0.15 + ( fsFbm( vec2( along * 2.1, 3.0 ) ) - 0.5 ) * 0.06;
  float b2 = 0.23 + ( fsFbm( vec2( along * 1.7, 11.0 ) ) - 0.5 ) * 0.06;
  float b3 = 0.62 + ( fsFbm( vec2( along * 1.2, 23.0 ) ) - 0.5 ) * 0.12;
  vec3 soil = mix( uAp, uPan, smoothstep( b1 - 0.03, b1 + 0.03, depth ) );
  soil = mix( soil, uB, smoothstep( b2 - 0.05, b2 + 0.06, depth ) );
  soil = mix( soil, uBC, smoothstep( b3 - 0.1, b3 + 0.1, depth ) );
  float m = fsNoise( vec2( along * 11.0, depth * 15.0 ) ) * 0.62 + fsNoise( vec2( along * 29.0, depth * 33.0 ) ) * 0.38;
  float mottle = smoothstep( 0.66, 0.82, m ) * smoothstep( b2, b2 + 0.1, depth ) * ( 1.0 - smoothstep( 0.86, 1.02, depth ) );
  soil = mix( soil, uRust, mottle * 0.28 );
  float streak = smoothstep( 0.55, 0.9, fsNoise( vec2( along * 46.0, depth * 3.0 ) ) ) * ( 1.0 - smoothstep( 0.0, b1, depth ) );
  soil *= 1.0 - streak * 0.12;
  soil = mix( soil, uSurface, ( 1.0 - smoothstep( 0.0, 0.03, depth ) ) * 0.45 );
  diffuseColor.rgb *= soil * detail;`,
      );
  };
  wall.customProgramCacheKey = () => "fieldshift-soil-wall-v1";

  return {
    top,
    wall,
    applyTextures(textures) {
      const repeatTop = new Vector2(PLOT.width / 1.5, PLOT.depth / 1.5);
      for (const texture of [textures.fieldDiffuse, textures.fieldNormal, textures.fieldArm]) {
        texture.repeat.copy(repeatTop);
      }
      top.map = textures.fieldDiffuse;
      top.normalMap = textures.fieldNormal;
      top.normalScale.set(0.85, 0.85);
      top.roughnessMap = textures.fieldArm;
      top.aoMap = textures.fieldArm;
      top.aoMapIntensity = 0.75;
      top.roughness = 1;
      top.color.set("#D9D2C9");
      top.needsUpdate = true;

      for (const texture of [textures.profileDiffuse, textures.profileNormal]) texture.repeat.set(1.8, 1.8);
      wall.map = textures.profileDiffuse;
      wall.normalMap = textures.profileNormal;
      wall.normalScale.set(0.5, 0.5);
      uniforms.uHasDetail.value = 1;
      wall.needsUpdate = true;
    },
  };
}

export function createSoilBlock(materials: SoilMaterials) {
  const top = new Mesh(topGeometry(), materials.top);
  top.receiveShadow = true;
  top.castShadow = true;
  const walls = (["front", "right", "back", "left"] as const).map((side) => {
    const mesh = new Mesh(wallGeometry(side), materials.wall);
    mesh.receiveShadow = true;
    mesh.castShadow = true;
    return mesh;
  });
  const bottom = new Mesh(new PlaneGeometry(PLOT.width, PLOT.depth), new MeshStandardMaterial({ color: "#5c4c3e", roughness: 1 }));
  bottom.rotation.x = Math.PI / 2;
  bottom.position.y = -PLOT.soil;
  return [top, ...walls, bottom];
}

/** Soft occlusion where the block meets the page, darkest at the contact line. */
export function contactShadow(): Mesh {
  const margin = 1.1;
  const size = 512;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d");
  const spanX = PLOT.width + margin * 2;
  const spanZ = PLOT.depth + margin * 2;
  if (context) {
    const image = context.createImageData(size, size);
    for (let j = 0; j < size; j++) {
      for (let i = 0; i < size; i++) {
        const x = (i / (size - 1) - 0.5) * spanX;
        const z = (j / (size - 1) - 0.5) * spanZ;
        const dx = Math.max(Math.abs(x) - halfW, 0);
        const dz = Math.max(Math.abs(z) - halfD, 0);
        const distance = Math.hypot(dx, dz);
        const inside = dx === 0 && dz === 0;
        const alpha = inside ? 0.6 : 0.5 * Math.exp(-distance / 0.05) + 0.16 * Math.exp(-distance / 0.32);
        const k = (j * size + i) * 4;
        image.data[k] = 34;
        image.data[k + 1] = 30;
        image.data[k + 2] = 25;
        image.data[k + 3] = Math.round(Math.min(1, alpha) * 255);
      }
    }
    context.putImageData(image, 0, 0);
  }
  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace;
  const mesh = new Mesh(
    new PlaneGeometry(spanX, spanZ),
    new MeshBasicMaterial({ map: texture, transparent: true, depthWrite: false, toneMapped: false }),
  );
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = -PLOT.soil - 0.001;
  mesh.renderOrder = -1;
  return mesh;
}
