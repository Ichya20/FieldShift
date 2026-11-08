import {
  Color,
  DirectionalLight,
  DoubleSide,
  Euler,
  HemisphereLight,
  InstancedMesh,
  Matrix4,
  Mesh,
  MeshDepthMaterial,
  MeshStandardMaterial,
  NeutralToneMapping,
  PCFShadowMap,
  PerspectiveCamera,
  PlaneGeometry,
  PMREMGenerator,
  Quaternion,
  RGBADepthPacking,
  RepeatWrapping,
  Scene,
  ShadowMaterial,
  SRGBColorSpace,
  TextureLoader,
  Vector3,
  WebGLRenderer,
  type BufferGeometry,
  type Texture,
} from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { range, rng } from "./noise";
import { cornPlant, grassTuft, riceHill, soyPlant } from "./plants";
import { PLANTING, PLOT, bundAmount, contactShadow, createSoilBlock, createSoilMaterials, surfaceHeight } from "./soil";
import type { CropId } from "../lib/types";

export interface DioramaOptions {
  reducedMotion: boolean;
  lowPower: boolean;
  interactive: boolean;
  onContextLost?: () => void;
}

export interface DioramaHandle {
  show(crop: CropId, token: string): void;
  setActive(active: boolean): void;
  setReducedMotion(reduced: boolean): void;
  rotateBy(degrees: number): void;
  resetView(): void;
  resize(): void;
  dispose(): void;
}

// ---- Plant material: rooted wind sway + thin-leaf translucency from the key light ----

const SWAY = /* glsl */ `
#ifdef USE_INSTANCING
  vec2 swayOrigin = vec2( instanceMatrix[3].x, instanceMatrix[3].z );
#else
  vec2 swayOrigin = vec2( 0.0 );
#endif
  float swayH = clamp( position.y / uPlantHeight, 0.0, 1.0 );
  float swayW = swayH * swayH;
  float swayPhase = dot( swayOrigin, vec2( 1.7, 2.3 ) );
  transformed.x += sin( uTime * 1.25 + swayPhase ) * uSway * swayW;
  transformed.z += sin( uTime * 0.85 + swayPhase * 1.31 + 1.7 ) * uSway * 0.6 * swayW;
`;

function plantMaterial(time: { value: number }, sway: number, plantHeight: number, translucency: number, roughness: number) {
  const uniforms = { uTime: time, uSway: { value: sway }, uPlantHeight: { value: plantHeight }, uTranslucency: { value: translucency } };
  const injectVertex = (shader: { uniforms: Record<string, unknown>; vertexShader: string }) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nuniform float uTime;\nuniform float uSway;\nuniform float uPlantHeight;")
      .replace("#include <begin_vertex>", `#include <begin_vertex>\n${SWAY}`);
  };
  const material = new MeshStandardMaterial({ vertexColors: true, side: DoubleSide, roughness, metalness: 0 });
  material.shadowSide = DoubleSide;
  material.onBeforeCompile = (shader) => {
    injectVertex(shader);
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <common>", "#include <common>\nuniform float uTranslucency;")
      .replace(
        "#include <lights_fragment_end>",
        `#include <lights_fragment_end>
#if NUM_DIR_LIGHTS > 0
  {
    float backLit = saturate( dot( -normal, directionalLights[ 0 ].direction ) );
    reflectedLight.directDiffuse += diffuseColor.rgb * directionalLights[ 0 ].color * backLit * uTranslucency;
  }
#endif`,
      );
  };
  material.customProgramCacheKey = () => `fieldshift-plant-${plantHeight}`;
  const depth = new MeshDepthMaterial({ depthPacking: RGBADepthPacking, side: DoubleSide });
  depth.onBeforeCompile = injectVertex;
  depth.customProgramCacheKey = () => `fieldshift-plant-depth-${plantHeight}`;
  return { material, depth, uniforms };
}

// ---- Crop stands -------------------------------------------------------------------

interface Placement {
  mesh: InstancedMesh;
  index: number;
  position: Vector3;
  quaternion: Quaternion;
  scale: number;
  delay: number;
}

interface Stand {
  crop: CropId;
  meshes: InstancedMesh[];
  placements: Placement[];
  growth: number;
}

