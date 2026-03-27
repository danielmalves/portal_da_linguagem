import * as THREE from "../vendor/three.module.js";
import { OrbitControls } from "../vendor/OrbitControls.js";

function createIdSampler(image) {
  const canvas = document.createElement("canvas");
  canvas.width = image.width;
  canvas.height = image.height;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  if (!context) {
    return null;
  }
  context.drawImage(image, 0, 0);
  return { canvas, context };
}

function getRegionColorFromUv(uv, sampler) {
  if (!sampler || !uv) {
    return null;
  }

  const x = Math.min(sampler.canvas.width - 1, Math.max(0, Math.floor(uv.x * sampler.canvas.width)));
  const y = Math.min(
    sampler.canvas.height - 1,
    Math.max(0, Math.floor((1 - uv.y) * sampler.canvas.height))
  );

  const pixel = sampler.context.getImageData(x, y, 1, 1).data;
  if (pixel[3] === 0) {
    return null;
  }

  return { r: pixel[0], g: pixel[1], b: pixel[2] };
}

function colorKey(rgb) {
  return `${rgb.r},${rgb.g},${rgb.b}`;
}

function loadGlobeDataPoints() {
  const script = document.getElementById("globe-data-points");
  if (!script?.textContent) {
    return [];
  }

  try {
    const points = JSON.parse(script.textContent);
    return Array.isArray(points) ? points : [];
  } catch (error) {
    console.warn("Globe data points failed to parse", error);
    return [];
  }
}

function createDataPointElement(point, theme) {
  const wrapper = document.createElement("div");
  wrapper.dataset.dataPoint = "";
  wrapper.dataset.iso3 = point.iso3;
  wrapper.className = theme === "light" ? "pointer-events-none absolute hidden" : "hidden";

  const isDark = theme === "dark";
  const cardClassName = isDark
    ? "rounded-[20px] border border-white/15 bg-slate-950/90 p-4 text-white shadow-2xl backdrop-blur-md"
    : "rounded-[20px] border border-stone-200/80 bg-white/96 p-4 text-stone-900 shadow-2xl backdrop-blur-md";
  const eyebrowClassName = isDark
    ? "text-[0.7rem] font-bold uppercase tracking-[0.12em] text-emerald-200"
    : "text-[0.7rem] font-bold uppercase tracking-[0.12em] text-teal-900";
  const descriptionClassName = isDark ? "mt-3 text-sm leading-6 text-slate-200" : "mt-3 text-sm leading-6 text-stone-600";
  const statClassName = isDark ? "rounded-2xl bg-white/10 px-3 py-2" : "rounded-2xl bg-teal-50 px-3 py-2";
  const sourceStatClassName = isDark ? "rounded-2xl bg-white/10 px-3 py-2" : "rounded-2xl bg-stone-50 px-3 py-2";
  const statLabelClassName = eyebrowClassName;
  const languageRole = point.language_role ? ` (${point.language_role})` : "";
  const sourceMarkup = point.source_url
    ? `<a href="${point.source_url}" class="${isDark ? "underline decoration-white/30 underline-offset-2" : "underline decoration-teal-300 underline-offset-2"}" target="_blank" rel="noreferrer">${point.source_label || "Source"}</a>`
    : point.source_label || "Source pending";

  wrapper.innerHTML = `
    <div data-data-point-card class="${cardClassName}">
      <div class="flex items-start justify-between gap-3">
        <div>
          <p class="${eyebrowClassName}">Atlas point</p>
          <h3 class="mt-1 font-display text-xl font-bold leading-tight">${point.country_name}</h3>
        </div>
      </div>
      <p class="${descriptionClassName}">
        Atlas sample data for ${point.country_name}, positioned over the globe from a country marker coordinate.
      </p>
      <dl class="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div class="${statClassName}">
          <dt class="${statLabelClassName}">Language</dt>
          <dd class="mt-1 font-semibold">${point.language_name || "Pending"}${languageRole}</dd>
        </div>
        <div class="${sourceStatClassName}">
          <dt class="${statLabelClassName}">Source</dt>
          <dd class="mt-1 font-semibold">${sourceMarkup}</dd>
        </div>
      </dl>
    </div>
  `;

  return wrapper;
}

