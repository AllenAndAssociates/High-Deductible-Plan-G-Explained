"""Synthesize music bed + frame-synced SFX (cue times from the voice track's word timings)."""
import numpy as np, wave, sys
SR = 48000; DUR = 128.5
N = int(SR * DUR)
rng = np.random.default_rng(7)
db = lambda d: 10 ** (d / 20)
t_ = lambda d: np.arange(int(SR * d)) / SR

def env(n, a=0.003, r=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a)
    if r: e *= np.exp(-t / r)
    return e

def tone(f, d, r, harm=((1, 1),)):
    t = t_(d); s = sum(w * np.sin(2 * np.pi * f * h * t) for h, w in harm)
    return s * env(len(t), 0.002, r)

def noise(d, r, lp=1):
    x = rng.standard_normal(int(SR * d))
    if lp > 1: x = np.convolve(x, np.ones(lp) / lp, 'same') * np.sqrt(lp)
    return x * env(len(x), 0.001, r)

def pop(f=900): t = t_(.09); return np.sin(2*np.pi*np.cumsum(np.linspace(f, f*1.7, len(t)))/SR) * env(len(t), .002, .025)
def click(): return noise(.012, .002) * .8
def ticks(n, gap=.05): return np.concatenate([np.pad(click()*.6, (0, int(SR*gap))) for _ in range(n)])
def marimba(f): return tone(f, 1.0, .25, ((1, 1), (4, .25), (10, .05)))
def chime(f): return tone(f, 1.6, .5, ((1, 1), (2.76, .3), (5.4, .1)))
def thud(): t = t_(.6); return np.sin(2*np.pi*np.cumsum(np.linspace(110, 40, len(t)))/SR)*env(len(t), .002, .15) + np.pad(noise(.08, .02, 20)*.5, (0, len(t)-int(SR*.08)))
def whoosh():
    d = .55; x = rng.standard_normal(int(SR*d)); t = np.arange(len(x))/SR
    x = np.convolve(x, np.ones(6)/6, 'same'); return x * np.sin(np.pi * t / d) ** 2 * .9
def swipe():
    d = .4; x = rng.standard_normal(int(SR*d)); t = np.arange(len(x))/SR
    return np.convolve(x, np.ones(3)/3, 'same') * np.sin(np.pi*t/d) * .5
def chord(fs, d, r): return sum(tone(f, d, r, ((1, 1), (2, .2))) for f in fs) / len(fs)

out = np.zeros(N)
def at(t, x, g):
    i = int(t * SR); j = min(N, i + len(x)); out[i:j] += x[:j - i] * db(g)

C5, E5, G5, C6, A4 = 523.25, 659.25, 783.99, 1046.5, 440
# Scene 1
at(0.0, whoosh(), -20); at(3.0, swipe(), -26); at(7.8, pop(700), -20)
# Scene 2
at(19.3, swipe(), -18)
at(22.7, pop(900), -16); at(26.5, ticks(14, .06), -22)
at(30.0, pop(950), -16); at(36.1, ticks(6, .05), -22)
# Scene 3 ascending pops
at(40.0, pop(900), -16); at(45.4, pop(1100), -16); at(49.0, pop(1350), -16)
at(53.8, marimba(C6) + .7 * np.pad(marimba(G5), (int(SR*.12), 0))[:int(SR)], -14)
# Scene 4
at(56.7, thud(), -8); at(56.75, whoosh(), -14)
at(69.5, chime(G5) + np.pad(chime(C6), (int(SR*.18), 0))[:int(SR*1.6)], -18)
at(69.6, noise(.03, .008), -14); at(69.65, click(), -12)
for k, f in enumerate([C5, E5, G5, C6]): at(74.4 + k * .09, chime(f), -18)
at(74.9, click(), -8); at(74.98, click(), -10)
# Scene 5
at(89.3, ticks(5, .025)[::-1], -16)
at(92.6, chime(A4) + np.pad(chime(A4*0.94), (int(SR*.25), 0))[:int(SR*1.6)], -16)
for t in (95.4, 96.55, 98.45): at(t, pop(800), -20)
at(105.1, thud(), -10)
# Scene 6
at(111.2, pop(1000), -16)
for t in (116.8, 117.25, 118.4): at(t, tone(350, .09, .05) + tone(440, .09, .05), -22)
at(120.9, click(), -10)
at(123.2, pop(1000), -18); at(123.6, pop(1200), -18)
at(122.4, chord([C5/2, E5/2, G5/2, C5], 1.4, .6) + chord([C5, E5, G5], 1.4, .5), -18)

out *= db(-9)  # SFX sit well under the voice
# Music bed: warm Cmaj–Am–F–G pad with soft 8th-note pluck
bpm = 96; beat = 60 / bpm; prog = [[261.6, 329.6, 392.0], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [196.0, 246.9, 293.7]]
mus = np.zeros(N); bar = 4 * beat; tt = np.arange(N) / SR
for b in range(int(DUR / bar) + 1):
    fs = prog[b % 4]; i0 = int(b * bar * SR); i1 = min(N, int((b + 1) * bar * SR))
    if i0 >= N: break
    seg = tt[i0:i1] - b * bar
    pad = sum(np.sin(2*np.pi*f*seg) + .3*np.sin(2*np.pi*f*2*seg + .5) for f in fs) / 3
    pad *= np.minimum(1, seg / .4) * np.minimum(1, (bar - seg) / .4)
    mus[i0:i1] += pad * .6
    for e in range(8):
        p = tone(fs[e % 3] * 2, beat / 2, .08, ((1, 1), (3, .15)))
        k = i0 + int(e * beat / 2 * SR); m = max(0, min(len(p), N - k)); mus[k:k + m] += p[:m] * .35
    bass = tone(fs[0] / 2, bar, .9); m = min(len(bass), N - i0); mus[i0:i0+m] += bass[:m] * .5
mus /= np.abs(mus).max()
# level automation (dB): -26 base, hard stop 56.7, resume 65.1, pause 92.5, soft resume 99.6, swell -22 at 107.2
keys = [(0, -60), (1.0, -26), (56.65, -26), (56.7, -90), (65.0, -90), (65.8, -26), (92.4, -26), (92.6, -90), (99.5, -90), (101.5, -30),
        (106.5, -30), (108.0, -22), (122.0, -22), (126.0, -20), (128.5, -60)]
lv = np.interp(tt, [k[0] for k in keys], [k[1] for k in keys])
lv = np.where(tt < 122.6, lv - 9, lv - 3)  # music bed well under voice; slightly fuller on end card
out += mus * db(lv)

# voice
w = wave.open(sys.argv[1]); v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
v = v.reshape(-1, w.getnchannels()).mean(1)[:N]; out[:len(v)] += v
out = np.tanh(out * 1.1) / np.tanh(1.1) if np.abs(out).max() > 1 else out
o = wave.open(sys.argv[2], 'w'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
o.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); o.close()
print('peak', np.abs(out).max())
