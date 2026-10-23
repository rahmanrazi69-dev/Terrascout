import asyncio, base64, os
from playwright.async_api import async_playwright
SHOTS={'aerial':3.5,'dock':9.5,'scan':25.5,'bird':35.5,'heat':50,'upload':59.5}
async def main():
    os.makedirs('stills', exist_ok=True)
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':1280,'height':720})
        await pg.goto('http://localhost:8765/scene.html'); await pg.wait_for_function('window.ready'); await pg.evaluate('window.ready')
        for k,t in SHOTS.items():
            d=await pg.evaluate(f'renderAt({t}, false)'); open(f'stills/{k}.jpg','wb').write(base64.b64decode(d.split(',')[1]))
        await b.close()
asyncio.run(main())