const tmpMatrix = new Matrix4();
const tmpScale = new Vector3();
const tmpColor = new Color();

function makeStand(
  crop: CropId,
  variants: BufferGeometry[],
  points: { x: number; z: number }[],
  material: MeshStandardMaterial,
  depth: MeshDepthMaterial,
  seed: number,
  scaleRange: [number, number],
): Stand {
  const random = rng(seed);
  const buckets: { x: number; z: number }[][] = variants.map(() => []);
  points.forEach((point) => buckets[Math.floor(random() * variants.length)].push(point));
  const meshes: InstancedMesh[] = [];
  const placements: Placement[] = [];
  const spanX = PLANTING.maxX - PLANTING.minX;
  variants.forEach((geometry, v) => {
    const bucket = buckets[v];
    if (!bucket.length) return;
    const mesh = new InstancedMesh(geometry, material, bucket.length);
    mesh.customDepthMaterial = depth;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.frustumCulled = false;
    bucket.forEach((point, index) => {
      const position = new Vector3(point.x, surfaceHeight(point.x, point.z) - 0.01, point.z);
      const quaternion = new Quaternion().setFromEuler(new Euler(range(random, -0.05, 0.05), random() * Math.PI * 2, range(random, -0.05, 0.05)));
      const scale = range(random, scaleRange[0], scaleRange[1]);
      const delay = ((point.x - PLANTING.minX) / spanX) * 0.42 + random() * 0.08;
      placements.push({ mesh, index, position, quaternion, scale, delay });
      tmpColor.setScalar(range(random, 0.86, 1.08));
      tmpColor.g *= range(random, 0.97, 1.03);
      mesh.setColorAt(index, tmpColor);
    });
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    meshes.push(mesh);
  });
  const stand: Stand = { crop, meshes, placements, growth: 1 };
  setGrowth(stand, 0);
  return stand;
}

const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);

function setGrowth(stand: Stand, growth: number) {
  stand.growth = growth;
  for (const p of stand.placements) {
    const local = Math.min(1, Math.max(0, (growth * 1.5 - p.delay) / 1.0));
    const s = easeOut(local);
    const visible = s > 0.002;
    const lateral = p.scale * (0.3 + 0.7 * s);
    tmpScale.set(lateral, p.scale * Math.max(s, 0.0001), lateral);
    tmpMatrix.compose(p.position, p.quaternion, visible ? tmpScale : tmpScale.setScalar(0.0001));
    p.mesh.setMatrixAt(p.index, tmpMatrix);
  }
  for (const mesh of stand.meshes) {
    mesh.instanceMatrix.needsUpdate = true;
    mesh.visible = growth > 0.001;
  }
}

function grid(stepX: number, stepZ: number, jitter: number, seed: number, rowOffset = 0) {
  const random = rng(seed);
  const points: { x: number; z: number }[] = [];
  let row = 0;
  for (let z = PLANTING.minZ; z <= PLANTING.maxZ + 1e-6; z += stepZ, row++) {
    const shift = (row % 2) * rowOffset;
    for (let x = PLANTING.minX + shift; x <= PLANTING.maxX + 1e-6; x += stepX) {
      points.push({ x: x + range(random, -jitter, jitter), z: z + range(random, -jitter, jitter) });
    }
  }
  return points;
}

// ---- Scene --------------------------------------------------------------------------

const DEG = Math.PI / 180;
const DEFAULT_VIEW = { azimuth: 38 * DEG, polar: 61 * DEG };
const TARGET = new Vector3(0, 0.2, 0);
const FRAME_BOX = [-2.05, 2.05, -1.04, 2.05, -1.58, 1.58];

