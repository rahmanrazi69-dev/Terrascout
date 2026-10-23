import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 44100
TOTAL = 98.5
N = int(SR * TOTAL)
rng = np.random.default_rng(7)
WB = 62.5          # walkthrough starts (final timeline)
CE = 26.5          # end segment offset: final = scene_t + CE for scene_t >= 63

def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], btype='band', fs=SR, output='sos'), x)
def lp(x, f, order=2): return sosfilt(butter(order, f, btype='low', fs=SR, output='sos'), x)
def hp(x, f, order=2): return sosfilt(butter(order, f, btype='high', fs=SR, output='sos'), x)
def tt(d): return np.arange(int(d * SR)) / SR
def env_ad(n, a, d):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d); return e
def place(buf, sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= len(buf) or i + len(sig) <= 0: return
    s = sig * gain; j0 = max(0, -i); i = max(0, i); s = s[j0:]; n = min(len(s), len(buf) - i)
    l, r = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
    buf[i:i + n, 0] += s[:n] * l * 1.414; buf[i:i + n, 1] += s[:n] * r * 1.414
def reverb(x, secs=1.6, mix=.25, seed=1):
    r = np.random.default_rng(seed); n = int(secs * SR); t = np.arange(n) / SR
    out = np.zeros_like(x)
    for ch in range(2):
        ir = r.standard_normal(n) * np.exp(-t * 4.2 / secs); ir = lp(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
        out[:, ch] = fftconvolve(x[:, ch], ir)[:len(x)]
    return x * (1 - mix) + out * mix
def note(f): return 440 * 2 ** ((f - 69) / 12)

# ---------------- MUSIC (original, generated here) ----------------
mus = np.zeros((N, 2))
BPM = 96; BEAT = 60 / BPM; BAR = BEAT * 4
# I-V-vi-IV in D: D, A, Bm, G (midi roots)
CH = [(50, [62, 66, 69]), (45, [61, 64, 69]), (47, [62, 66, 71]), (43, [62, 67, 71])]
nbars = int(TOTAL / BAR) + 1
for b in range(nbars):
    t0 = b * BAR; root, tri = CH[b % 4]
    # pad
    d = BAR + .6; t = tt(d); e = np.minimum(1, t / .5) * np.minimum(1, (d - t) / .6)
    pad = np.zeros_like(t)
    for m in tri + [tri[0] - 12]:
        for det in (-.003, 0, .003):
            ph = 2 * np.pi * note(m) * (1 + det) * t; pad += (2 * ((ph / (2 * np.pi)) % 1) - 1) * .12
    pad = lp(pad, 1400) * e
    place(mus, pad, t0, .16 if b < 2 else .13)
    # pluck arpeggio from bar 2
    if b >= 2:
        seq = [tri[0], tri[1], tri[2], tri[1] + 12, tri[2], tri[1], tri[0] + 12, tri[2]]
        for k, m in enumerate(seq):
            d = .5; t = tt(d); f = note(m + 12)
            s = (np.sin(2 * np.pi * f * t) + .35 * np.sin(4 * np.pi * f * t) + .12 * np.sin(6 * np.pi * f * t)) * env_ad(len(t), .004, .16)
            place(mus, s, t0 + k * BEAT / 2, .11, pan=(-.35 if k % 2 else .35))
    # bass + drums from bar 4
    if b >= 4:
        for off, dur in ((0, .55), (1.5 * BEAT, .3), (2 * BEAT, .55), (3.5 * BEAT, .25)):
            t = tt(dur); f = note(root - 12 + 12 if root < 45 else root - 12 + 12)
            f = note(root)
            s = (np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t)) * env_ad(len(t), .01, dur * .6)
            place(mus, lp(s, 600), t0 + off, .28)
        for off in (0, 2 * BEAT):
            t = tt(.3); f = 45 + 80 * np.exp(-t * 28); s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), .002, .12)
            place(mus, s, t0 + off, .32)
        for k in range(4):
            t = tt(.06); s = hp(rng.standard_normal(len(t)), 7000) * env_ad(len(t), .001, .018)
            place(mus, s, t0 + k * BEAT + BEAT / 2, .07, pan=.2)
        if b % 2 == 1:
            t = tt(.18); s = bp(rng.standard_normal(len(t)), 1500, 5000) * env_ad(len(t), .002, .06)
            place(mus, s, t0 + 3 * BEAT, .06, pan=-.1)
