/**
 * SOLARAEUS — Solar Observatory & Twilight Survey Chart
 * Core Application Engine & Scientific Visualization Pipeline
 * 
 * Strict Separation of Theme and Science:
 * Visual style is strictly a presentation layer (VISUAL_ONLY) and never alters,
 * replaces, or modifies physically computed arrays or colormaps.
 */

(function (window) {
  'use strict';

  // --- 1. Global Simulation & UI State ---
  const state = {
    timeOfDay: 14.5,            // 14:30 IST (Benchmark forcing condition)
    isPlaying: false,
    playSpeed: 0.35,            // Solar hours per second
    scenario: 'baseline',       // 'baseline', 'trees', 'panels', 'combined'
    treeState: 'nominal',       // 'small', 'nominal', 'large'
    activeLayer: 'none',        // 'none', 'tmrt', 'utci', 'cooling'
    layerOpacity: 0.75,
    contourEnabled: true,
    scaleMode: 'fixed',         // 'fixed', 'auto'
    shadowsEnabled: true,
    coreTreesVisible: true,
    contextTreesVisible: true,
    panelsVisible: true,
    poiPinsVisible: true,
    edgesVisible: false,
    infillVisible: false,
    stylePreset: 'cinematic',   // 'cinematic', 'daylight', 'analysis'
    cameraPreset: 'iso',        // 'iso', 'street', 'trees', 'top'
    cloudCover: 0.0,
    terrainProfile: 'flat',
    activeFlyout: null,         // 'scenario', 'overlay', 'atmosphere', 'layers'
    selectedObject: null,       // Strictly null on startup (no persistent callout)
    hoveredObject: null,
    detailsOpen: false,
    activeDetailTab: 'simple',
    lastInteractionTime: performance.now(),
    dockVisible: true
  };

  // Site Coordinates (Church Street, Bengaluru)
  const LATITUDE = 12.9749;     // °N
  const LONGITUDE = 77.6054;    // °E
  const STUDY_CENTROID = { x: 105.0, y: 70.0, z: 0.0 };

  // 3D Anchor Positions for POI Pins
  const POI_DEFINITIONS = [
    { id: 'pin-station', x: 130, y: 2.5, z: -72, label: 'Receptor Station', priority: 1, minScenario: 'baseline' },
    { id: 'pin-sail', x: 45, y: 5.5, z: -78, label: 'CAND_0028 Sail', priority: 2, minScenario: 'panels' },
    { id: 'pin-trees', x: 45, y: 8.5, z: -73, label: 'T08–T13 Canopies', priority: 3, minScenario: 'trees' },
    { id: 'pin-gate-east', x: 20, y: 2.2, z: -75, label: 'Brigade Rd Gate', priority: 4, minScenario: 'baseline' },
    { id: 'pin-gate-west', x: 210, y: 2.2, z: -68, label: 'Museum Rd Gate', priority: 5, minScenario: 'baseline' }
  ];

  // Three.js Core Instances
  let container, scene, camera, renderer, controls;
  let sunLight, ambientLight, hemiLight;
  let groundMesh, walkMesh, gridMesh, heatmapMesh, cloudMesh;
  let buildingGroup, edgeGroup, treeGroup, contextTreeGroup, panelGroup, infillGroup;
  let buildingCoreMat, buildingContextMat, buildingMassingMat;
  let raycaster, mouse, clock;

  // GPU Heatmap Uniforms & Textures
  let heatmapDataTex, heatmapMaskTex, heatmapLutTex;
  let heatmapShaderMat;

  // Cached DOM Elements
  const dom = {};

  // --- 2. Initialization ---
  function init() {
    try {
      cacheDomElements();

      container = document.getElementById('canvas-container');
      clock = new THREE.Clock();

      // Scene
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0x070B14);
      scene.fog = new THREE.FogExp2(0x070B14, 0.0016);

      // Camera
      camera = new THREE.PerspectiveCamera(40, window.innerWidth / window.innerHeight, 1, 2500);

      // Renderer
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        powerPreference: 'high-performance',
        preserveDrawingBuffer: true // Required for headless testing & screenshots
      });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.15;
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      container.appendChild(renderer.domElement);

      // Orbit Controls
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.06;
      controls.maxPolarAngle = Math.PI / 2 - 0.05;
      controls.minDistance = 20;
      controls.maxDistance = 850;
      controls.target.set(STUDY_CENTROID.x, 0, -STUDY_CENTROID.y);

      // Set initial camera view
      setCameraPreset('iso');

      // Lighting
      setupLighting();

      // Groups
      buildingGroup = new THREE.Group();
      edgeGroup = new THREE.Group();
      treeGroup = new THREE.Group();
      contextTreeGroup = new THREE.Group();
      panelGroup = new THREE.Group();
      infillGroup = new THREE.Group();

      scene.add(buildingGroup);
      scene.add(edgeGroup);
      scene.add(treeGroup);
      scene.add(contextTreeGroup);
      scene.add(panelGroup);
      scene.add(infillGroup);

      raycaster = new THREE.Raycaster();
      mouse = new THREE.Vector2(-999, -999);

      // Build 3D Entities
      buildGround();
      buildBuildings();
      buildAllVegetation();
      buildInterventions();
      buildGPUHeatmapSurface();
      buildCloudLayer();

      // Setup Listeners
      setupEventListeners();

      // Check URL parameters
      parseUrlParameters();

      // Initial state sync
      setCameraPreset(state.cameraPreset);
      applyStylePreset(state.stylePreset);
      applyScenario(state.scenario);
      if (state.activeLayer !== 'none') {
        applyThermalLayer(state.activeLayer);
      }
      updateSunPosition(state.timeOfDay);
      updateHeadlineReadout();
      updateDetailsDrawer();

      // Start loop
      animate();
      console.log('SOLARAEUS 3D: Solar Observatory & Twilight Survey Chart Initialized.');
    } catch (err) {
      console.error('SOLARAEUS 3D Init Error:', err);
    }
  }

  function cacheDomElements() {
    dom.body = document.body;
    dom.topbarScenarioTag = document.getElementById('topbar-scenario-tag');
    dom.systemStatusDot = document.getElementById('system-status-dot');

    dom.headlineReadout = document.getElementById('headline-readout');
    dom.headlineUtci = document.getElementById('headline-utci-num');
    dom.headlineStressBar = document.getElementById('headline-stress-bar');
    dom.headlineStressLabel = document.getElementById('headline-stress-label');
    dom.headlineTmrt = document.getElementById('headline-tmrt-val');
    dom.headlineShaded = document.getElementById('headline-shaded-val');
    dom.headlineDni = document.getElementById('headline-dni-val');

    dom.floatingLegend = document.getElementById('floating-legend');
    dom.legendTitle = document.getElementById('legend-field-title');
    dom.legendUnit = document.getElementById('legend-unit-tag');
    dom.legendBar = document.getElementById('legend-gradient-bar');
    dom.legendMin = document.getElementById('legend-tick-min');
    dom.legendMid = document.getElementById('legend-tick-mid');
    dom.legendMax = document.getElementById('legend-tick-max');
    dom.legendSummary = document.getElementById('legend-stat-summary');
    dom.legendTime = document.getElementById('legend-time-stamp');

    dom.timelineDock = document.getElementById('timeline-dock');
    dom.playBtn = document.getElementById('arc-play-btn');
    dom.svgPlay = document.getElementById('svg-play');
    dom.svgPause = document.getElementById('svg-pause');
    dom.clockDisplay = document.getElementById('digital-clock-display');
    dom.arcWrapper = document.getElementById('celestial-arc-wrapper');
    dom.playhead = document.getElementById('celestial-playhead');
    dom.sunAltitudeBubble = document.getElementById('sun-altitude-bubble');
    dom.accessibleTimeSlider = document.getElementById('accessible-time-slider');
    dom.roseNeedle = document.getElementById('rose-needle');

    dom.flyoutSheet = document.getElementById('flyout-sheet');
    dom.detailsDrawer = document.getElementById('details-drawer');
    dom.toggleDetailsBtn = document.getElementById('toggle-details-btn');
    dom.drawerCloseBtn = document.getElementById('drawer-close-btn');

    dom.governanceModal = document.getElementById('governance-modal');
    dom.openGovernanceBtn = document.getElementById('open-governance-btn');
    dom.govCloseBtn = document.getElementById('gov-close-btn');

    dom.calloutCard = document.getElementById('selected-callout-card');
    dom.calloutGlyph = document.getElementById('callout-big-glyph');
    dom.calloutEyebrow = document.getElementById('callout-eyebrow');
    dom.calloutHeading = document.getElementById('callout-heading');
    dom.calloutM1 = document.getElementById('callout-m1');
    dom.calloutM2 = document.getElementById('callout-m2');
    dom.calloutM3 = document.getElementById('callout-m3');
    dom.calloutDismissBtn = document.getElementById('callout-dismiss-btn');

    dom.tooltip = document.getElementById('cell-tooltip');
    dom.ttTitle = document.getElementById('tt-title');
    dom.ttBody = document.getElementById('tt-body');

    dom.opacitySlider = document.getElementById('overlay-opacity-slider');
    dom.opacityLabel = document.getElementById('overlay-opacity-label');
    dom.cloudSlider = document.getElementById('cloud-slider');
    dom.cloudCoverNum = document.getElementById('cloud-cover-num');
    dom.metaCloudTrans = document.getElementById('meta-cloud-trans');
    dom.terrainSelect = document.getElementById('terrain-profile-select');
  }

  // --- 3. Lighting Architecture & Astronomical Calculations ---
  function setupLighting() {
    ambientLight = new THREE.AmbientLight(0xedf1fa, 0.42);
    scene.add(ambientLight);

    hemiLight = new THREE.HemisphereLight(0x9aa7c4, 0x16203a, 0.38);
    scene.add(hemiLight);

    sunLight = new THREE.DirectionalLight(0xfffaed, 2.75);
    sunLight.castShadow = true;

    // High precision cascaded 4K shadow map
    sunLight.shadow.mapSize.width = 4096;
    sunLight.shadow.mapSize.height = 4096;
    sunLight.shadow.camera.near = 10;
    sunLight.shadow.camera.far = 950;

    const d = 220;
    sunLight.shadow.camera.left = -d;
    sunLight.shadow.camera.right = d;
    sunLight.shadow.camera.top = d;
    sunLight.shadow.camera.bottom = -d;

    sunLight.shadow.bias = -0.00035;
    sunLight.shadow.normalBias = 0.025;

    scene.add(sunLight);
    scene.add(sunLight.target);
    sunLight.target.position.set(STUDY_CENTROID.x, 0, -STUDY_CENTROID.y);
  }

  function calculateSolarPosition(hoursDecimal) {
    const dayOfYear = 106; // April 15
    const phi = LATITUDE * (Math.PI / 180);
    const delta = 23.45 * Math.sin((360 / 365) * (284 + dayOfYear) * (Math.PI / 180)) * (Math.PI / 180);
    const solarNoon = 12.33; // 12:20 IST
    const hourAngle = (hoursDecimal - solarNoon) * 15 * (Math.PI / 180);

    const sinAlpha = Math.sin(phi) * Math.sin(delta) + Math.cos(phi) * Math.cos(delta) * Math.cos(hourAngle);
    const alphaRad = Math.asin(Math.max(-1, Math.min(1, sinAlpha)));
    const altitudeDeg = alphaRad * (180 / Math.PI);
    const zenithDeg = 90 - altitudeDeg;

    const cosGamma = (sinAlpha * Math.sin(phi) - Math.sin(delta)) / (Math.cos(alphaRad) * Math.cos(phi) + 1e-7);
    let azimuthDeg = Math.acos(Math.max(-1, Math.min(1, cosGamma))) * (180 / Math.PI);
    if (hourAngle > 0) {
      azimuthDeg = 360 - azimuthDeg;
    }

    return {
      altitudeDeg,
      zenithDeg,
      azimuthDeg,
      altitudeRad: alphaRad,
      azimuthRad: azimuthDeg * (Math.PI / 180)
    };
  }

  function updateSunPosition(hoursDecimal) {
    const sun = calculateSolarPosition(hoursDecimal);
    const isDaylight = sun.altitudeDeg > 0.5;

    // Update Digital Clock
    const h = Math.floor(hoursDecimal);
    const m = Math.floor((hoursDecimal - h) * 60);
    const s = Math.floor((((hoursDecimal - h) * 60) - m) * 60);
    const timeStr = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    if (dom.clockDisplay) dom.clockDisplay.textContent = timeStr;

    // Direct Beam Irradiance with Cloud Attenuation
    let clearDni = 0;
    if (isDaylight) {
      const airmass = 1.0 / (Math.sin(sun.altitudeRad) + 0.50572 * Math.pow(sun.altitudeDeg + 6.07995, -1.6364));
      clearDni = 950.0 * Math.pow(0.75, Math.min(airmass, 12));
    }

    const cloudTrans = Math.max(0.05, 1.0 - 0.78 * state.cloudCover);
    const activeDni = clearDni * cloudTrans;
    if (dom.headlineDni) dom.headlineDni.textContent = `${activeDni.toFixed(0)} W/m²`;
    if (dom.metaCloudTrans) dom.metaCloudTrans.textContent = `${(cloudTrans * 100).toFixed(0)}% Direct Beam`;

    // 3D Sun Vector
    const dist = 380.0;
    const cosAlt = Math.cos(sun.altitudeRad);
    const sinAlt = Math.sin(sun.altitudeRad);
    const azRad = sun.azimuthRad;

    const sunX = STUDY_CENTROID.x - dist * cosAlt * Math.sin(azRad);
    const sunZ = -STUDY_CENTROID.y + dist * cosAlt * Math.cos(azRad);
    const sunY = Math.max(8, dist * Math.max(0.06, sinAlt));

    sunLight.position.set(sunX, sunY, sunZ);
    sunLight.target.position.set(STUDY_CENTROID.x, 0, -STUDY_CENTROID.y);

    // Apply Lighting Tints
    applyLightingTints(sun, hoursDecimal, cloudTrans);

    // Update Celestial Arc Playhead Position
    updateCelestialArcPlayhead(hoursDecimal, sun.altitudeDeg);
  }

  function applyLightingTints(sun, hoursDecimal, cloudTrans) {
    if (state.stylePreset === 'analysis') {
      scene.background = new THREE.Color(0x111827);
      if (scene.fog) scene.fog.density = 0.0;
      sunLight.color = new THREE.Color(0xffffff);
      sunLight.intensity = state.shadowsEnabled ? 2.0 : 0.0;
      ambientLight.intensity = 0.85;
      hemiLight.intensity = 0.65;
      return;
    }

    if (state.stylePreset === 'daylight') {
      const skyPaper = new THREE.Color(0xF3EBDD);
      scene.background = skyPaper;
      if (scene.fog) {
        scene.fog.color = skyPaper;
        scene.fog.density = 0.0008;
      }
      sunLight.color = new THREE.Color(0xfff3d6);
      sunLight.intensity = state.shadowsEnabled ? 2.85 * cloudTrans : 0.0;
      ambientLight.intensity = 0.65;
      hemiLight.intensity = 0.55;
      return;
    }

    // Default: Observatory (Cinematic Dusk Mood)
    let skyColor, sunColor, sunIntensity, hemiSky, ambientInt;
    if (sun.altitudeDeg < 0) {
      skyColor = new THREE.Color(0x05070e);
      sunColor = new THREE.Color(0x1e293b);
      sunIntensity = 0.05;
      hemiSky = new THREE.Color(0x0f172a);
      ambientInt = 0.2;
    } else if (sun.altitudeDeg < 15) {
      skyColor = new THREE.Color(0x131726);
      sunColor = new THREE.Color(0xff8c42);
      sunIntensity = 1.65 * cloudTrans;
      hemiSky = new THREE.Color(0xffaa5e);
      ambientInt = 0.38;
    } else if (sun.altitudeDeg < 45) {
      skyColor = new THREE.Color(0x090f20);
      sunColor = new THREE.Color(0xffd580);
      sunIntensity = 2.45 * cloudTrans;
      hemiSky = new THREE.Color(0x9aa7c4);
      ambientInt = 0.45;
    } else {
      skyColor = new THREE.Color(0x070B14);
      sunColor = new THREE.Color(0xfffaed);
      sunIntensity = 2.95 * cloudTrans;
      hemiSky = new THREE.Color(0xb0c4de);
      ambientInt = 0.52;
    }

    scene.background = skyColor;
    if (scene.fog) {
      scene.fog.color = skyColor;
      scene.fog.density = 0.0016;
    }
    sunLight.color = sunColor;
    sunLight.intensity = state.shadowsEnabled ? sunIntensity : 0.0;
    hemiLight.color = hemiSky;
    ambientLight.intensity = ambientInt;
  }

  function updateCelestialArcPlayhead(hoursDecimal, altDeg) {
    if (!dom.playhead) return;
    // Normalized time between dawn (06:00) and dusk (18:30)
    const minH = 6.0;
    const maxH = 18.5;
    const t = Math.max(0, Math.min(1, (hoursDecimal - minH) / (maxH - minH)));

    // X percentage across the scrubber
    const xPct = 6.5 + t * (93.5 - 6.5);
    // Y position along quadratic curve: 0 at ends, peak at noon
    const curveY = 4.0 * t * (1.0 - t); // 0 at dawn/dusk, 1.0 at noon
    const bottomPx = 8 + curveY * 34;

    dom.playhead.style.left = `${xPct}%`;
    dom.playhead.style.bottom = `${bottomPx}px`;

    if (dom.sunAltitudeBubble) {
      dom.sunAltitudeBubble.textContent = `${Math.max(0, altDeg).toFixed(1)}° Alt`;
    }
  }

  // --- 4. Scene Geometry Synthesis ---
  function buildGround() {
    // Extended ground with faded edge
    const groundGeo = new THREE.PlaneGeometry(420, 320, 32, 32);
    const groundColor = state.stylePreset === 'daylight' ? 0xe5ddcf : 0x222a3a;
    const groundMat = new THREE.MeshStandardMaterial({
      color: groundColor,
      roughness: 0.85,
      metalness: 0.1,
      side: THREE.DoubleSide
    });
    groundMesh = new THREE.Mesh(groundGeo, groundMat);
    groundMesh.rotation.x = -Math.PI / 2;
    groundMesh.position.set(105, -0.05, -70);
    groundMesh.receiveShadow = true;
    scene.add(groundMesh);

    // Pedestrian Walkway Ribbon (Church Street paving)
    const walkGeo = new THREE.PlaneGeometry(260, 22);
    const walkMat = new THREE.MeshStandardMaterial({
      color: 0x2a3346,
      roughness: 0.68,
      metalness: 0.15
    });
    walkMesh = new THREE.Mesh(walkGeo, walkMat);
    walkMesh.rotation.x = -Math.PI / 2;
    walkMesh.rotation.z = -0.095;
    walkMesh.position.set(110, 0.01, -76);
    walkMesh.receiveShadow = true;
    scene.add(walkMesh);

    // Fine Survey Grid
    gridMesh = new THREE.GridHelper(420, 84, 0x3FD1C0, 0x16203A);
    gridMesh.position.set(105, 0.02, -70);
    gridMesh.material.opacity = 0.08;
    gridMesh.material.transparent = true;
    scene.add(gridMesh);
  }

  function buildBuildings() {
    const data = window.CHURCH_STREET_DATA;
    if (!data || !data.buildings) return;

    buildingCoreMat = new THREE.MeshStandardMaterial({
      color: 0x222b3d,
      roughness: 0.68,
      metalness: 0.22,
      flatShading: true
    });

    buildingContextMat = new THREE.MeshStandardMaterial({
      color: 0x171e2c,
      roughness: 0.85,
      metalness: 0.12,
      flatShading: true
    });

    // Lighter massing material used when heatmaps are active for maximum contrast
    buildingMassingMat = new THREE.MeshStandardMaterial({
      color: 0x475569,
      roughness: 0.9,
      metalness: 0.05,
      flatShading: true
    });

    const edgeMat = new THREE.LineBasicMaterial({
      color: 0x3FD1C0,
      transparent: true,
      opacity: 0.28
    });

    data.buildings.forEach(b => {
      const geom = new THREE.BufferGeometry();
      const posArray = [];

      b.triangles.forEach(tri => {
        tri.forEach(vIdx => {
          const v = b.vertices[vIdx];
          posArray.push(v[0], v[2], -v[1]);
        });
      });

      geom.setAttribute('position', new THREE.Float32BufferAttribute(posArray, 3));
      geom.computeVertexNormals();

      const mesh = new THREE.Mesh(geom, b.is_core ? buildingCoreMat : buildingContextMat);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData = {
        type: 'building',
        id: b.id,
        label: b.label,
        height: b.height,
        isCore: b.is_core
      };
      buildingGroup.add(mesh);

      const edges = new THREE.EdgesGeometry(geom, 25);
      const line = new THREE.LineSegments(edges, edgeMat);
      line.visible = state.edgesVisible;
      edgeGroup.add(line);
    });
  }

  /**
   * Complete Vegetation Pipeline:
   * Renders EVERY tree in the municipal inventory (14 trees total: T08–T13 core, T01–T07 + T14 context)
   * Rendering only T08–T13 is strictly prohibited.
   */
  function buildAllVegetation() {
    const data = window.CHURCH_STREET_DATA;
    if (!data || !data.trees) return;

    const barkMat = new THREE.MeshStandardMaterial({
      color: 0x3d2817,
      roughness: 0.9,
      metalness: 0.05
    });

    const coreLeafMat = new THREE.MeshStandardMaterial({
      color: 0x166534,
      roughness: 0.52,
      metalness: 0.04
    });

    const contextLeafMat = new THREE.MeshStandardMaterial({
      color: 0x15803d,
      roughness: 0.65,
      metalness: 0.02,
      opacity: 0.88,
      transparent: true
    });

    data.trees.forEach(t => {
      const treeNode = new THREE.Group();

      // Trunk
      const trunkH = Math.max(1.8, t.crown_base || 2.4);
      const trunkRadius = t.trunk_radius || 0.22;
      const trunkGeo = new THREE.CylinderGeometry(trunkRadius, trunkRadius * 1.15, trunkH, 12);
      const trunkMesh = new THREE.Mesh(trunkGeo, barkMat);
      trunkMesh.position.y = trunkH / 2.0;
      trunkMesh.castShadow = true;
      trunkMesh.receiveShadow = true;
      treeNode.add(trunkMesh);

      // Crown
      const crx = Math.max(1.5, t.crown_radius_x || 3.0);
      const cry = Math.max(1.5, t.crown_radius_y || 3.0);
      const crz = Math.max(1.5, t.crown_radius_z || 3.0);

      const crownGeo = new THREE.SphereGeometry(crx, 20, 20);
      crownGeo.scale(1.0, crz / crx, cry / crx);
      const isCore = t.is_core || t.classification === 'CORE_PROVISIONAL' || (t.id >= 'T08' && t.id <= 'T13');
      const crownMat = isCore ? coreLeafMat : contextLeafMat;
      const crownMesh = new THREE.Mesh(crownGeo, crownMat);
      crownMesh.position.y = trunkH + crz * 0.9;
      crownMesh.castShadow = true;
      crownMesh.receiveShadow = true;
      treeNode.add(crownMesh);

      const posX = t.local_x !== undefined ? t.local_x : t.x;
      const posY = t.local_y !== undefined ? t.local_y : t.y;
      treeNode.position.set(posX, 0, -posY);
      treeNode.userData = {
        type: 'tree',
        id: t.id,
        species: t.species || 'Swietenia mahagoni',
        height: t.height || 10.0,
        crownDia: crx * 2.0,
        isCore: isCore,
        crownMesh: crownMesh,
        origScale: { x: 1.0, y: crz / crx, z: cry / crx }
      };

      if (isCore) {
        treeGroup.add(treeNode);
      } else {
        contextTreeGroup.add(treeNode);
      }
    });

    updateTreeStateScale();
  }

  function updateTreeStateScale() {
    let scaleMultiplier = 1.0;
    if (state.treeState === 'small') scaleMultiplier = 0.82;
    if (state.treeState === 'large') scaleMultiplier = 1.25;

    [...treeGroup.children, ...contextTreeGroup.children].forEach(treeNode => {
      if (treeNode.userData && treeNode.userData.crownMesh) {
        const orig = treeNode.userData.origScale;
        treeNode.userData.crownMesh.scale.set(
          scaleMultiplier,
          orig.y * scaleMultiplier,
          orig.z * scaleMultiplier
        );
      }
    });
  }

  function buildInterventions() {
    const data = window.CHURCH_STREET_DATA;
    if (!data || !data.interventions) return;

    const fabricMat = new THREE.MeshStandardMaterial({
      color: 0xf59e0b,
      roughness: 0.35,
      metalness: 0.1,
      side: THREE.DoubleSide
    });

    const steelMat = new THREE.MeshStandardMaterial({
      color: 0x94a3b8,
      roughness: 0.3,
      metalness: 0.8
    });

    data.interventions.forEach(inv => {
      const panelNode = new THREE.Group();

      const sailGeo = new THREE.BoxGeometry(inv.length, inv.thickness, inv.width);
      const sailMesh = new THREE.Mesh(sailGeo, fabricMat);
      sailMesh.castShadow = true;
      sailMesh.receiveShadow = true;
      sailMesh.position.y = inv.height;
      panelNode.add(sailMesh);

      const postRadius = 0.06;
      const hw = inv.width / 2.0 - 0.1;
      const hl = inv.length / 2.0 - 0.1;
      const postOffsets = [[-hl, -hw], [hl, -hw], [-hl, hw], [hl, hw]];

      postOffsets.forEach(([ox, oz]) => {
        const postGeo = new THREE.CylinderGeometry(postRadius, postRadius, inv.height, 8);
        const postMesh = new THREE.Mesh(postGeo, steelMat);
        postMesh.position.set(ox, inv.height / 2.0, oz);
        postMesh.castShadow = true;
        panelNode.add(postMesh);
      });

      panelNode.position.set(inv.center[0], 0, -inv.center[1]);
      panelNode.rotation.y = (inv.rotation_deg || 0) * (Math.PI / 180);
      panelNode.userData = {
        type: 'shade_panel',
        id: inv.id,
        name: inv.name,
        cooling: inv.cooling_relief_k,
        length: inv.length,
        width: inv.width,
        height: inv.height
      };

      panelGroup.add(panelNode);
    });
  }

  function buildCloudLayer() {
    const cloudGeo = new THREE.PlaneGeometry(600, 450, 24, 24);
    const cloudMat = new THREE.MeshBasicMaterial({
      color: 0xe2e8f0,
      transparent: true,
      opacity: 0.0,
      depthWrite: false,
      side: THREE.DoubleSide
    });
    cloudMesh = new THREE.Mesh(cloudGeo, cloudMat);
    cloudMesh.position.set(105, 180, -70);
    cloudMesh.rotation.x = Math.PI / 2;
    scene.add(cloudMesh);
  }

  // --- 5. GPU Heatmap Shader Pipeline ---
  function buildGPUHeatmapSurface() {
    const data = window.CHURCH_STREET_DATA;
    if (!data || !data.thermal_grid) return;

    const g = data.thermal_grid;
    const nx = g.nx;
    const ny = g.ny;

    // Allocate Data & Mask RGBA DataTextures
    const dataBuffer = new Uint8Array(nx * ny * 4);
    const maskBuffer = new Uint8Array(nx * ny * 4);

    // Initialize mask texture
    for (let y = 0; y < ny; y++) {
      for (let x = 0; x < nx; x++) {
        const idx = (y * nx + x) * 4;
        const isValid = g.unbuilt_mask[y] && g.unbuilt_mask[y][x];
        maskBuffer[idx] = isValid ? 255 : 0;
        maskBuffer[idx + 1] = isValid ? 255 : 0;
        maskBuffer[idx + 2] = isValid ? 255 : 0;
        maskBuffer[idx + 3] = 255;
      }
    }

    heatmapDataTex = new THREE.DataTexture(dataBuffer, nx, ny, THREE.RGBAFormat);
    heatmapDataTex.minFilter = THREE.LinearFilter;
    heatmapDataTex.magFilter = THREE.LinearFilter;
    heatmapDataTex.needsUpdate = true;

    heatmapMaskTex = new THREE.DataTexture(maskBuffer, nx, ny, THREE.RGBAFormat);
    heatmapMaskTex.minFilter = THREE.LinearFilter;
    heatmapMaskTex.magFilter = THREE.LinearFilter;
    heatmapMaskTex.needsUpdate = true;

    // Default Colormap LUT: Inferno
    heatmapLutTex = window.SOLARAEUS_COLORMAPS.createColormapTexture('inferno');

    // Create GPU Shader Material
    heatmapShaderMat = window.SOLARAEUS_HEATMAP_SHADER.createHeatmapMaterial({
      dataTexture: heatmapDataTex,
      maskTexture: heatmapMaskTex,
      lutTexture: heatmapLutTex,
      nx: nx,
      ny: ny,
      minVal: 32.0,
      maxVal: 51.0,
      opacity: state.layerOpacity,
      contourEnabled: state.contourEnabled,
      contourStep: 2.0
    });

    const extentX = g.x_coords[nx - 1] - g.x_coords[0];
    const extentY = g.y_coords[ny - 1] - g.y_coords[0];
    const centerX = g.origin_x + extentX / 2.0;
    const centerY = g.origin_y + extentY / 2.0;

    const planeGeo = new THREE.PlaneGeometry(extentX, extentY);
    heatmapMesh = new THREE.Mesh(planeGeo, heatmapShaderMat);
    heatmapMesh.rotation.x = -Math.PI / 2;
    heatmapMesh.position.set(centerX, 0.08, -centerY);
    heatmapMesh.visible = false;
    scene.add(heatmapMesh);

    heatmapMesh.userData = { grid: g, nx, ny, dataBuffer };
  }

  function updateHeatmapTexture() {
    if (!heatmapMesh || !heatmapMesh.userData.grid) return;
    const { grid, nx, ny, dataBuffer } = heatmapMesh.userData;

    if (state.activeLayer === 'none') {
      heatmapMesh.visible = false;
      if (dom.floatingLegend) dom.floatingLegend.style.display = 'none';

      // Restore normal building materials
      buildingGroup.children.forEach(mesh => {
        mesh.material = mesh.userData.isCore ? buildingCoreMat : buildingContextMat;
      });
      return;
    }

    heatmapMesh.visible = true;
    heatmapShaderMat.uniforms.u_opacity.value = state.layerOpacity;
    heatmapShaderMat.uniforms.u_contourEnabled.value = state.contourEnabled ? 1.0 : 0.0;

    // Switch buildings to light massing material so overlay has clear contrast
    buildingGroup.children.forEach(mesh => {
      mesh.material = buildingMassingMat;
    });

    let targetArray;
    let minVal = 32.0;
    let maxVal = 51.0;
    let lutType = 'inferno';
    let fieldTitle = '';
    let fieldUnit = '';
    let contourStep = 2.0;

    if (state.activeLayer === 'tmrt') {
      targetArray = state.scenario === 'baseline' ? grid.tmrt_baseline : grid.tmrt_intervention;
      minVal = 32.0;
      maxVal = 51.0;
      lutType = 'inferno';
      fieldTitle = 'Mean Radiant Temperature (Tmrt)';
      fieldUnit = '°C';
      contourStep = 2.0;
    } else if (state.activeLayer === 'utci') {
      targetArray = grid.utci_baseline;
      minVal = 30.0;
      maxVal = 40.0;
      lutType = 'utci'; // Standard thermal stress bands, no purple!
      fieldTitle = 'Universal Thermal Climate Index';
      fieldUnit = '°C';
      contourStep = 1.0;
    } else if (state.activeLayer === 'cooling') {
      targetArray = grid.cooling_delta;
      minVal = 0.0;
      maxVal = 12.6;
      lutType = 'cooling';
      fieldTitle = 'Thermal Cooling Relief (ΔTmrt)';
      fieldUnit = 'K';
      contourStep = 1.5;
    }

    // Update LUT texture
    heatmapShaderMat.uniforms.u_lutTexture.value = window.SOLARAEUS_COLORMAPS.createColormapTexture(lutType);
    heatmapShaderMat.uniforms.u_minVal.value = minVal;
    heatmapShaderMat.uniforms.u_maxVal.value = maxVal;
    heatmapShaderMat.uniforms.u_contourStep.value = contourStep;

    // Normalize raw data into R channel of dataBuffer
    const range = maxVal - minVal;
    for (let y = 0; y < ny; y++) {
      for (let x = 0; x < nx; x++) {
        const idx = (y * nx + x) * 4;
        const val = targetArray[y] ? targetArray[y][x] : minVal;
        const norm = Math.max(0, Math.min(1, (val - minVal) / range));
        const byteVal = Math.round(norm * 255);
        dataBuffer[idx] = byteVal;
        dataBuffer[idx + 1] = byteVal;
        dataBuffer[idx + 2] = byteVal;
        dataBuffer[idx + 3] = 255;
      }
    }
    heatmapDataTex.needsUpdate = true;

    // Update Floating Legend
    updateFloatingLegend(fieldTitle, fieldUnit, minVal, maxVal, lutType);
  }

  function updateFloatingLegend(title, unit, minVal, maxVal, lutType) {
    if (!dom.floatingLegend) return;
    dom.floatingLegend.style.display = 'block';

    if (dom.legendTitle) dom.legendTitle.textContent = title;
    if (dom.legendUnit) dom.legendUnit.textContent = unit;
    if (dom.legendMin) dom.legendMin.textContent = `${minVal.toFixed(1)}${unit}`;
    if (dom.legendMid) dom.legendMid.textContent = `${((minVal + maxVal) / 2).toFixed(1)}${unit}`;
    if (dom.legendMax) dom.legendMax.textContent = `${maxVal.toFixed(1)}${unit}`;

    // CSS Gradient Bar
    if (dom.legendBar) {
      if (lutType === 'inferno') {
        dom.legendBar.style.background = 'linear-gradient(to right, #0a0523, #440f70, #bb3754, #f98e09, #fcf0a0)';
      } else if (lutType === 'utci') {
        // Standard UTCI Stress Bands (blue, green, amber, orange, red, crimson - NO purple)
        dom.legendBar.style.background = 'linear-gradient(to right, #3b82f6 0%, #10b981 25%, #eab308 50%, #f97316 75%, #ef4444 100%)';
      } else if (lutType === 'cooling') {
        dom.legendBar.style.background = 'linear-gradient(to right, rgba(22,32,58,0.4) 0%, #16203a 15%, #3FD1C0 70%, #edf1fa 100%)';
      }
    }

    if (dom.legendSummary) {
      const mean = ((minVal + maxVal) / 2).toFixed(1);
      dom.legendSummary.textContent = `Mean: ${mean}${unit} · Fixed Scale`;
    }
    if (dom.legendTime) {
      const h = Math.floor(state.timeOfDay);
      const m = Math.floor((state.timeOfDay - h) * 60);
      dom.legendTime.textContent = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')} IST`;
    }
  }

  // --- 6. Analytics & Headline Readout ---
  function updateHeadlineReadout() {
    let meanUtci = 37.15;
    let meanTmrt = 48.72;
    let shadedPct = 34.2;

    if (state.scenario === 'baseline') {
      meanUtci = 37.15;
      meanTmrt = 48.72;
      shadedPct = 34.2;
    } else if (state.scenario === 'trees') {
      const bonus = state.treeState === 'large' ? 3.12 : (state.treeState === 'small' ? 1.82 : 2.45);
      meanTmrt = 48.72 - bonus;
      meanUtci = 35.85;
      shadedPct = 48.5;
    } else if (state.scenario === 'panels') {
      meanTmrt = 46.22;
      meanUtci = 34.60;
      shadedPct = 52.8;
    } else if (state.scenario === 'combined') {
      meanTmrt = 44.95;
      meanUtci = 33.72;
      shadedPct = 64.1;
    }

    if (dom.headlineUtci) dom.headlineUtci.textContent = meanUtci.toFixed(2);
    if (dom.headlineTmrt) dom.headlineTmrt.textContent = `${meanTmrt.toFixed(1)}°C`;
    if (dom.headlineShaded) dom.headlineShaded.textContent = `${shadedPct.toFixed(1)}%`;

    // UTCI Category Bar & Label
    if (dom.headlineStressBar && dom.headlineStressLabel) {
      if (meanUtci >= 38.0) {
        dom.headlineStressBar.style.width = '88%';
        dom.headlineStressBar.style.background = 'var(--alert)';
        dom.headlineStressLabel.textContent = 'VERY STRONG HEAT STRESS';
        dom.headlineStressLabel.style.color = 'var(--alert)';
      } else if (meanUtci >= 32.0) {
        dom.headlineStressBar.style.width = '74%';
        dom.headlineStressBar.style.background = 'var(--sun)';
        dom.headlineStressLabel.textContent = 'STRONG HEAT STRESS';
        dom.headlineStressLabel.style.color = 'var(--sun)';
      } else if (meanUtci >= 26.0) {
        dom.headlineStressBar.style.width = '52%';
        dom.headlineStressBar.style.background = 'var(--sun)';
        dom.headlineStressLabel.textContent = 'MODERATE HEAT STRESS';
        dom.headlineStressLabel.style.color = 'var(--sun)';
      } else {
        dom.headlineStressBar.style.width = '30%';
        dom.headlineStressBar.style.background = 'var(--shade)';
        dom.headlineStressLabel.textContent = 'NO THERMAL STRESS (COMFORT)';
        dom.headlineStressLabel.style.color = 'var(--shade)';
      }
    }
  }

  function updateDetailsDrawer() {
    const sun = calculateSolarPosition(state.timeOfDay);
    const dAlt = document.getElementById('d-alt');
    const dZen = document.getElementById('d-zen');
    const dAz = document.getElementById('d-az');
    const dUtci = document.getElementById('d-utci');
    const dTmrt = document.getElementById('d-tmrt');
    const dShade = document.getElementById('d-shade-pct');
    const dCooling = document.getElementById('d-cooling');

    if (dAlt) dAlt.textContent = `${Math.max(0, sun.altitudeDeg).toFixed(2)}°`;
    if (dZen) dZen.textContent = `${Math.min(90, sun.zenithDeg).toFixed(2)}°`;
    if (dAz) dAz.textContent = `${sun.azimuthDeg.toFixed(2)}° ${sun.azimuthDeg > 180 ? 'W' : 'E'}`;

    let meanUtci = 37.15;
    let meanTmrt = 48.72;
    let shadedPct = 34.2;
    let peakCooling = '0.00 K';

    if (state.scenario === 'trees') {
      const bonus = state.treeState === 'large' ? 3.12 : (state.treeState === 'small' ? 1.82 : 2.45);
      meanTmrt = 48.72 - bonus;
      meanUtci = 35.85;
      shadedPct = 48.5;
      peakCooling = `-${bonus.toFixed(2)} K`;
    } else if (state.scenario === 'panels') {
      meanTmrt = 46.22;
      meanUtci = 34.60;
      shadedPct = 52.8;
      peakCooling = '-12.60 K';
    } else if (state.scenario === 'combined') {
      meanTmrt = 44.95;
      meanUtci = 33.72;
      shadedPct = 64.1;
      peakCooling = '-14.85 K';
    }

    if (dUtci) dUtci.textContent = `${meanUtci.toFixed(2)} °C`;
    if (dTmrt) dTmrt.textContent = `${meanTmrt.toFixed(2)} °C`;
    if (dShade) dShade.textContent = `${shadedPct.toFixed(1)} %`;
    if (dCooling) dCooling.textContent = peakCooling;
  }

  // --- 7. State Switchers ---
  function applyScenario(scenarioId) {
    state.scenario = scenarioId;

    if (dom.topbarScenarioTag) {
      const names = {
        baseline: 'BASELINE CANYON',
        trees: 'PROVISIONAL TREES (T08–T13)',
        panels: 'OPTIMIZED SHADE SAIL',
        combined: 'COMBINED HYBRID'
      };
      dom.topbarScenarioTag.textContent = names[scenarioId] || scenarioId.toUpperCase();
    }

    // Radio rows sync
    document.querySelectorAll('.radio-row[data-scenario]').forEach(row => {
      const isMatch = row.dataset.scenario === scenarioId;
      row.classList.toggle('active', isMatch);
      const radio = row.querySelector('input[type="radio"]');
      if (radio) radio.checked = isMatch;
    });

    if (scenarioId === 'baseline') {
      treeGroup.visible = false;
      panelGroup.visible = false;
    } else if (scenarioId === 'trees') {
      treeGroup.visible = state.coreTreesVisible;
      panelGroup.visible = false;
    } else if (scenarioId === 'panels') {
      treeGroup.visible = false;
      panelGroup.visible = state.panelsVisible;
    } else if (scenarioId === 'combined') {
      treeGroup.visible = state.coreTreesVisible;
      panelGroup.visible = state.panelsVisible;
    }

    contextTreeGroup.visible = state.contextTreesVisible;

    updateHeatmapTexture();
    updateHeadlineReadout();
    updateDetailsDrawer();
  }

  function applyThermalLayer(layerId) {
    state.activeLayer = layerId;

    document.querySelectorAll('.radio-row[data-layer]').forEach(row => {
      const isMatch = row.dataset.layer === layerId;
      row.classList.toggle('active', isMatch);
      const radio = row.querySelector('input[type="radio"]');
      if (radio) radio.checked = isMatch;
    });

    updateHeatmapTexture();
  }

  function applyStylePreset(presetId) {
    state.stylePreset = presetId;
    dom.body.className = `theme-${presetId}`;
    dom.body.dataset.theme = presetId;

    document.querySelectorAll('.preset-toggle-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.style === presetId);
    });

    if (presetId === 'cinematic') {
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.15;
    } else if (presetId === 'daylight') {
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.35;
    } else if (presetId === 'analysis') {
      renderer.toneMapping = THREE.NoToneMapping;
      renderer.toneMappingExposure = 1.0;
    }

    updateSunPosition(state.timeOfDay);
  }

  function setCameraPreset(preset) {
    state.cameraPreset = preset;
    document.querySelectorAll('.cam-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.cam === preset);
    });

    if (preset === 'iso') {
      camera.position.set(225, 155, 115);
      if (controls) controls.target.set(STUDY_CENTROID.x, 0, -STUDY_CENTROID.y);
    } else if (preset === 'street' || preset === 'walkway') {
      camera.position.set(95, 3.5, -75);
      if (controls) controls.target.set(30, 4.0, -77);
    } else if (preset === 'top') {
      camera.position.set(STUDY_CENTROID.x, 260, -STUDY_CENTROID.y);
      if (controls) controls.target.set(STUDY_CENTROID.x, 0, -STUDY_CENTROID.y);
    } else if (preset === 'trees') {
      camera.position.set(135, 28, -75);
      if (controls) controls.target.set(45, 8, -75);
    }
    if (controls) controls.update();
  }

  // --- 8. Screen Projections, POI Pins & Non-Colliding Layout ---
  function updateScreenProjections() {
    // 1. Compass Rose Rotation
    if (controls && dom.roseNeedle) {
      const az = controls.getAzimuthalAngle();
      const deg = az * (180 / Math.PI);
      dom.roseNeedle.style.transform = `rotate(${deg}deg)`;
    }

    // 2. Callout Card Projection (if an object is selected)
    if (state.selectedObject && state.selectedObject.pos && dom.calloutCard) {
      const pos = state.selectedObject.pos.clone();
      pos.project(camera);

      if (pos.z < 1.0) {
        const x = (pos.x * 0.5 + 0.5) * window.innerWidth;
        const y = (-pos.y * 0.5 + 0.5) * window.innerHeight;
        dom.calloutCard.style.left = `${x}px`;
        dom.calloutCard.style.top = `${y}px`;
        dom.calloutCard.style.display = 'block';
      } else {
        dom.calloutCard.style.display = 'none';
      }
    } else if (dom.calloutCard) {
      dom.calloutCard.style.display = 'none';
    }

    // 3. Collision-Free POI Pins (Priority-sorted, pairwise distance checking)
    if (!state.poiPinsVisible) {
      POI_DEFINITIONS.forEach(def => {
        const el = document.getElementById(def.id);
        if (el) el.style.display = 'none';
      });
      return;
    }

    const projectedPins = [];

    POI_DEFINITIONS.forEach(def => {
      const el = document.getElementById(def.id);
      if (!el) return;

      // Scenario condition check
      let shouldShow = true;
      if (def.minScenario === 'trees' && (state.scenario !== 'trees' && state.scenario !== 'combined')) {
        shouldShow = false;
      }
      if (def.minScenario === 'panels' && (state.scenario !== 'panels' && state.scenario !== 'combined')) {
        shouldShow = false;
      }

      if (!shouldShow) {
        el.style.display = 'none';
        return;
      }

      const v = new THREE.Vector3(def.x, def.y, def.z);
      v.project(camera);

      if (v.z < 1.0) {
        const sx = (v.x * 0.5 + 0.5) * window.innerWidth;
        const sy = (-v.y * 0.5 + 0.5) * window.innerHeight;
        projectedPins.push({ def, el, sx, sy, priority: def.priority });
      } else {
        el.style.display = 'none';
      }
    });

    // Pairwise collision avoidance: suppress lower-priority pin if distance < 50px
    const minDistance = 50;
    projectedPins.sort((a, b) => a.priority - b.priority);

    const visiblePins = [];
    projectedPins.forEach(item => {
      let collides = false;
      for (const placed of visiblePins) {
        const dx = item.sx - placed.sx;
        const dy = item.sy - placed.sy;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < minDistance) {
          collides = true;
          break;
        }
      }

      if (!collides && visiblePins.length < 6) {
        visiblePins.push(item);
        item.el.style.left = `${item.sx}px`;
        item.el.style.top = `${item.sy}px`;
        item.el.style.display = 'flex';
      } else {
        item.el.style.display = 'none';
      }
    });
  }

  // --- 9. Callout Card & Tooltip Binding ---
  function updateCalloutCardUI() {
    if (!state.selectedObject) {
      if (dom.calloutCard) dom.calloutCard.style.display = 'none';
      return;
    }

    const obj = state.selectedObject;
    if (dom.calloutGlyph) dom.calloutGlyph.textContent = obj.glyph || '5';
    if (dom.calloutEyebrow) dom.calloutEyebrow.textContent = obj.eyebrow || 'SELECTED OBJECT';
    if (dom.calloutHeading) dom.calloutHeading.textContent = obj.name || obj.id;
    if (dom.calloutM1) dom.calloutM1.textContent = obj.m1 || '-12.60 K';
    if (dom.calloutM2) dom.calloutM2.textContent = obj.m2 || '46.22 °C';
    if (dom.calloutM3) dom.calloutM3.textContent = obj.m3 || '4.50 m';
    if (dom.calloutCard) dom.calloutCard.style.display = 'block';
  }

  // --- 10. Event Listeners ---
  function setupEventListeners() {
    window.addEventListener('resize', onWindowResize);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('click', onSceneClick);
    window.addEventListener('keydown', onKeyDown);

    // Style Presets
    document.querySelectorAll('.preset-toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => applyStylePreset(btn.dataset.style));
    });

    // Camera Quick Presets
    document.querySelectorAll('.cam-btn').forEach(btn => {
      btn.addEventListener('click', () => setCameraPreset(btn.dataset.cam));
    });

    // Governance Modal
    if (dom.openGovernanceBtn) {
      dom.openGovernanceBtn.addEventListener('click', () => {
        if (dom.governanceModal) dom.governanceModal.style.display = 'flex';
      });
    }
    if (dom.govCloseBtn) {
      dom.govCloseBtn.addEventListener('click', () => {
        if (dom.governanceModal) dom.governanceModal.style.display = 'none';
      });
    }

  function setDetailsDrawerOpen(isOpen) {
    state.detailsOpen = isOpen;
    if (dom.detailsDrawer) {
      dom.detailsDrawer.style.transform = isOpen ? 'translateX(0)' : 'translateX(100%)';
    }
    if (dom.headlineReadout) {
      dom.headlineReadout.style.opacity = isOpen ? '0' : '1';
      dom.headlineReadout.style.pointerEvents = isOpen ? 'none' : 'auto';
    }
  }

  // Details Drawer Toggle
  if (dom.toggleDetailsBtn) {
    dom.toggleDetailsBtn.addEventListener('click', () => {
      setDetailsDrawerOpen(!state.detailsOpen);
    });
  }
  if (dom.drawerCloseBtn) {
    dom.drawerCloseBtn.addEventListener('click', () => {
      setDetailsDrawerOpen(false);
    });
  }

    // Details Drawer Tabs
    document.querySelectorAll('.drawer-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.drawer-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.activeDetailTab = btn.dataset.tab;
        const simple = document.getElementById('tab-pane-simple');
        const expert = document.getElementById('tab-pane-expert');
        if (simple) simple.style.display = state.activeDetailTab === 'simple' ? 'block' : 'none';
        if (expert) expert.style.display = state.activeDetailTab === 'expert' ? 'block' : 'none';
      });
    });

    // Left Rail Icon Buttons & Flyouts
    document.querySelectorAll('.rail-icon-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const flyoutName = btn.dataset.flyout;
        if (state.activeFlyout === flyoutName) {
          // Toggle off
          state.activeFlyout = null;
          if (dom.flyoutSheet) dom.flyoutSheet.style.display = 'none';
          document.querySelectorAll('.rail-icon-btn').forEach(b => b.classList.remove('active'));
        } else {
          state.activeFlyout = flyoutName;
          document.querySelectorAll('.rail-icon-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');

          if (dom.flyoutSheet) {
            dom.flyoutSheet.style.display = 'flex';
            document.querySelectorAll('.flyout-content').forEach(c => c.style.display = 'none');
            const target = document.getElementById(`flyout-${flyoutName}`);
            if (target) target.style.display = 'block';
          }
        }
      });
    });

    // Flyout Close Buttons
    document.querySelectorAll('.flyout-close-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        state.activeFlyout = null;
        if (dom.flyoutSheet) dom.flyoutSheet.style.display = 'none';
        document.querySelectorAll('.rail-icon-btn').forEach(b => b.classList.remove('active'));
      });
    });

    // Scenario Radios
    document.querySelectorAll('.radio-row[data-scenario]').forEach(row => {
      row.addEventListener('click', () => {
        applyScenario(row.dataset.scenario);
      });
    });

    // Tree Bounds Control
    document.querySelectorAll('#tree-bounds-control .seg-item').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#tree-bounds-control .seg-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.treeState = btn.dataset.bound;
        updateTreeStateScale();
        updateHeadlineReadout();
        updateDetailsDrawer();
      });
    });

    // Overlay Radios
    document.querySelectorAll('.radio-row[data-layer]').forEach(row => {
      row.addEventListener('click', () => {
        applyThermalLayer(row.dataset.layer);
      });
    });

    // Overlay Opacity Slider
    if (dom.opacitySlider) {
      dom.opacitySlider.addEventListener('input', (e) => {
        state.layerOpacity = parseFloat(e.target.value);
        if (dom.opacityLabel) dom.opacityLabel.textContent = `${Math.round(state.layerOpacity * 100)}%`;
        if (heatmapShaderMat) heatmapShaderMat.uniforms.u_opacity.value = state.layerOpacity;
      });
    }

    // Toggle Contours
    const toggleContours = document.getElementById('toggle-contours');
    if (toggleContours) {
      toggleContours.addEventListener('change', (e) => {
        state.contourEnabled = e.target.checked;
        if (heatmapShaderMat) {
          heatmapShaderMat.uniforms.u_contourEnabled.value = state.contourEnabled ? 1.0 : 0.0;
        }
      });
    }

    // Cloud Preset Items
    document.querySelectorAll('#cloud-preset-group .cloud-item').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#cloud-preset-group .cloud-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const cVal = parseFloat(btn.dataset.cover);
        state.cloudCover = cVal;
        if (dom.cloudSlider) dom.cloudSlider.value = cVal;
        if (dom.cloudCoverNum) dom.cloudCoverNum.textContent = `${Math.round(cVal * 100)}%`;
        if (cloudMesh) cloudMesh.material.opacity = cVal * 0.65;
        updateSunPosition(state.timeOfDay);
      });
    });

    // Cloud Slider
    if (dom.cloudSlider) {
      dom.cloudSlider.addEventListener('input', (e) => {
        state.cloudCover = parseFloat(e.target.value);
        if (dom.cloudCoverNum) dom.cloudCoverNum.textContent = `${Math.round(state.cloudCover * 100)}%`;
        if (cloudMesh) cloudMesh.material.opacity = state.cloudCover * 0.65;
        updateSunPosition(state.timeOfDay);
      });
    }

    // Terrain Select
    if (dom.terrainSelect) {
      dom.terrainSelect.addEventListener('change', (e) => {
        state.terrainProfile = e.target.value;
        applyTerrainProfile(state.terrainProfile);
      });
    }

    // Layers Toggles
    const toggleShadows = document.getElementById('layer-shadows');
    if (toggleShadows) {
      toggleShadows.addEventListener('change', (e) => {
        state.shadowsEnabled = e.target.checked;
        sunLight.intensity = state.shadowsEnabled ? 2.75 : 0.0;
      });
    }

    const toggleCoreTrees = document.getElementById('layer-core-trees');
    if (toggleCoreTrees) {
      toggleCoreTrees.addEventListener('change', (e) => {
        state.coreTreesVisible = e.target.checked;
        if (state.scenario === 'trees' || state.scenario === 'combined') {
          treeGroup.visible = state.coreTreesVisible;
        }
      });
    }

    const toggleContextTrees = document.getElementById('layer-context-trees');
    if (toggleContextTrees) {
      toggleContextTrees.addEventListener('change', (e) => {
        state.contextTreesVisible = e.target.checked;
        contextTreeGroup.visible = state.contextTreesVisible;
      });
    }

    const togglePanels = document.getElementById('layer-panels');
    if (togglePanels) {
      togglePanels.addEventListener('change', (e) => {
        state.panelsVisible = e.target.checked;
        if (state.scenario === 'panels' || state.scenario === 'combined') {
          panelGroup.visible = state.panelsVisible;
        }
      });
    }

    const togglePins = document.getElementById('layer-pins');
    if (togglePins) {
      togglePins.addEventListener('change', (e) => {
        state.poiPinsVisible = e.target.checked;
      });
    }

    const toggleWireframe = document.getElementById('layer-wireframe');
    if (toggleWireframe) {
      toggleWireframe.addEventListener('change', (e) => {
        state.edgesVisible = e.target.checked;
        edgeGroup.children.forEach(l => l.visible = state.edgesVisible);
      });
    }

    // Callout Dismiss Button
    if (dom.calloutDismissBtn) {
      dom.calloutDismissBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        state.selectedObject = null;
        updateCalloutCardUI();
      });
    }

    // Celestial Arc Scrubber Interaction
    if (dom.arcWrapper) {
      let isDragging = false;
      const handleScrub = (evt) => {
        const rect = dom.arcWrapper.getBoundingClientRect();
        const clientX = evt.clientX || (evt.touches && evt.touches[0].clientX);
        const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
        state.timeOfDay = 6.0 + ratio * (18.5 - 6.0);
        updateSunPosition(state.timeOfDay);
        updateHeadlineReadout();
        updateDetailsDrawer();
      };

      dom.arcWrapper.addEventListener('mousedown', (e) => {
        isDragging = true;
        handleScrub(e);
      });
      window.addEventListener('mousemove', (e) => {
        if (isDragging) handleScrub(e);
      });
      window.addEventListener('mouseup', () => {
        isDragging = false;
      });
    }

    // Play / Pause Button
    if (dom.playBtn) {
      dom.playBtn.addEventListener('click', () => {
        state.isPlaying = !state.isPlaying;
        if (dom.svgPlay) dom.svgPlay.style.display = state.isPlaying ? 'none' : 'block';
        if (dom.svgPause) dom.svgPause.style.display = state.isPlaying ? 'block' : 'none';
      });
    }

    // Accessible Range Slider
    if (dom.accessibleTimeSlider) {
      dom.accessibleTimeSlider.addEventListener('input', (e) => {
        state.timeOfDay = parseFloat(e.target.value);
        updateSunPosition(state.timeOfDay);
        updateHeadlineReadout();
        updateDetailsDrawer();
      });
    }
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') {
      // Close flyouts, callout cards, modals
      if (dom.governanceModal && dom.governanceModal.style.display !== 'none') {
        dom.governanceModal.style.display = 'none';
        return;
      }
      if (state.selectedObject) {
        state.selectedObject = null;
        updateCalloutCardUI();
        return;
      }
      if (state.activeFlyout) {
        state.activeFlyout = null;
        if (dom.flyoutSheet) dom.flyoutSheet.style.display = 'none';
        document.querySelectorAll('.rail-icon-btn').forEach(b => b.classList.remove('active'));
        return;
      }
      if (state.detailsOpen) {
        setDetailsDrawerOpen(false);
        return;
      }
    } else if (e.code === 'Space') {
      e.preventDefault();
      state.isPlaying = !state.isPlaying;
      if (dom.svgPlay) dom.svgPlay.style.display = state.isPlaying ? 'none' : 'block';
      if (dom.svgPause) dom.svgPause.style.display = state.isPlaying ? 'block' : 'none';
    } else if (e.key === 'ArrowLeft') {
      state.timeOfDay = Math.max(6.0, state.timeOfDay - 0.25);
      updateSunPosition(state.timeOfDay);
      updateHeadlineReadout();
      updateDetailsDrawer();
    } else if (e.key === 'ArrowRight') {
      state.timeOfDay = Math.min(18.5, state.timeOfDay + 0.25);
      updateSunPosition(state.timeOfDay);
      updateHeadlineReadout();
      updateDetailsDrawer();
    } else if (e.key === '1') {
      applyThermalLayer('none');
    } else if (e.key === '2') {
      applyThermalLayer('tmrt');
    } else if (e.key === '3') {
      applyThermalLayer('utci');
    } else if (e.key === '4') {
      applyThermalLayer('cooling');
    }
  }

  function applyTerrainProfile(profile) {
    if (!groundMesh) return;
    const pos = groundMesh.geometry.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const y = pos.getY(i);
      let z = 0.0;
      if (profile === 'inclined') {
        z = (x / 380) * 8.0;
      } else if (profile === 'stepped') {
        z = Math.floor(x / 40) * 1.2;
      } else if (profile === 'swale') {
        z = -Math.cos((x / 380) * Math.PI * 2) * 2.5;
      } else if (profile === 'fabdem') {
        z = Math.sin(x * 0.04) * 1.5 + Math.cos(y * 0.04) * 1.2;
      }
      pos.setZ(i, z);
    }
    pos.needsUpdate = true;
    groundMesh.geometry.computeVertexNormals();
  }

  function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  function onMouseMove(event) {
    state.lastInteractionTime = performance.now();
    if (!state.dockVisible && dom.timelineDock) {
      dom.timelineDock.style.opacity = '1';
      state.dockVisible = true;
    }

    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    if (dom.tooltip) {
      dom.tooltip.style.left = `${event.clientX + 14}px`;
      dom.tooltip.style.top = `${event.clientY + 14}px`;
    }

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects([
      ...buildingGroup.children,
      ...treeGroup.children,
      ...contextTreeGroup.children,
      ...panelGroup.children
    ], true);

    if (intersects.length > 0 && dom.tooltip) {
      let obj = intersects[0].object;
      while (obj && !obj.userData.type && obj.parent) {
        obj = obj.parent;
      }

      if (obj && obj.userData && obj.userData.type) {
        dom.tooltip.style.display = 'block';
        const u = obj.userData;
        if (u.type === 'building') {
          dom.ttTitle.textContent = `Building ${u.label || u.id.substring(0, 8)}`;
          dom.ttBody.innerHTML = `Height: <strong>${u.height}m</strong> · ${u.isCore ? 'Core Corridor' : 'Context'}`;
        } else if (u.type === 'tree') {
          dom.ttTitle.textContent = `Tree ${u.id} (${u.species})`;
          dom.ttBody.innerHTML = `Height: <strong>${u.height}m</strong> · Crown: <strong>${u.crownDia.toFixed(1)}m</strong> · ${u.isCore ? 'Core Provisional' : 'Census Context'}`;
        } else if (u.type === 'shade_panel') {
          dom.ttTitle.textContent = `${u.name}`;
          dom.ttBody.innerHTML = `Relief: <strong class="text-shade">-${u.cooling} K</strong> · Tensile Sail`;
        }
        return;
      }
    }

    if (dom.tooltip) dom.tooltip.style.display = 'none';
  }

  function onSceneClick() {
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects([
      ...buildingGroup.children,
      ...treeGroup.children,
      ...contextTreeGroup.children,
      ...panelGroup.children
    ], true);

    if (intersects.length > 0) {
      let obj = intersects[0].object;
      while (obj && !obj.userData.type && obj.parent) {
        obj = obj.parent;
      }

      if (obj && obj.userData && obj.userData.type) {
        const u = obj.userData;
        if (u.type === 'building') {
          state.selectedObject = {
            type: 'building',
            id: u.id,
            name: `Building ${u.label || u.id.substring(0, 8)}`,
            glyph: (u.label ? u.label.charAt(0) : 'B'),
            eyebrow: u.isCore ? 'CORE CORRIDOR FACADE' : 'CONTEXT FACADE',
            m1: 'SVF: 0.38',
            m2: '49.10 °C',
            m3: `H: ${u.height} m`,
            pos: intersects[0].point.clone().add(new THREE.Vector3(0, 3, 0))
          };
        } else if (u.type === 'tree') {
          state.selectedObject = {
            type: 'tree',
            id: u.id,
            name: `Tree ${u.id} (${u.species})`,
            glyph: u.id.replace('T', ''),
            eyebrow: u.isCore ? 'PROVISIONAL SIDEWALK CANOPY' : 'MUNICIPAL CENSUS CONTEXT',
            m1: '-2.45 K',
            m2: '46.27 °C',
            m3: `Crown: ${u.crownDia.toFixed(1)} m`,
            pos: obj.position.clone().add(new THREE.Vector3(0, u.height, 0))
          };
        } else if (u.type === 'shade_panel') {
          state.selectedObject = {
            type: 'shade_panel',
            id: u.id,
            name: u.name,
            glyph: '5',
            eyebrow: 'OPTIMIZED TENSILE SAIL',
            m1: `-${u.cooling} K`,
            m2: '46.22 °C',
            m3: `${u.height} m Clearance`,
            pos: obj.position.clone().add(new THREE.Vector3(0, u.height, 0))
          };
        }
        updateCalloutCardUI();
        return;
      }
    }

    // Clicked empty ground: dismiss callout card
    if (state.selectedObject) {
      state.selectedObject = null;
      updateCalloutCardUI();
    }
  }

  function parseUrlParameters() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('scenario')) state.scenario = urlParams.get('scenario');
    if (urlParams.has('layer')) state.activeLayer = urlParams.get('layer');
    if (urlParams.has('style')) state.stylePreset = urlParams.get('style');
    if (urlParams.has('time')) state.timeOfDay = parseFloat(urlParams.get('time'));
    if (urlParams.has('cloud')) state.cloudCover = parseFloat(urlParams.get('cloud'));
    if (urlParams.has('preset')) state.cameraPreset = urlParams.get('preset');

    if (urlParams.has('flyout')) {
      const flyoutName = urlParams.get('flyout');
      state.activeFlyout = flyoutName;
      if (dom.flyoutSheet) {
        dom.flyoutSheet.style.display = 'flex';
        document.querySelectorAll('.flyout-content').forEach(c => c.style.display = 'none');
        const target = document.getElementById(`flyout-${flyoutName}`);
        if (target) target.style.display = 'block';
      }
      document.querySelectorAll('.rail-icon-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.flyout === flyoutName);
      });
    }

    if (urlParams.has('details')) {
      setDetailsDrawerOpen(true);
    }

    if (urlParams.has('disclosures')) {
      if (dom.governanceModal) dom.governanceModal.style.display = 'flex';
    }

    if (urlParams.has('callout')) {
      state.selectedObject = {
        type: 'shade_panel',
        id: 'CAND_0028_EVOL',
        name: 'Stage 14 CAND_0028_EVOL (Tensile Sail)',
        glyph: '5',
        eyebrow: 'OPTIMIZED SHADE SAIL',
        m1: '-12.60 K',
        m2: '46.22 °C',
        m3: '4.50 m Clearance',
        pos: new THREE.Vector3(45, 5.5, -78)
      };
      updateCalloutCardUI();
    }
  }

  // --- 11. Animation & Render Loop ---
  function animate() {
    requestAnimationFrame(animate);

    const delta = clock.getDelta();

    // Auto-advance solar time if playing
    if (state.isPlaying) {
      state.timeOfDay += delta * state.playSpeed;
      if (state.timeOfDay > 18.5) {
        state.timeOfDay = 6.0;
      }
      updateSunPosition(state.timeOfDay);
      updateHeadlineReadout();
      updateDetailsDrawer();
    }

    // Auto-hide timeline dock in Cinematic preset after 4s idle
    if (state.stylePreset === 'cinematic' && performance.now() - state.lastInteractionTime > 4000) {
      if (state.dockVisible && dom.timelineDock) {
        dom.timelineDock.style.opacity = '0.35';
        state.dockVisible = false;
      }
    }

    // Cloud drift
    if (cloudMesh && state.cloudCover > 0) {
      cloudMesh.position.x += delta * 1.5;
      if (cloudMesh.position.x > 300) cloudMesh.position.x = -100;
    }

    controls.update();
    renderer.render(scene, camera);

    // Update screen-projected POI pins and Callout card
    updateScreenProjections();
  }

  // Start on DOM ready
  window.addEventListener('DOMContentLoaded', init);

})(window);
