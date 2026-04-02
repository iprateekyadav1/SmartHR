/* ═══════════════════════════════════════════════════════════════
   SmartHR — 3D Department Visualization
   Renders an interactive sphere with department nodes, orbiting
   rings, and connection lines. GPU-only (will-change: transform).
═══════════════════════════════════════════════════════════════ */

window.SmartHRGlobe = (function () {
  'use strict';

  var renderer, scene, camera, animId;
  var sphereMesh, ringMesh1, ringMesh2;
  var nodeMeshes = [];
  var labelData  = [];
  var mouse = { x: 0, y: 0 };
  var isDragging = false, prevMouse = { x: 0, y: 0 };
  var rotY = 0, rotX = 0.2;

  var DEPT_COLORS = [
    0x00d4ff, 0x7c3aed, 0x10b981, 0xf59e0b,
    0xef4444, 0x06b6d4, 0xec4899, 0x8b5cf6
  ];

  function fibonacciSphere(count) {
    var pts = [];
    var phi = Math.PI * (3 - Math.sqrt(5));
    for (var i = 0; i < count; i++) {
      var y   = 1 - (i / (count - 1)) * 2;
      var r   = Math.sqrt(1 - y * y);
      var th  = phi * i;
      pts.push(new THREE.Vector3(Math.cos(th) * r, y, Math.sin(th) * r));
    }
    return pts;
  }

  function buildScene(canvas, departments) {
    var W = canvas.clientWidth;
    var H = canvas.clientHeight;

    renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(W, H);
    renderer.setClearColor(0x000000, 0);

    scene  = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(50, W / H, 0.1, 500);
    camera.position.z = 3.2;

    /* ── Wireframe globe ── */
    var sGeo = new THREE.IcosahedronGeometry(1, 3);
    var sMat = new THREE.MeshBasicMaterial({
      color: 0x00d4ff,
      wireframe: true,
      transparent: true,
      opacity: 0.07
    });
    sphereMesh = new THREE.Mesh(sGeo, sMat);
    scene.add(sphereMesh);

    /* ── Inner glow sphere ── */
    var innerGeo = new THREE.SphereGeometry(0.95, 32, 32);
    var innerMat = new THREE.MeshBasicMaterial({
      color: 0x00d4ff,
      transparent: true,
      opacity: 0.02
    });
    scene.add(new THREE.Mesh(innerGeo, innerMat));

    /* ── Orbiting rings ── */
    var r1Geo = new THREE.TorusGeometry(1.35, 0.004, 8, 100);
    var r1Mat = new THREE.MeshBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.25 });
    ringMesh1 = new THREE.Mesh(r1Geo, r1Mat);
    ringMesh1.rotation.x = Math.PI / 2.4;
    scene.add(ringMesh1);

    var r2Geo = new THREE.TorusGeometry(1.55, 0.003, 8, 100);
    var r2Mat = new THREE.MeshBasicMaterial({ color: 0x7c3aed, transparent: true, opacity: 0.18 });
    ringMesh2 = new THREE.Mesh(r2Geo, r2Mat);
    ringMesh2.rotation.x = -Math.PI / 3;
    ringMesh2.rotation.z = Math.PI / 5;
    scene.add(ringMesh2);

    /* ── Department nodes ── */
    var pts = fibonacciSphere(departments.length);
    var center = new THREE.Vector3(0, 0, 0);

    departments.forEach(function (dept, idx) {
      var pos   = pts[idx].multiplyScalar(1.02);
      var color = DEPT_COLORS[idx % DEPT_COLORS.length];
      var size  = 0.042 + Math.min(dept.count / 200, 0.06);

      /* Node sphere */
      var nGeo = new THREE.SphereGeometry(size, 12, 12);
      var nMat = new THREE.MeshBasicMaterial({ color: color });
      var node = new THREE.Mesh(nGeo, nMat);
      node.position.copy(pos);
      scene.add(node);
      nodeMeshes.push({ mesh: node, color: color, dept: dept });

      /* Glow halo */
      var gGeo = new THREE.SphereGeometry(size * 2.2, 10, 10);
      var gMat = new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.12 });
      var glow = new THREE.Mesh(gGeo, gMat);
      glow.position.copy(pos);
      scene.add(glow);

      /* Connection line to center */
      var points = [center.clone(), pos.clone()];
      var linGeo = new THREE.BufferGeometry().setFromPoints(points);
      var linMat = new THREE.LineBasicMaterial({ color: color, transparent: true, opacity: 0.15 });
      scene.add(new THREE.Line(linGeo, linMat));

      /* Label data for canvas overlay */
      labelData.push({ pos: pos.clone(), label: dept.name, count: dept.count, color: color });
    });

    /* ── Ambient stars ── */
    var stGeo = new THREE.BufferGeometry();
    var stPos = new Float32Array(600 * 3);
    for (var s = 0; s < 600; s++) {
      stPos[s * 3]     = (Math.random() - 0.5) * 12;
      stPos[s * 3 + 1] = (Math.random() - 0.5) * 12;
      stPos[s * 3 + 2] = (Math.random() - 0.5) * 12;
    }
    stGeo.setAttribute('position', new THREE.BufferAttribute(stPos, 3));
    var stMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.012, transparent: true, opacity: 0.3 });
    scene.add(new THREE.Points(stGeo, stMat));
  }

  function hexToCSS(hex) {
    return '#' + hex.toString(16).padStart(6, '0');
  }

  function toScreenPos(vec3, W, H) {
    var v = vec3.clone().project(camera);
    return {
      x: (v.x + 1) / 2 * W,
      y: (-v.y + 1) / 2 * H
    };
  }

  function animate(labelCanvas) {
    animId = requestAnimationFrame(function () { animate(labelCanvas); });

    rotY += 0.0025;
    sphereMesh.rotation.y = rotY;
    sphereMesh.rotation.x = rotX;

    /* Sync nodes with globe rotation */
    nodeMeshes.forEach(function (n) { n.mesh.rotation.copy(sphereMesh.rotation); });

    ringMesh1.rotation.z += 0.004;
    ringMesh2.rotation.z -= 0.003;

    renderer.render(scene, camera);

    /* Draw labels on 2D overlay canvas */
    if (labelCanvas) {
      var ctx = labelCanvas.getContext('2d');
      var W   = labelCanvas.width;
      var H   = labelCanvas.height;
      ctx.clearRect(0, 0, W, H);

      labelData.forEach(function (ld) {
        /* Transform label position by globe rotation */
        var cos = Math.cos(rotY), sin = Math.sin(rotY);
        var rx  = ld.pos.x * cos - ld.pos.z * sin;
        var rz  = ld.pos.x * sin + ld.pos.z * cos;
        var rotated = new THREE.Vector3(rx, ld.pos.y, rz);
        var s = toScreenPos(rotated, W, H);

        /* Only show front-facing labels */
        if (rz < 0) return;

        ctx.font = 'bold 10px Inter, sans-serif';
        ctx.textAlign = 'center';

        /* Background pill */
        var text  = ld.label + ' (' + ld.count + ')';
        var tw    = ctx.measureText(text).width + 14;
        var th    = 18;
        ctx.fillStyle = 'rgba(10,15,30,0.7)';
        ctx.beginPath();
        ctx.roundRect(s.x - tw / 2, s.y - th - 6, tw, th, 4);
        ctx.fill();

        ctx.fillStyle = hexToCSS(ld.color);
        ctx.fillText(text, s.x, s.y - 10);
      });
    }
  }

  function init(canvasId, labelCanvasId, departments) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || typeof THREE === 'undefined') return;
    if (!departments || !departments.length) return;

    buildScene(canvas, departments);

    var labelCanvas = document.getElementById(labelCanvasId);
    if (labelCanvas) {
      labelCanvas.width  = canvas.clientWidth;
      labelCanvas.height = canvas.clientHeight;
    }

    animate(labelCanvas);

    /* Drag to rotate */
    canvas.addEventListener('mousedown', function (e) {
      isDragging = true;
      prevMouse = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mouseup',  function () { isDragging = false; });
    window.addEventListener('mousemove', function (e) {
      if (!isDragging) return;
      var dx = e.clientX - prevMouse.x;
      var dy = e.clientY - prevMouse.y;
      rotY += dx * 0.006;
      rotX = Math.max(-0.6, Math.min(0.6, rotX + dy * 0.006));
      prevMouse = { x: e.clientX, y: e.clientY };
    });

    /* Touch support */
    canvas.addEventListener('touchstart', function (e) {
      isDragging = true;
      prevMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }, { passive: true });

    canvas.addEventListener('touchmove', function (e) {
      if (!isDragging) return;
      var dx = e.touches[0].clientX - prevMouse.x;
      var dy = e.touches[0].clientY - prevMouse.y;
      rotY += dx * 0.006;
      rotX = Math.max(-0.6, Math.min(0.6, rotX + dy * 0.006));
      prevMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }, { passive: true });

    canvas.addEventListener('touchend', function () { isDragging = false; });
  }

  function destroy() {
    if (animId) cancelAnimationFrame(animId);
  }

  return { init: init, destroy: destroy };
})();