mus = reverb(mus, 1.8, .28, 3)
# fades
fi = np.minimum(1, np.arange(N) / (SR * 1.5)); fo = np.clip((TOTAL - np.arange(N) / SR) / 4.5, 0, 1)
mus *= (fi * fo)[:, None]
mus /= np.sqrt((mus ** 2).mean()) + 1e-9
mus *= 10 ** (-27 / 20)    # quiet background bed

# ---------------- SFX ----------------
sfx = np.zeros((N, 2))
def sine_blip(f, d=.12, dec=.05, h=0.0):
    t = tt(d); return (np.sin(2 * np.pi * f * t) + h * np.sin(4 * np.pi * f * t)) * env_ad(len(t), .003, dec)
def chime(fs, gap=.09, gain=.3, t0=0, pan=0):
    for i, f in enumerate(fs):
        t = tt(.9); s = (np.sin(2 * np.pi * f * t) + .25 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 12)) * env_ad(len(t), .003, .28)
        place(sfx, s, t0 + i * gap, gain, pan)
def whoosh(t0, d=.5, gain=.12, lo=400, hi=4000):
    t = tt(d); n = rng.standard_normal(len(t)); e = np.sin(np.pi * t / d) ** 2
    s = bp(n, lo, hi) * e; place(sfx, s, t0, gain)
def click(t0, gain=.35):
    for k, dt in enumerate((0, .045)):
        t = tt(.02); s = hp(rng.standard_normal(len(t)), 2500) * env_ad(len(t), .0005, .004); place(sfx, s, t0 + dt, gain * (1 if k == 0 else .6))
def servo(t0, d, f0, f1, gain=.09):
    t = tt(d); f = np.linspace(f0, f1, len(t)); ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sign(np.sin(ph)) * (1 + .3 * np.sin(2 * np.pi * 55 * t)); s = lp(s, 2200) * np.minimum(1, np.minimum(t / .05, (d - t) / .08))
    place(sfx, s, t0, gain)

# rover motion (replicates uAt from the scene)
KU = [[0, 0], [6, 0], [11, .08], [13.2, .12], [17, .12], [20.3, .2], [28.5, .2], [32, .38], [40.5, .38], [53, .71], [57.5, 1], [72, 1]]
def sm(x): x = min(1, max(0, x)); return x * x * x * (x * (x * 6 - 15) + 10)
def uAt(t):
    for i in range(len(KU) - 1):
        t0, u0 = KU[i]; t1, u1 = KU[i + 1]
        if t <= t1:
            k = (t - t0) / (t1 - t0); e = (k + (sm(k) - k) * .35) if (u1 - u0) > .2 else sm(k); return u0 + (u1 - u0) * e
    return 1
LEN = 150.0
ts = np.arange(0, 63, .01); us = np.array([uAt(x) for x in ts]); v = np.gradient(us, ts) * LEN
tS = np.arange(int(63 * SR)) / SR; vS = np.interp(tS, ts, v); vn = np.clip(vS / 3.0, 0, 1)
near = np.interp(tS, [0, 5.5, 6.3, 52.6, 53.6, 63], [.25, .25, 1, 1, .4, .4])
f = 62 + 30 * vn; ph = 2 * np.pi * np.cumsum(f) / SR
hum = (np.sin(ph) + .5 * np.sin(2 * ph) + .3 * np.sin(3 * ph) + .2 * np.sign(np.sin(4 * ph)) * .5)
hum = lp(hum, 700)
grit = bp(rng.standard_normal(len(tS)), 250, 2400) * (1 + .6 * np.sin(2 * np.pi * 13 * tS))
whine = np.sin(2 * np.pi * np.cumsum(380 + 260 * vn) / SR) * .25
mot = (hum * .55 + grit * .35 + whine * .3) * (np.clip(vn * 1.6, 0, 1) ** 1.2) * near
sfx[:len(mot), 0] += mot * .22; sfx[:len(mot), 1] += mot * .22

