import asyncio, os
from playwright.async_api import async_playwright
SK = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>:root{color-scheme:light}body{margin:0;font:14px Inter,system-ui}</style></head><body>'
FPS, DUR = 30, 27.5
async def main():
    src = open('../dashboard/index.html').read().replace('"Public Sans",', 'Inter,').replace('"Bricolage Grotesque",', '"Inter Display",')
    open('_walk.html', 'w').write(SK + src + '</body></html>')
    os.makedirs('wframes', exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1440, 'height': 810}, device_scale_factor=1280 / 1440, reduced_motion='reduce')
        await pg.clock.install()
        await pg.goto('http://localhost:8765/_walk.html')
        await pg.clock.run_for(1500)
        await pg.evaluate("document.fonts.ready")
        await pg.add_script_tag(content=open('walk.js').read())
        n = int(DUR * FPS)
        for i in range(n):
            t = i / FPS
            await pg.evaluate(f'WT.render({t})')
            await pg.clock.run_for(round((i + 1) * 1000 / FPS) - round(i * 1000 / FPS))
            await pg.screenshot(path=f'wframes/{i:05d}.jpg', type='jpeg', quality=92)
            if i % 150 == 0: print(i, n, flush=True)
        await b.close()
asyncio.run(main())
