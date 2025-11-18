const cursor = document.getElementById("magic-cursor");
const particlesCanvas = document.getElementById("magic-particles");

const lerp = (start, end, amt) => (1 - amt) * start + amt * end;

// Magic wand cursor with SVG
if (cursor) {
  let targetX = 0;
  let targetY = 0;
  let currentX = 0;
  let currentY = 0;
  let mouseDown = false;

  // Create magic wand SVG
  cursor.innerHTML = `
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" style="overflow: visible;">
      <!-- Wand stick with gradient -->
      <line x1="6" y1="26" x2="18" y2="14" stroke="url(#wandGradient)" stroke-width="3" stroke-linecap="round"/>
      
      <!-- Star at the tip -->
      <g id="star" transform="translate(18, 10)">
        <path d="M0,-6 L1.5,-2 L6,-1.5 L2,2 L3,6.5 L0,4 L-3,6.5 L-2,2 L-6,-1.5 L-1.5,-2 Z" 
              fill="url(#starGradient)" stroke="#fbbf24" stroke-width="0.5">
          <animateTransform attributeName="transform" type="rotate" from="0 0 0" to="360 0 0" 
                            dur="4s" repeatCount="indefinite"/>
        </path>
      </g>
      
      <!-- Sparkles around the star -->
      <g id="sparkles">
        <circle cx="22" cy="6" r="1.5" fill="#38bdf8" opacity="0.9">
          <animate attributeName="opacity" values="0.3;1;0.3" dur="1.2s" repeatCount="indefinite"/>
          <animate attributeName="r" values="1;2;1" dur="1.2s" repeatCount="indefinite"/>
        </circle>
        <circle cx="25" cy="12" r="1" fill="#f472b6" opacity="0.8">
          <animate attributeName="opacity" values="0.2;0.9;0.2" dur="1.8s" repeatCount="indefinite"/>
        </circle>
        <circle cx="20" cy="4" r="1.2" fill="#fbbf24" opacity="0.7">
          <animate attributeName="opacity" values="0.4;1;0.4" dur="1.5s" repeatCount="indefinite"/>
        </circle>
        <circle cx="14" cy="8" r="0.8" fill="#38bdf8" opacity="0.6">
          <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2s" repeatCount="indefinite"/>
        </circle>
      </g>
      
      <defs>
        <linearGradient id="wandGradient" x1="6" y1="26" x2="18" y2="14">
          <stop offset="0%" stop-color="#6366f1"/>
          <stop offset="50%" stop-color="#8b5cf6"/>
          <stop offset="100%" stop-color="#a855f7"/>
        </linearGradient>
        <radialGradient id="starGradient">
          <stop offset="0%" stop-color="#fef3c7"/>
          <stop offset="50%" stop-color="#fbbf24"/>
          <stop offset="100%" stop-color="#f59e0b"/>
        </radialGradient>
      </defs>
    </svg>
  `;

  const render = () => {
    currentX = lerp(currentX, targetX, 0.15);
    currentY = lerp(currentY, targetY, 0.15);
    
    const scale = mouseDown ? 1.3 : 1;
    const rotate = mouseDown ? 25 : 0;
    
    cursor.style.transform = `translate(${currentX - 16}px, ${currentY - 16}px) scale(${scale}) rotate(${rotate}deg)`;
    requestAnimationFrame(render);
  };

  window.addEventListener("mousemove", (event) => {
    targetX = event.clientX;
    targetY = event.clientY;
  });

  window.addEventListener("mousedown", () => {
    mouseDown = true;
    // Add click sparkle effect
    createClickSparkle(targetX, targetY);
  });

  window.addEventListener("mouseup", () => {
    mouseDown = false;
  });

  render();
}

// Click sparkle effect
function createClickSparkle(x, y) {
  const sparkle = document.createElement('div');
  sparkle.className = 'click-sparkle';
  sparkle.style.left = x + 'px';
  sparkle.style.top = y + 'px';
  document.body.appendChild(sparkle);
  
  setTimeout(() => sparkle.remove(), 600);
}

// Particle system
if (particlesCanvas) {
  const ctx = particlesCanvas.getContext("2d");
  const particles = Array.from({ length: 60 }, () => ({
    x: Math.random() * window.innerWidth,
    y: Math.random() * window.innerHeight,
    radius: Math.random() * 2 + 0.5,
    speed: Math.random() * 0.5 + 0.2,
    drift: (Math.random() - 0.5) * 0.4,
    opacity: Math.random() * 0.5 + 0.3,
  }));

  const resize = () => {
    particlesCanvas.width = window.innerWidth;
    particlesCanvas.height = window.innerHeight;
  };

  const draw = () => {
    ctx.clearRect(0, 0, particlesCanvas.width, particlesCanvas.height);
    
    particles.forEach((particle) => {
      particle.y -= particle.speed;
      particle.x += particle.drift;
      
      if (particle.y < -10) {
        particle.y = particlesCanvas.height + 10;
        particle.x = Math.random() * particlesCanvas.width;
      }
      if (particle.x < -10) particle.x = particlesCanvas.width + 10;
      if (particle.x > particlesCanvas.width + 10) particle.x = -10;
      
      // Gradient particles
      const gradient = ctx.createRadialGradient(
        particle.x, particle.y, 0,
        particle.x, particle.y, particle.radius * 2
      );
      gradient.addColorStop(0, `rgba(168, 85, 247, ${particle.opacity})`);
      gradient.addColorStop(0.5, `rgba(56, 189, 248, ${particle.opacity * 0.5})`);
      gradient.addColorStop(1, 'rgba(168, 85, 247, 0)');
      
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(particle.x, particle.y, particle.radius * 2, 0, Math.PI * 2);
      ctx.fill();
    });
    
    requestAnimationFrame(draw);
  };

  resize();
  window.addEventListener("resize", resize);
  draw();
}
