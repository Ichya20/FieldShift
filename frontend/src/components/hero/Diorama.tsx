import { RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { DioramaHandle } from "../../diorama/scene";
import { useInView, useReducedMotion } from "../../lib/hooks";
import type { CropId } from "../../lib/types";

function detectLowPower() {
  const nav = navigator as Navigator & { deviceMemory?: number };
  const cores = nav.hardwareConcurrency ?? 8;
  const memory = nav.deviceMemory ?? 8;
  const smallTouch = window.matchMedia("(pointer: coarse)").matches && window.innerWidth < 720;
  return cores <= 4 || memory <= 4 || smallTouch;
}

function webglAvailable() {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

interface Props {
  crop: CropId;
  token: string;
  label: string;
}

export function Diorama({ crop, token, label }: Props) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const handle = useRef<DioramaHandle | null>(null);
  const { ref: stage, inView } = useInView<HTMLDivElement>("120px");
  const reducedMotion = useReducedMotion();
  const [state, setState] = useState<"loading" | "ready" | "unavailable">(() => (webglAvailable() ? "loading" : "unavailable"));
  const [moved, setMoved] = useState(false);
  const [interactive] = useState(() => window.matchMedia("(pointer: fine)").matches);
  const latest = useRef({ crop, token });
  latest.current = { crop, token };

  useEffect(() => {
    if (state === "unavailable" || !canvas.current) return;
    let disposed = false;
    import("../../diorama/scene")
      .then(({ createDiorama }) => {
        if (disposed || !canvas.current) return;
        try {
          handle.current = createDiorama(canvas.current, {
            reducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
            lowPower: detectLowPower(),
            interactive,
            onContextLost: () => setState("unavailable"),
          });
          handle.current.show(latest.current.crop, latest.current.token);
          setState("ready");
        } catch {
          setState("unavailable");
        }
      })
      .catch(() => setState("unavailable"));
    return () => {
      disposed = true;
      handle.current?.dispose();
      handle.current = null;
    };
    // The scene is created once; later prop changes go through the handle.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    handle.current?.show(crop, token);
  }, [crop, token, state]);

  useEffect(() => {
    handle.current?.setReducedMotion(reducedMotion);
  }, [reducedMotion, state]);

  useEffect(() => {
    const update = () => handle.current?.setActive(inView && document.visibilityState === "visible");
    update();
    document.addEventListener("visibilitychange", update);
    return () => document.removeEventListener("visibilitychange", update);
  }, [inView, state]);

  if (state === "unavailable") {
    return (
      <div className="stage stage--fallback" ref={stage}>
        <p>Tampilan 3D tidak dapat dimuat pada perangkat ini. Kalender di bawah tetap menunjukkan skenario yang sama.</p>
      </div>
    );
  }

  return (
    <div
      className="stage"
      ref={stage}
      tabIndex={0}
      role="img"
      aria-label={`${label}. ${interactive ? "Seret atau gunakan panah kiri dan kanan untuk memutar tampilan." : ""}`}
      aria-busy={state === "loading"}
      onKeyDown={(event) => {
        if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
          event.preventDefault();
          handle.current?.rotateBy(event.key === "ArrowLeft" ? -8 : 8);
          setMoved(true);
        }
      }}
      onPointerDown={() => interactive && setMoved(true)}
    >
      <canvas ref={canvas} className="stage__canvas" />
      {moved && (
        <button
          type="button"
          className="stage__reset"
          onClick={() => {
            handle.current?.resetView();
            setMoved(false);
          }}
        >
          <RotateCcw aria-hidden="true" size={15} />
          Sudut awal
        </button>
      )}
    </div>
  );
}
