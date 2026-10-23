(function(){
  const css = `
  #wt-dim{position:fixed;pointer-events:none;border-radius:16px;box-shadow:0 0 0 9999px rgba(14,10,46,.40),0 0 0 4px #FF006E,0 0 30px 8px rgba(255,0,110,.45);z-index:50}
  #wt-cap{position:fixed;bottom:24px;z-index:60;background:rgba(255,255,255,.98);border-radius:20px;box-shadow:0 12px 34px rgba(20,30,60,.32);padding:16px 26px 16px 16px;display:flex;gap:16px;align-items:center;width:640px}
  #wt-cap .n{width:56px;height:56px;border-radius:50%;background:#FF006E;color:#fff;display:grid;place-items:center;font:800 26px "Inter Display";flex:none}
  #wt-cap .e{font:700 13px Inter;letter-spacing:.08em;text-transform:uppercase;color:#FF006E}
  #wt-cap .t{font:800 27px "Inter Display";color:#13201A;line-height:1.15}
  #wt-cap .s{font:500 17px Inter;color:#5A6A61;margin-top:3px}
  #wt-cur{position:fixed;z-index:70;width:30px;height:30px;pointer-events:none;filter:drop-shadow(0 3px 4px rgba(0,0,0,.35))}
  #wt-rip{position:fixed;z-index:69;border-radius:50%;border:4px solid #FF006E;pointer-events:none}`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  const dim = Object.assign(document.createElement('div'), { id: 'wt-dim' });
  const cap = Object.assign(document.createElement('div'), { id: 'wt-cap' }); cap.innerHTML = '<div class="n"></div><div><div class="e">TerraScout Console</div><div class="t"></div><div class="s"></div></div>';
  const cur = Object.assign(document.createElement('div'), { id: 'wt-cur' }); cur.innerHTML = '<svg viewBox="0 0 24 24" width="30" height="30"><path d="M3 2l17 10-7.5 1.6L9 21z" fill="#fff" stroke="#13201A" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  const rip = Object.assign(document.createElement('div'), { id: 'wt-rip' });
  document.body.append(dim, cap, rip, cur);

  const rowTop = document.querySelector('.row3').getBoundingClientRect().top + scrollY - 70;
  const STEPS = [
    [0, 4.2, '.kpis', 'Headline indicators', 'Survival, care needed, species, shade cooling and audit status', 'left', 0],
    [4.2, 10.6, '.main > .panel', 'Live patrol map', 'Run a patrol and watch saplings update as the rover checks them', 'right', 175],
    [10.6, 15.2, '.side > .panel', 'Maintenance tickets', 'Flagged saplings become tickets, with the server’s YOLO result attached', 'left', 175],
    [15.2, 19.2, '.row3 > .panel:nth-child(1)', 'Biodiversity', 'Bird detections wait for an ecologist to verify them', 'right', rowTop],
    [19.2, 22.2, '.row3 > .panel:nth-child(2)', 'Heat transect', 'Each reading is compared with the reference station at the same moment', 'left', rowTop],
    [22.2, 99, '.row3 > .panel:nth-child(3)', 'Audit trail', 'Edit a past record and the chain shows exactly where it broke', 'left', rowTop]
  ];
  const CLICKS = [[4.9, '#speedBtn'], [5.4, '#speedBtn'], [6.0, '#runBtn'], [13.4, 'button[data-id="TK-119"]'], [17.6, 'button[data-v="Common Iora"]'], [23.4, '#tamperBtn'], [25.2, '#verifyBtn']];
  const fired = new Set();
  let sy = 0, rect = null, cx = innerWidth * .62, cy = innerHeight * .55, lastClick = -9, lastStep = -1;
  const lerp = (a, b, k) => a + (b - a) * k;
  const center = sel => { const e = document.querySelector(sel); if (!e) return null; const r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
  window.WT = { clicks: CLICKS.map(c => c[0]), steps: STEPS.map(s => s[0]), render(t){
    const si = STEPS.findIndex(s => t >= s[0] && t < s[1]); const S = STEPS[si];
    sy = lerp(sy, S[6], .12); scrollTo(0, Math.round(sy));
    const el = document.querySelector(S[2]); const r = el.getBoundingClientRect(); const tgt = [r.left - 8, r.top - 8, r.width + 16, r.height + 16];
    rect = rect ? rect.map((v, i) => lerp(v, tgt[i], .2)) : tgt;
    Object.assign(dim.style, { left: rect[0] + 'px', top: rect[1] + 'px', width: rect[2] + 'px', height: rect[3] + 'px' });
    if (si !== lastStep) { cap.querySelector('.n').textContent = si + 1; cap.querySelector('.t').textContent = S[3]; cap.querySelector('.s').textContent = S[4]; lastStep = si; }
    cap.style.left = S[5] === 'left' ? '24px' : ''; cap.style.right = S[5] === 'right' ? '24px' : '';
    const k = Math.min(1, (t - S[0]) / .35); cap.style.opacity = k; cap.style.transform = `translateY(${(1 - k) * 18}px)`;
    // cursor
    const next = CLICKS.find(c => c[0] > t - .05 && c[0] - t < 1.0);
    let target = next && center(next[1]); if (!target) target = [r.left + r.width * .72, r.top + Math.min(r.height * .3, 160)];
    cx = lerp(cx, target[0], .16); cy = lerp(cy, target[1], .16);
    Object.assign(cur.style, { left: (cx - 4) + 'px', top: (cy - 3) + 'px' });
    CLICKS.forEach(([ct, sel]) => { if (t >= ct && !fired.has(ct)) { fired.add(ct); const e = document.querySelector(sel); if (e) e.click(); lastClick = ct; } });
    const rk = (t - lastClick) / .45; if (rk >= 0 && rk < 1) { const d = 14 + rk * 46; Object.assign(rip.style, { display: 'block', left: (cx - d / 2) + 'px', top: (cy - d / 2) + 'px', width: d + 'px', height: d + 'px', opacity: 1 - rk }); } else rip.style.display = 'none';
  } };
})();