export function createDiorama(canvas: HTMLCanvasElement, options: DioramaOptions): DioramaHandle {
  const renderer = new WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "high-performance" });
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = NeutralToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = PCFShadowMap;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, options.lowPower ? 1.25 : 2));

  const scene = new Scene();
  const pmrem = new PMREMGenerator(renderer);
  const environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environment = environment;
  scene.environmentIntensity = 0.32;

  const camera = new PerspectiveCamera(24, 1, 0.5, 80);

  // Daylight key from upper left, slightly in front of the viewer; shadows fall back-right.
  const sun = new DirectionalLight(new Color("#FFF6EA"), 2.7);
  sun.position.set(-3.2, 9.4, 6.4);
  sun.target.position.copy(TARGET);
  sun.castShadow = true;
  sun.shadow.mapSize.set(options.lowPower ? 1024 : 2048, options.lowPower ? 1024 : 2048);
  sun.shadow.camera.left = -4.2;
  sun.shadow.camera.right = 4.2;
  sun.shadow.camera.top = 4.2;
  sun.shadow.camera.bottom = -4.2;
  sun.shadow.camera.near = 2;
  sun.shadow.camera.far = 24;
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.018;
  sun.shadow.radius = 2.2;
  scene.add(sun, sun.target);
  // Fill keeps the shaded faces readable without flattening them.
  scene.add(new HemisphereLight(new Color("#E6ECF0"), new Color("#8C8070"), 0.55));
  const fill = new DirectionalLight(new Color("#E9EEF2"), 0.32);
  fill.position.set(6, 3, -2);
  scene.add(fill);

  // Ground: only shadows land on the page colour; the block itself carries a contact gradient.
  const ground = new Mesh(new PlaneGeometry(16, 16), new ShadowMaterial({ color: new Color("#3B352C"), opacity: 0.2 }));
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -PLOT.soil - 0.002;
  ground.receiveShadow = true;
  scene.add(ground, contactShadow());

  const soilMaterials = createSoilMaterials();
  scene.add(...createSoilBlock(soilMaterials));

  // Shared time uniform for sway.
  const time = { value: 0 };
  const density = options.lowPower ? 0.72 : 1;

  // Grass on the bunds stays identical in every scenario.
  {
    const grass = plantMaterial(time, 0.006, 0.13, 0.12, 0.7);
    const random = rng(41);
    const points: { x: number; z: number }[] = [];
    const count = Math.round(520 * density);
    for (let i = 0; i < count; i++) {
      const alongBack = random() < PLOT.width / (PLOT.width + PLOT.depth);
      const x = alongBack ? range(random, -PLOT.width / 2, PLOT.width / 2) : range(random, -PLOT.width / 2, -PLOT.width / 2 + 0.26);
      const z = alongBack ? range(random, -PLOT.depth / 2, -PLOT.depth / 2 + 0.26) : range(random, -PLOT.depth / 2, PLOT.depth / 2);
      if (bundAmount(x, z) > 0.55) points.push({ x, z });
    }
    const stand = makeStand("padi", [grassTuft(3), grassTuft(5), grassTuft(8)], points, grass.material, grass.depth, 7, [0.8, 1.25]);
    setGrowth(stand, 1);
    scene.add(...stand.meshes);
  }

  const builders: Record<CropId, () => Stand> = {
    padi: () => {
      const m = plantMaterial(time, 0.02, 0.85, 0.2, 0.62);
      return makeStand("padi", [riceHill(11), riceHill(23), riceHill(37), riceHill(51)], grid(0.28 / Math.sqrt(density), 0.28, 0.02, 2), m.material, m.depth, 13, [0.9, 1.06]);
    },
    jagung: () => {
      const m = plantMaterial(time, 0.035, 2.3, 0.2, 0.58);
      return makeStand("jagung", [cornPlant(5), cornPlant(17), cornPlant(29)], grid(0.25 / Math.sqrt(density), 0.7, 0.03, 4), m.material, m.depth, 19, [0.92, 1.06]);
    },
    kedelai: () => {
      const m = plantMaterial(time, 0.01, 0.8, 0.24, 0.64);
      return makeStand("kedelai", [soyPlant(3), soyPlant(9), soyPlant(21), soyPlant(33)], grid(0.22 / Math.sqrt(density), 0.42, 0.025, 6, 0.11), m.material, m.depth, 29, [0.9, 1.08]);
    },
  };
  const stands = new Map<CropId, Stand>();
  const standFor = (crop: CropId) => {
    let stand = stands.get(crop);
    if (!stand) {
      stand = builders[crop]();
      stands.set(crop, stand);
      scene.add(...stand.meshes);
    }
    return stand;
  };

  // ---- Camera framing ------------------------------------------------------------------
  let azimuth = DEFAULT_VIEW.azimuth;
  let polar = DEFAULT_VIEW.polar;
  let distance = 14;
  const corners = [] as Vector3[];
  for (const x of [FRAME_BOX[0], FRAME_BOX[1]])
    for (const y of [FRAME_BOX[2], FRAME_BOX[3]]) for (const z of [FRAME_BOX[4], FRAME_BOX[5]]) corners.push(new Vector3(x, y, z));

  const place = () => {
    camera.position.set(
      TARGET.x + distance * Math.sin(polar) * Math.sin(azimuth),
      TARGET.y + distance * Math.cos(polar),
      TARGET.z + distance * Math.sin(polar) * Math.cos(azimuth),
    );
    camera.lookAt(TARGET);
    camera.updateMatrixWorld();
  };

  const fits = () => {
    const ndc = new Vector3();
    for (const corner of corners) {
      ndc.copy(corner).project(camera);
      if (Math.abs(ndc.x) > 0.94 || Math.abs(ndc.y) > 0.92) return false;
    }
    return true;
  };

  const frame = () => {
    const saved = [azimuth, polar];
    [azimuth, polar] = [DEFAULT_VIEW.azimuth, DEFAULT_VIEW.polar];
    let low = 4;
    let high = 60;
    for (let i = 0; i < 18; i++) {
      distance = (low + high) / 2;
      place();
      if (fits()) high = distance;
      else low = distance;
    }
    distance = high;
    [azimuth, polar] = saved;
    place();
  };

  // ---- Interaction ------------------------------------------------------------------
  let controls: OrbitControls | null = null;
  if (options.interactive) {
    controls = new OrbitControls(camera, canvas);
    controls.target.copy(TARGET);
    controls.enableZoom = false;
    controls.enablePan = false;
    controls.enableDamping = true;
    controls.dampingFactor = 0.09;
    controls.rotateSpeed = 0.5;
    controls.minPolarAngle = 50 * DEG;
    controls.maxPolarAngle = 70 * DEG;
    controls.minAzimuthAngle = 4 * DEG;
    controls.maxAzimuthAngle = 78 * DEG;
    controls.addEventListener("change", () => invalidate());
  }

  // ---- Render loop -------------------------------------------------------------------
  let active = true;
  let reducedMotion = options.reducedMotion;
  let frameRequest = 0;
  let last = performance.now();
  let needsRender = true;
  let swayFrame = 0;

  interface Tween {
    stand: Stand;
    from: number;
    to: number;
    start: number;
    duration: number;
    done?: () => void;
  }
  let tweens: Tween[] = [];

  const schedule = () => {
    if (!frameRequest && active) frameRequest = requestAnimationFrame(loop);
  };
  const invalidate = () => {
    needsRender = true;
    schedule();
  };

  function loop(now: number) {
    frameRequest = 0;
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    let animating = false;
    if (tweens.length) {
      const finished: Tween[] = [];
      for (const tween of tweens) {
        const t = Math.min(1, (now - tween.start) / tween.duration);
        setGrowth(tween.stand, tween.from + (tween.to - tween.from) * t);
        if (t >= 1) finished.push(tween);
      }
      tweens = tweens.filter((tween) => !finished.includes(tween));
      finished.forEach((tween) => tween.done?.());
      animating = true;
      needsRender = true;
    }
    if (controls && controls.update()) {
      animating = true;
      needsRender = true;
    }
    const sway = !reducedMotion && !options.lowPower;
    if (sway) {
      time.value += dt;
      swayFrame++;
      // Sway alone renders at half rate; transitions and orbiting render every frame.
      if (animating || swayFrame % 2 === 0) needsRender = true;
    }
    if (needsRender) {
      renderer.render(scene, camera);
      needsRender = false;
    }
    if (animating || sway) schedule();
  }

  // ---- Crop changes --------------------------------------------------------------------
  let current: Stand | null = null;
  let currentToken = "";

  const show = (crop: CropId, token: string) => {
    if (token === currentToken) return;
    currentToken = token;
    const next = standFor(crop);
    current = next;
    const now = performance.now();
    tweens = [];
    if (reducedMotion) {
      for (const stand of stands.values()) setGrowth(stand, stand === next ? 1 : 0);
      invalidate();
      return;
    }
    const grow = () => {
      if (current !== next || currentToken !== token) return;
      tweens = tweens.filter((tween) => tween.stand !== next);
      tweens.push({ stand: next, from: 0, to: 1, start: performance.now(), duration: 1250 });
      last = performance.now();
      invalidate();
    };
    // Every other stand that is still (partly) visible leaves first; the field is the same plot.
    let exitDuration = 0;
    for (const stand of stands.values()) {
      if (stand.growth <= 0.001) continue;
      const duration = 380 * stand.growth;
      exitDuration = Math.max(exitDuration, duration);
      tweens.push({ stand, from: stand.growth, to: 0, start: now, duration });
    }
    if (exitDuration > 0) setTimeout(grow, Math.max(0, exitDuration - 40));
    else {
      setGrowth(next, 0);
      grow();
    }
    last = performance.now();
    invalidate();
  };

  // ---- Textures (progressive) -------------------------------------------------------------
  const loader = new TextureLoader();
  const load = (url: string, color: boolean) =>
    new Promise<Texture>((resolve, reject) =>
      loader.load(
        url,
        (texture) => {
          texture.wrapS = texture.wrapT = RepeatWrapping;
          texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
          if (color) texture.colorSpace = SRGBColorSpace;
          resolve(texture);
        },
        undefined,
        reject,
      ),
    );
  let disposed = false;
  Promise.all([
    load("/textures/field-soil-diffuse.webp", true),
    load("/textures/field-soil-normal.webp", false),
    load("/textures/field-soil-arm.webp", false),
    load("/textures/profile-soil-diffuse.webp", true),
    load("/textures/profile-soil-normal.webp", false),
  ])
    .then(([fieldDiffuse, fieldNormal, fieldArm, profileDiffuse, profileNormal]) => {
      if (disposed) return;
      soilMaterials.applyTextures({ fieldDiffuse, fieldNormal, fieldArm, profileDiffuse, profileNormal });
      invalidate();
    })
    .catch(() => {
      // Plain material colours remain; the illustration stays usable without textures.
    });

  const resize = () => {
    const parent = canvas.parentElement;
    if (!parent) return;
    const width = Math.max(1, parent.clientWidth);
    const height = Math.max(1, parent.clientHeight);
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    frame();
    if (controls) {
      controls.target.copy(TARGET);
      controls.update();
    }
    invalidate();
  };

  const observer = new ResizeObserver(resize);
  if (canvas.parentElement) observer.observe(canvas.parentElement);

  const onLost = (event: Event) => {
    event.preventDefault();
    options.onContextLost?.();
  };
  canvas.addEventListener("webglcontextlost", onLost);

  resize();

  return {
    show,
    setActive(next) {
      active = next;
      if (active) {
        last = performance.now();
        invalidate();
      } else if (frameRequest) {
        cancelAnimationFrame(frameRequest);
        frameRequest = 0;
      }
    },
    setReducedMotion(next) {
      reducedMotion = next;
      if (reducedMotion && current) {
        tweens = [];
        for (const stand of stands.values()) setGrowth(stand, stand === current ? 1 : 0);
      }
      invalidate();
    },
    rotateBy(degrees) {
      const offset = camera.position.clone().sub(TARGET);
      azimuth = Math.atan2(offset.x, offset.z);
      polar = Math.acos(Math.min(1, Math.max(-1, offset.y / offset.length())));
      azimuth = Math.min(78 * DEG, Math.max(4 * DEG, azimuth + degrees * DEG));
      place();
      controls?.update();
      invalidate();
    },
    resetView() {
      azimuth = DEFAULT_VIEW.azimuth;
      polar = DEFAULT_VIEW.polar;
      place();
      if (controls) {
        controls.target.copy(TARGET);
        controls.update();
      }
      invalidate();
    },
    resize,
    dispose() {
      disposed = true;
      observer.disconnect();
      canvas.removeEventListener("webglcontextlost", onLost);
      if (frameRequest) cancelAnimationFrame(frameRequest);
      controls?.dispose();
      scene.traverse((object) => {
        const mesh = object as Mesh;
        if (mesh.isMesh) {
          mesh.geometry.dispose();
          const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
          materials.forEach((material) => material.dispose());
        }
      });
      environment.dispose();
      pmrem.dispose();
      renderer.dispose();
    },
  };
}
