// ===== PARTICLES =====
(function spawnParticles() {
  const container = document.getElementById('particles');
  for (let i = 0; i < 30; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.cssText = `
      left: ${Math.random() * 100}%;
      --dur: ${6 + Math.random() * 8}s;
      --delay: ${Math.random() * 8}s;
      --drift: ${(Math.random() - 0.5) * 80}px;
      width: ${1 + Math.random() * 2}px;
      height: ${1 + Math.random() * 2}px;
      opacity: ${0.3 + Math.random() * 0.5};
    `;
    container.appendChild(p);
  }
})();

// ===== EMBERS =====
(function spawnEmbers() {
  const container = document.getElementById('embers');
  for (let i = 0; i < 20; i++) {
    const e = document.createElement('div');
    e.className = 'ember';
    e.style.cssText = `
      left: ${10 + Math.random() * 80}%;
      bottom: ${Math.random() * 30}%;
      --dur: ${4 + Math.random() * 6}s;
      --delay: ${Math.random() * 6}s;
      --dx: ${(Math.random() - 0.5) * 60}px;
      --dy: ${-(80 + Math.random() * 150)}px;
    `;
    container.appendChild(e);
  }
})();

// ===== POPUP =====
function openForm() {
  const overlay = document.getElementById('overlay');
  const modal   = document.getElementById('formModal');
  overlay.classList.add('active');
  modal.style.animation = 'none';
  void modal.offsetWidth; // force reflow
  modal.style.animation = 'modalIn 0.45s cubic-bezier(0.34, 1.56, 0.64, 1)';
  document.body.style.overflow = 'hidden';
}

function closeForm() {
  const overlay = document.getElementById('overlay');
  const modal   = document.getElementById('formModal');
  modal.style.animation = 'modalOut 0.25s ease forwards';
  setTimeout(() => {
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }, 230);
}

function closeOnOverlay(e) {
  if (e.target === document.getElementById('overlay')) closeForm();
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeForm();
});

// ===== PAY BUTTON =====
function handlePay() {
  alert('Redirecting to payment gateway...');
}