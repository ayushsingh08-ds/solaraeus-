/**
 * SOLARAEUS 3D: GPU Heatmap Shader Material (heatmapShader.js)
 * 
 * Implements GPU-accelerated colormapping with mask-weighted bilinear interpolation
 * and strict building boundary clipping to eliminate pixel blockiness and bleeding.
 */

(function (window) {
  'use strict';

  const vertexShader = `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `;

  const fragmentShader = `
    precision highp float;
    varying vec2 vUv;

    uniform sampler2D u_dataTexture;
    uniform sampler2D u_maskTexture;
    uniform sampler2D u_lutTexture;
    uniform vec2 u_resolution; // (nx, ny)
    uniform float u_minVal;
    uniform float u_maxVal;
    uniform float u_opacity;
    uniform float u_contourEnabled;
    uniform float u_contourStep;

    void main() {
      vec2 uv = vUv;

      // Sample mask directly at fragment center
      float centerMask = texture2D(u_maskTexture, uv).r;
      if (centerMask < 0.2) {
        discard; // Strictly transparent inside building footprints
      }

      vec2 texelSize = 1.0 / u_resolution;
      vec2 coord = uv * u_resolution - 0.5;
      vec2 f = fract(coord);
      vec2 baseUv = (floor(coord) + 0.5) * texelSize;

      // 4 neighbor texels
      float m00 = texture2D(u_maskTexture, baseUv).r;
      float m10 = texture2D(u_maskTexture, baseUv + vec2(texelSize.x, 0.0)).r;
      float m01 = texture2D(u_maskTexture, baseUv + vec2(0.0, texelSize.y)).r;
      float m11 = texture2D(u_maskTexture, baseUv + texelSize).r;

      float v00 = texture2D(u_dataTexture, baseUv).r;
      float v10 = texture2D(u_dataTexture, baseUv + vec2(texelSize.x, 0.0)).r;
      float v01 = texture2D(u_dataTexture, baseUv + vec2(0.0, texelSize.y)).r;
      float v11 = texture2D(u_dataTexture, baseUv + texelSize).r;

      // Bilinear weights
      float w00 = (1.0 - f.x) * (1.0 - f.y);
      float w10 = f.x * (1.0 - f.y);
      float w01 = (1.0 - f.x) * f.y;
      float w11 = f.x * f.y;

      // Mask-weighted interpolation: Σ(w·v·m) / Σ(w·m)
      float weightSum = w00 * m00 + w10 * m10 + w01 * m01 + w11 * m11;
      if (weightSum < 0.001) {
        discard;
      }

      float valNorm = (w00 * m00 * v00 + w10 * m10 * v10 + w01 * m01 * v01 + w11 * m11 * v11) / weightSum;
      float physicalVal = u_minVal + valNorm * (u_maxVal - u_minVal);

      // Map to 256x1 colormap LUT
      float lutU = clamp(valNorm, 0.0, 1.0);
      vec4 lutColor = texture2D(u_lutTexture, vec2(lutU, 0.5));

      // Optional subtle contour lines at break intervals
      if (u_contourEnabled > 0.5 && u_contourStep > 0.0) {
        float cDist = mod(physicalVal, u_contourStep);
        if (cDist < 0.08 || cDist > (u_contourStep - 0.08)) {
          lutColor.rgb = mix(lutColor.rgb, vec3(1.0, 1.0, 1.0), 0.35);
        }
      }

      gl_FragColor = vec4(lutColor.rgb, lutColor.a * u_opacity);
    }
  `;

  function createHeatmapMaterial(params) {
    if (typeof THREE === 'undefined') return null;

    const material = new THREE.ShaderMaterial({
      vertexShader: vertexShader,
      fragmentShader: fragmentShader,
      uniforms: {
        u_dataTexture: { value: params.dataTexture },
        u_maskTexture: { value: params.maskTexture },
        u_lutTexture: { value: params.lutTexture },
        u_resolution: { value: new THREE.Vector2(params.nx, params.ny) },
        u_minVal: { value: params.minVal || 30.0 },
        u_maxVal: { value: params.maxVal || 50.0 },
        u_opacity: { value: params.opacity !== undefined ? params.opacity : 0.75 },
        u_contourEnabled: { value: params.contourEnabled ? 1.0 : 0.0 },
        u_contourStep: { value: params.contourStep || 2.0 }
      },
      transparent: true,
      depthWrite: false,
      polygonOffset: true,
      polygonOffsetFactor: -1.0,
      polygonOffsetUnits: -4.0,
      toneMapped: false // Never alter scientific data with filmic tone mapping
    });

    return material;
  }

  window.SOLARAEUS_HEATMAP_SHADER = {
    vertexShader,
    fragmentShader,
    createHeatmapMaterial
  };

})(window);