function mountDataPoints(layer, points) {
  if (!layer || !points.length) {
    return [];
  }

  const theme = layer.dataset.pointTheme || "light";
  layer.replaceChildren();

  const emptyState = document.createElement("div");
  emptyState.dataset.emptyState = "";
  emptyState.className = theme === "dark" ? "text-sm leading-6 text-slate-200" : "text-sm leading-6 text-stone-600";
  if (theme === "dark") {
    emptyState.innerHTML = `
      <p class="text-[0.7rem] font-bold uppercase tracking-[0.12em] text-emerald-200">Atlas detail</p>
      <p class="mt-2">Turn on data mode and hover a country to inspect its atlas card here.</p>
    `;
  } else {
    emptyState.innerHTML = `
      <p class="text-[0.7rem] font-bold uppercase tracking-[0.12em] text-teal-900">Atlas detail</p>
      <p class="mt-2">Data mode reveals country-level language notes and atlas references.</p>
    `;
  }
  layer.appendChild(emptyState);

  return points.map((point) => {
    const element = createDataPointElement(point, theme);
    layer.appendChild(element);
    return element;
  });
}

function initGlobe(mount, label, options = {}) {
  if (!mount || !window.WebGLRenderingContext) {
    return null;
  }

  const showStatus = (message) => {
    mount.innerHTML = `
      <div style="
        position:absolute;
        inset:0;
        display:flex;
        align-items:center;
        justify-content:center;
        color:#0f766e;
        font:600 14px/1.4 Manrope, sans-serif;
        text-align:center;
        padding:1rem;
      ">${message}</div>
    `;
  };

    const textureUrl = mount.dataset.textureUrl;
    const idMapUrl = mount.dataset.idmapUrl;
    const regionsUrl = mount.dataset.regionsUrl;
    if (!textureUrl || !idMapUrl) {
      return null;
    }

    const highlightEnabled = options.highlightEnabled !== false;

  try {
    showStatus("Loading globe...");
    if (label) {
      label.textContent = "Hover a country";
    }

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0xf4efe6, 5.5, 9.5);

    const camera = new THREE.PerspectiveCamera(26, 1, 0.1, 100);
    camera.position.set(0, 0.06, options.cameraZ ?? 5.11);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(1, 1, false);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.setClearColor(0x000000, 0);
    renderer.domElement.style.position = "absolute";
    renderer.domElement.style.inset = "0";
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enablePan = false;
    controls.enableZoom = false;
    controls.enableDamping = true;
    controls.dampingFactor = 0.045;
    controls.rotateSpeed = 0.45;
    controls.autoRotate = !reducedMotion;
    controls.autoRotateSpeed = 0.4;
    controls.minPolarAngle = 0.65;
    controls.maxPolarAngle = 2.1;
    controls.target.set(0, 0, 0);
    controls.update();

    const baseSphereScale = options.baseSphereScale ?? 1.0;
    const hoverSphereScale = options.hoverSphereScale ?? 1.51;
    const baseFocusScale = options.baseFocusScale ?? 1.0;
    const hoverFocusScale = options.hoverFocusScale ?? 1.0;
    const baseGroupX = options.baseGroupX ?? 0;
    const hoverGroupX = options.hoverGroupX ?? -0.04;
    const baseGroupY = options.baseGroupY ?? 0;
    const hoverGroupY = options.hoverGroupY ?? 0.01;
    const baseFocusZ = options.baseFocusZ ?? 0.0;
    const hoverFocusZ = options.hoverFocusZ ?? 0.0;

    const group = new THREE.Group();
    group.rotation.z = -0.12;
    group.rotation.x = 0.18;
    scene.add(group);

    const ambient = new THREE.AmbientLight(0xffffff, 1.55);
    scene.add(ambient);

    const keyLight = new THREE.DirectionalLight(0xffffff, 2.8);
    keyLight.position.set(-2.8, 2.1, 3.6);
    scene.add(keyLight);

    const warmFill = new THREE.DirectionalLight(0xf5d7c1, 0.8);
    warmFill.position.set(-1.2, -1.5, 2.2);
    scene.add(warmFill);

    const coolRim = new THREE.DirectionalLight(0x8fe0d8, 1.0);
    coolRim.position.set(3.2, -1.0, -2.6);
    scene.add(coolRim);

    const textureLoader = new THREE.TextureLoader();
    const texture = textureLoader.load(
    textureUrl,
    () => {
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
    },
    undefined,
    (error) => {
      console.error("Globe texture failed to load", error);
    }
  );
    const idTexture = textureLoader.load(
    idMapUrl,
    () => {
      idTexture.colorSpace = THREE.NoColorSpace;
      idTexture.anisotropy = renderer.capabilities.getMaxAnisotropy();
    },
    undefined,
    (error) => {
      console.warn("Globe id map failed to load", error);
    }
  );

    const sphereGeometry = new THREE.SphereGeometry(1, 128, 128);
    const globeMaterial = new THREE.ShaderMaterial({
    uniforms: {
      mapTex: { value: texture },
      idMap: { value: idTexture },
      hoverColor: { value: new THREE.Vector3(-1, -1, -1) },
      hoverActive: { value: 0.0 },
    },
    vertexShader: `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      precision highp float;
      uniform sampler2D mapTex;
      uniform sampler2D idMap;
      uniform vec3 hoverColor;
      uniform float hoverActive;
      varying vec2 vUv;

      void main() {
        vec4 baseColor = texture2D(mapTex, vUv);
        if (baseColor.a < 0.05) {
          discard;
        }

        if (hoverActive > 0.5) {
          vec3 idSample = texture2D(idMap, vUv).rgb;
          vec3 diff = abs(idSample - hoverColor);
          float match = step(max(max(diff.r, diff.g), diff.b), 0.01);
          vec3 contrasted = (baseColor.rgb - 0.5) * 1.22 + 0.5;
          vec3 highlighted = mix(baseColor.rgb * 0.78, contrasted, 0.55);
          baseColor.rgb = mix(baseColor.rgb, highlighted, match);
        }

        gl_FragColor = vec4(baseColor.rgb, baseColor.a);
      }
    `,
    toneMapped: false,
  });

    const sphere = new THREE.Mesh(sphereGeometry, globeMaterial);
    group.add(sphere);

    const atmosphere = new THREE.Mesh(
    new THREE.SphereGeometry(1.03, 128, 128),
    new THREE.MeshBasicMaterial({
      color: 0xd5f1ff,
      transparent: true,
      opacity: 0.1,
      side: THREE.BackSide,
    })
  );
    group.add(atmosphere);

    const glow = new THREE.Mesh(
    new THREE.SphereGeometry(1.08, 128, 128),
    new THREE.MeshBasicMaterial({
      color: 0xbdeee6,
      transparent: true,
      opacity: 0.05,
      side: THREE.BackSide,
    })
  );
    group.add(glow);

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let hovered = false;
    let isDragging = false;
    let zoomingIn = false;
    let lastTime = performance.now();
    let idSampler = null;
    let regionLookup = {};
    let activeKey = "";
    let started = false;
    let frameId = 0;
    const frameSubscribers = new Set();

    const clearHover = () => {
    activeKey = "";
    globeMaterial.uniforms.hoverActive.value = 0.0;
    if (label) {
      label.textContent = "Hover a country";
    }
    options.onHoverChange?.(null);
  };

    const applyHover = (rgb) => {
      if (!highlightEnabled) {
        return;
      }
      const key = colorKey(rgb);
      if (key === activeKey) {
        return;
      }
    activeKey = key;
    globeMaterial.uniforms.hoverColor.value.set(rgb.r / 255, rgb.g / 255, rgb.b / 255);
    globeMaterial.uniforms.hoverActive.value = 1.0;
    if (label) {
      const region = regionLookup[key];
      label.textContent = region ? region.name : "Country";
    }
    options.onHoverChange?.(regionLookup[key] ?? null);
  };

    const resize = () => {
    const width = mount.clientWidth || 1;
    const height = mount.clientHeight || width;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  };

    const updatePointer = (event) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((event.clientY - rect.top) / rect.height) * 2 - 1);
      pointer.set(x, y);

    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObject(sphere, false);
      if (!hits.length || !hits[0].uv) {
        clearHover();
        return;
      }

    const rgb = getRegionColorFromUv(hits[0].uv, idSampler);
      if (!rgb) {
        clearHover();
        return;
      }

    applyHover(rgb);
  };

    const loadRegions = async () => {
    try {
      const response = await fetch(regionsUrl, { cache: "force-cache" });
      if (!response.ok) {
        return;
      }
      regionLookup = await response.json();
    } catch {
      regionLookup = {};
    }
  };

    const loadSampler = () => {
    const image = idTexture.image;
    if (!image || !image.width || !image.height) {
      return false;
    }
    idSampler = createIdSampler(image);
    return Boolean(idSampler);
  };

    const animate = (now) => {
    const delta = Math.min((now - lastTime) / 1000, 0.05);
    lastTime = now;

    controls.autoRotate = !reducedMotion && !isDragging && !hovered;

    group.scale.setScalar(THREE.MathUtils.lerp(group.scale.x, zoomingIn ? hoverSphereScale : baseSphereScale, 0.07));
    group.position.x = THREE.MathUtils.lerp(group.position.x, zoomingIn ? hoverGroupX : baseGroupX, 0.08);
    group.position.y = THREE.MathUtils.lerp(group.position.y, zoomingIn ? hoverGroupY : baseGroupY, 0.08);
    if (!reducedMotion && !hovered && !isDragging) {
      sphere.rotation.y += delta * 0.08;
      atmosphere.rotation.y += delta * 0.06;
      glow.rotation.y += delta * 0.05;
    }

    group.rotation.x = 0.18 + Math.sin(now * 0.00025) * 0.015;
    group.rotation.z = -0.12 + Math.cos(now * 0.00033) * 0.012;

    controls.update();
    renderer.render(scene, camera);
    for (const subscriber of frameSubscribers) {
      subscriber();
    }
      frameId = requestAnimationFrame(animate);
    };

    const onPointerDown = () => {
      isDragging = true;
    };

    const onPointerUp = () => {
      isDragging = false;
    };

    const onMouseEnter = () => {
      hovered = true;
      zoomingIn = true;
    };

    const onMouseLeave = () => {
      hovered = false;
      zoomingIn = false;
      clearHover();
    };

    const onPointerEnter = () => {
      zoomingIn = true;
    };

    const onPointerLeave = () => {
      zoomingIn = false;
    };

    mount.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointerup", onPointerUp);
    renderer.domElement.addEventListener("pointermove", updatePointer);
    renderer.domElement.addEventListener("pointerleave", clearHover);
    mount.addEventListener("mouseenter", onMouseEnter);
    mount.addEventListener("mouseleave", onMouseLeave);
    renderer.domElement.addEventListener("pointerenter", onPointerEnter);
    renderer.domElement.addEventListener("pointerleave", onPointerLeave);
    window.addEventListener("resize", resize, { passive: true });

    const startAnimation = () => {
      if (started) {
        return;
      }
      started = true;
      mount.innerHTML = "";
      mount.appendChild(renderer.domElement);
      resize();
      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };

    loadRegions();
    startAnimation();

    const waitForSampler = () => {
      if (loadSampler()) {
        return;
      }
      requestAnimationFrame(waitForSampler);
    };

    waitForSampler();

    return {
      projectLatLng(lat, lng, radius = 1.02) {
        const latRad = THREE.MathUtils.degToRad(lat);
        const lngRad = THREE.MathUtils.degToRad(lng);
        const point = new THREE.Vector3(
          Math.cos(latRad) * Math.sin(lngRad),
          Math.sin(latRad),
          Math.cos(latRad) * Math.cos(lngRad)
        ).multiplyScalar(radius);
        const worldPoint = sphere.localToWorld(point.clone());
        const worldCenter = sphere.getWorldPosition(new THREE.Vector3());
        const surfaceNormal = worldPoint.clone().sub(worldCenter).normalize();
        const towardCamera = camera.position.clone().sub(worldPoint).normalize();
        const projected = worldPoint.clone().project(camera);
        const width = mount.clientWidth || 1;
        const height = mount.clientHeight || 1;

        return {
          x: (projected.x * 0.5 + 0.5) * width,
          y: (-projected.y * 0.5 + 0.5) * height,
          visible:
            projected.z > -1 &&
            projected.z < 1 &&
            surfaceNormal.dot(towardCamera) > 0.12,
        };
      },
      subscribeFrame(callback) {
        frameSubscribers.add(callback);
        return () => {
          frameSubscribers.delete(callback);
        };
      },
      resize,
      dispose() {
        frameSubscribers.clear();
        cancelAnimationFrame(frameId);
        mount.removeEventListener("pointerdown", onPointerDown);
        window.removeEventListener("pointerup", onPointerUp);
        renderer.domElement.removeEventListener("pointermove", updatePointer);
        renderer.domElement.removeEventListener("pointerleave", clearHover);
        mount.removeEventListener("mouseenter", onMouseEnter);
        mount.removeEventListener("mouseleave", onMouseLeave);
        renderer.domElement.removeEventListener("pointerenter", onPointerEnter);
        renderer.domElement.removeEventListener("pointerleave", onPointerLeave);
        window.removeEventListener("resize", resize);
        renderer.dispose();
        mount.innerHTML = "";
      },
    };
  } catch (error) {
    console.error("Globe failed to initialize", error);
    showStatus("Globe failed to load. Check the browser console.");
    return null;
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const mainMount = document.querySelector("[data-globe-stage]");
  const mainLabel = document.querySelector("[data-globe-label]");
  const atlasDefault = document.querySelector("[data-atlas-default]");
  const globalPerspectiveCard = document.querySelector("[data-global-perspective]");
  const wikiPanel = document.querySelector("[data-wiki-panel]");
  const wikiPointer = document.querySelector("[data-wiki-pointer]");
  const wikiTitle = document.querySelector("[data-wiki-title]");
  const wikiDescription = document.querySelector("[data-wiki-description]");
  const wikiSummary = document.querySelector("[data-wiki-summary]");
  const wikiLink = document.querySelector("[data-wiki-link]");
  const dataModeToggles = Array.from(document.querySelectorAll("[data-data-mode-toggle]"));
  const dataInfoPanels = Array.from(document.querySelectorAll("[data-data-info-panel]"));
  const mainInfoPanel = dataInfoPanels.find((panel) => panel.dataset.pointTheme === "light");
  const mainInfoPointer = mainInfoPanel?.querySelector("[data-data-info-pointer]");
  const dataModeIndicator = document.querySelector("[data-data-mode-indicator]");
  const modal = document.querySelector("[data-globe-modal]");
  const modalMount = document.querySelector("[data-globe-stage-expanded]");
  const openButton = document.querySelector("[data-globe-open]");
  const closeButton = document.querySelector("[data-globe-close]");
  const dataPointsData = loadGlobeDataPoints();
  const dataPointsByIso3 = new Map(dataPointsData.map((point) => [point.iso3, point]));

  let dataModeActive = false;
  let modalGlobe = null;
  let mainDataPoints = [];
  let modalDataPoints = [];
  let activeRegionId = "";
  let stopMainPanelTracking = null;

  const handleHoverChange = (region) => {
    activeRegionId = region?.type === "country" ? region.id : "";
    syncHoveredPointCards();
    syncWikiPanel();
  };

  const mainGlobe = initGlobe(mainMount, mainLabel, {
    onHoverChange: handleHoverChange,
  });

  const setDataPointOpen = (point, isOpen) => {
    point.classList.toggle("hidden", !isOpen);
  };

  const getDataPoints = () => [...mainDataPoints, ...modalDataPoints];

  const closeAllDataPoints = () => {
    for (const point of getDataPoints()) {
      setDataPointOpen(point, false);
    }
  };

  const syncHoveredPointCards = () => {
    for (const panel of dataInfoPanels) {
      const emptyState = panel.querySelector("[data-empty-state]");
      const isMainPanel = panel.dataset.pointTheme === "light";
      emptyState?.classList.toggle("hidden", dataModeActive || (!isMainPanel && Boolean(activeRegionId)));
    }
    for (const point of getDataPoints()) {
      const shouldShow = dataModeActive && Boolean(activeRegionId) && point.dataset.iso3 === activeRegionId;
      setDataPointOpen(point, shouldShow);
    }
  };

  const syncMainInfoPanelMode = () => {
    if (!mainInfoPanel) {
      return;
    }

    const activePoint = dataPointsByIso3.get(activeRegionId);
    const showAsBalloon = dataModeActive && Boolean(activePoint) && Boolean(mainGlobe);

    atlasDefault?.classList.toggle("hidden", dataModeActive);
    mainInfoPanel.classList.toggle("hidden", !showAsBalloon);
    globalPerspectiveCard?.classList.toggle("hidden", !dataModeActive);

    if (!showAsBalloon) {
      mainInfoPanel.style.position = "";
      mainInfoPanel.style.left = "";
      mainInfoPanel.style.top = "";
      mainInfoPanel.style.width = "";
      mainInfoPanel.style.height = "";
      mainInfoPanel.style.zIndex = "";
      mainInfoPointer?.classList.add("hidden");
      return;
    }

    const projection = mainGlobe?.projectLatLng?.(activePoint.lat, activePoint.lng);
    const aside = mainInfoPanel.closest("aside");
    if (!projection || !projection.visible || !aside) {
      mainInfoPanel.classList.add("hidden");
      globalPerspectiveCard?.classList.remove("hidden");
      return;
    }

    const asideRect = aside.getBoundingClientRect();
    const mountRect = mainMount.getBoundingClientRect();
    const panelWidth = 320;
    const targetLeft = mountRect.left - asideRect.left + projection.x + 28;
    const targetTop = mountRect.top - asideRect.top + projection.y - 84;
    const clampedLeft = Math.max(24, Math.min(targetLeft, asideRect.width - panelWidth - 24));
    const clampedTop = Math.max(84, Math.min(targetTop, asideRect.height - 180));

    mainInfoPanel.style.position = "absolute";
    mainInfoPanel.style.left = `${clampedLeft}px`;
    mainInfoPanel.style.top = `${clampedTop}px`;
    mainInfoPanel.style.width = `${panelWidth}px`;
    mainInfoPanel.style.height = "auto";
    mainInfoPanel.style.zIndex = "40";
    mainInfoPointer?.classList.remove("hidden");
  };

  const syncWikiPanel = () => {
    if (!wikiPanel || !wikiTitle || !wikiSummary || !wikiLink || !wikiDescription) {
      return;
    }

    const point = dataPointsByIso3.get(activeRegionId);
    wikiPanel.style.position = "";
    wikiPanel.style.right = "";
    wikiPanel.style.top = "";
    wikiPanel.style.width = "";
    wikiPanel.style.zIndex = "";
    wikiPanel.style.boxShadow = "";
    wikiPointer?.classList.add("hidden");

    if (!point || !point.wiki_summary) {
      wikiTitle.textContent = "Location note";
      wikiDescription.textContent = "";
      wikiSummary.textContent = "Hover a country to read a short reference summary here.";
      wikiLink.classList.add("hidden");
      wikiLink.href = "#";
      return;
    }

    wikiTitle.textContent = point.wiki_title || point.country_name;
    wikiDescription.textContent = point.wiki_description || "";
    wikiSummary.textContent = point.wiki_summary;

    if (point.wiki_url) {
      wikiLink.classList.remove("hidden");
      wikiLink.href = point.wiki_url;
      wikiLink.textContent = `Source: ${point.wiki_source || "Wikipedia"}`;
    } else {
      wikiLink.classList.add("hidden");
      wikiLink.href = "#";
    }
  };

  const syncDataModeUi = () => {
    for (const toggle of dataModeToggles) {
      toggle.setAttribute("aria-pressed", String(dataModeActive));
      toggle.setAttribute("aria-label", dataModeActive ? "Disable data mode" : "Enable data mode");
      toggle.classList.toggle("ring-teal-500/30", dataModeActive);
      toggle.classList.toggle("bg-teal-50", dataModeActive);
      toggle.classList.toggle("text-teal-950", dataModeActive);
    }

    syncHoveredPointCards();
    syncMainInfoPanelMode();

    if (dataModeIndicator) {
      dataModeIndicator.classList.toggle("hidden", !dataModeActive);
      dataModeIndicator.classList.toggle("flex", dataModeActive);
    }

  };

  const buildInfoCards = (panel) => mountDataPoints(panel, dataPointsData);

  if (mainGlobe) {
    const mainPanel = dataInfoPanels.find((panel) => panel.dataset.pointTheme === "light");
    mainDataPoints = buildInfoCards(mainPanel);
    stopMainPanelTracking = mainGlobe.subscribeFrame(() => {
      syncMainInfoPanelMode();
    });
  }

  syncDataModeUi();
  syncWikiPanel();

  for (const toggle of dataModeToggles) {
    toggle.addEventListener("click", () => {
      dataModeActive = !dataModeActive;
      syncDataModeUi();
    });
  }

  if (openButton && modal && modalMount) {
    openButton.addEventListener("click", () => {
      modal.classList.remove("hidden");
      modal.classList.add("flex");
      if (!modalGlobe) {
        modalGlobe = initGlobe(modalMount, null, {
          cameraZ: 3.0,
          hoverSphereScale: 1.05,
          hoverFocusScale: 1.0,
          hoverGroupX: -0.02,
          hoverGroupY: 0.012,
          autoRotateSpeed: 0.25,
          onHoverChange: handleHoverChange,
        });
        const modalPanel = dataInfoPanels.find((panel) => panel.dataset.pointTheme === "dark");
        modalDataPoints = buildInfoCards(modalPanel);
        syncDataModeUi();
      }
      modalGlobe?.resize?.();
      modalMount?.focus?.();
    });
  }

  const closeModal = () => {
    if (!modal) {
      return;
    }
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    modalGlobe?.dispose?.();
    modalGlobe = null;
    modalDataPoints = [];
    activeRegionId = "";
    const modalPanel = dataInfoPanels.find((panel) => panel.dataset.pointTheme === "dark");
    modalDataPoints = buildInfoCards(modalPanel);
    syncHoveredPointCards();
    syncWikiPanel();
  };

  closeButton?.addEventListener("click", closeModal);
  modal?.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeModal();
    }
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeModal();
    }
  });
  if (mainGlobe) {
    window.addEventListener(
      "resize",
      () => {
        mainGlobe.resize();
        syncMainInfoPanelMode();
        syncWikiPanel();
      },
      { passive: true }
    );
  }
});







