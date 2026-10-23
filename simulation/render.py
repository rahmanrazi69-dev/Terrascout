import asyncio, base64, os, sys, time
from playwright.async_api import async_playwright
FPS=30; DUR=72.0
async def main():
    os.makedirs('frames', exist_ok=True)
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':1280,'height':720})
        await pg.goto('http://localhost:8765/scene.html'); await pg.wait_for_function('window.ready'); await pg.evaluate('window.ready')
        n=int(DUR*FPS); s=time.time()
        for i in range(n):
            d=await pg.evaluate(f'renderAt({i/FPS})')
            open(f'frames/{i:05d}.jpg','wb').write(base64.b64decode(d.split(',')[1]))
            if i%150==0: print(i,n,round(time.time()-s),flush=True)
        await b.close()
asyncio.run(main())
