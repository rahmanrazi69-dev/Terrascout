import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from scipy.signal import resample_poly
k = Kokoro('kokoro-v1.0.onnx', 'voices-v1.0.bin')
# (start s, latest end s, text)
L = [
 (0.4, 5.9, "This is TerraScout: a robotic ecologist for Sime Darby Property townships."),
 (6.4, 12.3, "Each patrol starts at a solar charging dock, and follows a scheduled route through the park."),
 (12.6, 20.4, "At every tagged sapling, the rover reads its marker to know exactly which tree it is, then photographs the leaves."),
 (21.0, 29.3, "This one scores zero point four one, below the care line. It's flagged as stressed, and a ticket goes straight to the landscapers."),
 (29.8, 33.2, "At sound stations, the rover stops and listens."),
 (35.7, 41.2, "BirdNET names the bird on board: a Common Iora. An ecologist confirms it later."),
 (41.6, 53.2, "Next, a heat transect. Every reading is compared with a fixed reference station at the same moment. Under the canopy, the path is almost four degrees cooler."),
 (53.5, 63.0, "Back at the dock, photos upload to the server, where a larger YOLO model diagnoses the problem. Every record is hash linked, so any edit is detectable."),
 (63.3, 68.3, "The TerraScout Console puts it all on one screen, starting with five headline numbers."),
 (68.5, 73.0, "Run a patrol, and the map updates as each sapling is checked."),
 (73.3, 78.3, "Stressed saplings become tickets, with the server's diagnosis attached."),
 (78.5, 81.6, "Ecologists verify new species with one click."),
 (81.9, 84.8, "The heat chart shows where shade cools the township."),
 (85.0, 90.6, "And if anyone edits an old record, the audit trail shows exactly where it broke."),
 (91.0, 97.6, "TerraScout. Measured, not estimated."),
]
SR = 44100; TOTAL = 98.5
vo = np.zeros(int(SR * TOTAL)); spans = []
for st, end, txt in L:
    sp = 1.05
    while True:
        a, sr = k.create(txt, voice='af_heart', speed=sp, lang='en-us')
        d = len(a) / sr
        if st + d <= end or sp >= 1.3: break
        sp += .05
    a = resample_poly(a, SR, sr); i = int(st * SR); n = min(len(a), len(vo) - i)
    vo[i:i + n] += a[:n]; spans.append((st, st + n / SR))
    print(f'{st:5.1f} {d:4.1f}s speed {sp:.2f} end {st + d:5.1f} / {end}')
vo /= np.abs(vo).max(); vo *= 0.9
np.save('spans.npy', np.array(spans)); sf.write('vo.wav', vo, SR)