# park ambience: wind + distant birds (rover scenes and end)
def ambience(a, b, g=1.0):
    t = tt(b - a); w = lp(rng.standard_normal(len(t)), 500) * (0.6 + .4 * np.sin(2 * np.pi * .13 * t)); w *= np.minimum(1, np.minimum(t / 1, (b - a - t) / 1))
    place(sfx, w, a, .03 * g)
    k = a + .5
    while k < b - .5:
        f0 = rng.uniform(2800, 4800); d = rng.uniform(.05, .12); t = tt(d); fr = f0 * (1 + .25 * np.sin(np.pi * t / d))
        s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.sin(np.pi * t / d) ** 2
        for r in range(int(rng.integers(1, 4))): place(sfx, s, k + r * (d + .04), .025 * g, pan=rng.uniform(-.8, .8))
        k += rng.uniform(.9, 2.6)
ambience(0, 63); ambience(89.5, 98.5, .8)

# title + chapters
whoosh(0.15, .9, .16, 300, 3000); chime([1175, 1568, 2349], .11, .16, 1.0)
for c in (6.3, 12.4, 29.4, 41.4, 53.4): whoosh(c - .1, .45, .09, 600, 5000)
# dock departure: power-up
servo(6.2, .5, 200, 520, .06)
# sapling TS-06 scan
servo(13.4, .6, 420, 640); servo(16.2, .6, 640, 420)
def scan_window(a, b):
    k = a
    while k < b:
        place(sfx, sine_blip(1500, .3, .09, .3), k, .14); k += .55
    t = tt(b - a); s = bp(rng.standard_normal(len(t)), 2500, 7000) * (.5 + .5 * np.sin(2 * np.pi * 1.8 * t)) * np.minimum(1, np.minimum(t / .3, (b - a - t) / .3))
    place(sfx, s, a, .035)
scan_window(14.0, 16.2); chime([1047, 1568], .1, .18, 15.6)
# TS-07
servo(20.6, .6, 420, 640); servo(27.2, .6, 640, 420)
scan_window(21.2, 27.2)
for i in range(12): place(sfx, sine_blip(600 + i * 28, .08, .03), 22.2 + i * .15, .1)
for k, f0 in enumerate((988, 784)):
    t = tt(.3); s = (2 * np.abs(2 * ((f0 * t) % 1) - 1) - 1) * env_ad(len(t), .005, .12); place(sfx, lp(s, 3500), 24.2 + k * .22, .2)
for k, f0 in enumerate((988, 784)):
    t = tt(.3); s = (2 * np.abs(2 * ((f0 * t) % 1) - 1) - 1) * env_ad(len(t), .005, .12); place(sfx, lp(s, 3500), 24.75 + k * .22, .1)
chime([1319, 1661], .05, .2, 25.25)
# sound station: mic raise, birdsong, detection
servo(31.8, .8, 300, 520, .07); servo(40.0, .6, 520, 300, .06)
def whistle(f0, f1, d, vib=8):
    t = tt(d); fr = np.linspace(f0, f1, len(t)) * (1 + .012 * np.sin(2 * np.pi * vib * t)); s = np.sin(2 * np.pi * np.cumsum(fr) / SR) + .15 * np.sin(4 * np.pi * np.cumsum(fr) / SR)
    return s * np.sin(np.pi * t / d) ** .8
bird = np.zeros((int(6 * SR), 2)); bt = 0.05
phrases = [[(2600, 3400, .42), (3300, 2500, .18)], [(3000, 3000, .1), (3100, 3100, .1), (2700, 3800, .5)], [(3600, 2600, .25), (2600, 3300, .35)], [(2400, 3500, .55), (3400, 2900, .15), (2900, 2900, .12)]]
for rep in range(5):
    ph = phrases[rep % len(phrases)]; k = bt
    for (a, b2, d) in ph: place(bird, whistle(a, b2, d), k, .38, .25); k += d + .05
    bt = k + .55
bird = reverb(bird, 1.0, .3, 9)
sfx[int(33 * SR):int(33 * SR) + len(bird)] += bird[:min(len(bird), N - int(33 * SR))]
chime([784, 1175], .12, .22, 35.6, -.2); chime([1047, 1319, 1568], .08, .18, 37.4)
for i in range(12):
    t = tt(.05); s = lp(rng.standard_normal(len(t)), 1800) * env_ad(len(t), .004, .02); place(sfx, s, 38.6 + i * .085, .12 * (1 - i / 14), .3)
# heat tiles
heat_u = np.arange(.45, .7001, .0125)
tgrid = np.arange(41, 53, .02); ugrid = np.array([uAt(x) for x in tgrid])
for u in heat_u:
    idx = np.argmax(ugrid >= u) if (ugrid >= u).any() else len(tgrid) - 1; tp = tgrid[idx]
    shade = u > .56; t = tt(.1); fr = np.linspace(380 if shade else 520, 700 if shade else 900, len(t)); s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * env_ad(len(t), .003, .035)
    place(sfx, s, tp, .09)
# docking + upload + audit
servo(57.4, .7, 260, 820, .06)
for i in range(4): click(55.6 + i * .75, .25); place(sfx, sine_blip(1760, .1, .03), 55.62 + i * .75, .06)
pent = [72, 74, 76, 79, 81, 84, 86, 88, 91, 93, 96, 98, 100, 103]
for i in range(14): place(sfx, sine_blip(note(pent[i]), .1, .04, .2), 57.8 + i * .33, .07, pan=(-.3 if i % 2 else .3))
chime([1047, 1319, 1568, 2093], .07, .2, 59.0); chime([880, 1319], .1, .18, 60.2)
# walkthrough (dashboard)
for s in (0, 4.2, 10.6, 15.2, 19.2, 22.2): whoosh(WB + s - .05, .4, .08, 800, 6000)
for c in (4.9, 5.4, 6.0, 13.4, 17.6, 23.4, 25.2): click(WB + c, .32)
chime([1319, 1661], .05, .12, WB + 9.5)        # ticket appears during patrol
chime([1047, 1568], .08, .12, WB + 17.65)      # species verified
t = tt(.5); buzz = lp(np.sign(np.sin(2 * np.pi * 196 * t)), 1500) * (np.sin(2 * np.pi * 6 * t) > 0) * env_ad(len(t), .01, .3); place(sfx, buzz, WB + 25.3, .12)
# end segment
whoosh(63.6 + CE, .7, .14, 300, 4000)
for i in range(4): place(sfx, sine_blip(note(84 + [0, 4, 7, 12][i]), .2, .08, .2), 65.6 + CE + i * .45, .08)
chime([587, 880, 1175, 1760], .12, .16, 67.0 + CE)

# ---------------- MIX ----------------
sfx = reverb(sfx, .7, .12, 11)
mix = mus + sfx
fo = np.clip((TOTAL - np.arange(N) / SR) / 1.2, 0, 1); mix *= fo[:, None]
pk = np.abs(mix).max(); mix *= 10 ** (-1.5 / 20) / pk
print('music rms dBFS', 20 * np.log10(np.sqrt((mus ** 2).mean()) * 10 ** (-1.5 / 20) / pk), 'mix rms dBFS', 20 * np.log10(np.sqrt((mix ** 2).mean())))
wavfile.write('mix.wav', SR, (mix * 32767).astype(np.int16))
