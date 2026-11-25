"""Takes the screenshots for the user guide from the test copy (dummy data only), in English and Bahasa Malaysia.
Run from the repo root:  python3 tests/guide_shots.py   -> guide/g-*-en.jpg, guide/g-*-bm.jpg"""
import os, io, threading, http.server, functools
from playwright.sync_api import sync_playwright
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, 'guide')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8766), functools.partial(Q, directory=ROOT)); threading.Thread(target=srv.serve_forever, daemon=True).start()
FAKE = open(os.path.join(ROOT, 'tests', 'fake-supabase.js')).read()
PHONE = {'width': 390, 'height': 760}; DESK = {'width': 1180, 'height': 760}
TXT = {'en': dict(rm='Small dent on the valve handle', ret='Please check the butterfly valve again', nm='Fadzil bin Hassan', dn='Handle only, no product contact. Valve closes fully. F45 raised.'), 'bm': dict(rm='Kemek kecil pada pemegang injap', ret='Sila periksa semula butterfly valve', nm='Fadzil bin Hassan', dn='Pemegang sahaja, tiada sentuhan produk. Injap tutup rapat. F45 dibuat.')}
def run(lang, b):
    ctx = b.new_context(viewport=PHONE, device_scale_factor=2, locale='en-GB'); ctx.add_init_script("try{localStorage.setItem('mic_lang','%s')}catch(e){}" % lang)
    pg = ctx.new_page(); pg.route('**/vendor/supabase.js', lambda r: r.fulfill(body=FAKE, content_type='application/javascript'))
    def shot(name, h=None, full=False):
        pg.evaluate("document.querySelectorAll('.toast').forEach(x=>x.remove());0"); pg.wait_for_timeout(250)
        vp = pg.viewport_size; png = pg.screenshot(clip={'x': 0, 'y': 0, 'width': vp['width'], 'height': h or vp['height']})
        Image.open(io.BytesIO(png)).convert('RGB').save(os.path.join(OUT, 'g-%s-%s.jpg' % (name, lang)), 'JPEG', quality=82, optimize=True)
    def login(u, go=True):
        pg.fill('[name=uid]', u); pg.fill('[name=pw]', 'password1')
        if go: pg.click('#authf button[type=submit]'); pg.wait_for_selector('.grid')
    def signout(): pg.evaluate("document.querySelectorAll('.toast').forEach(x=>x.remove());0"); pg.click('[data-act=menu]'); pg.click('.modal [data-act=signout]'); pg.wait_for_selector('#authf')
    def drum(): pg.click('.mcard >> nth=0'); pg.wait_for_selector('.f52')
    pg.goto('http://127.0.0.1:8766/index.html'); pg.wait_for_selector('#authf'); login('admin@demo.my'); signout()
    login('ali', go=False); shot('login', 640); pg.click('#authf button[type=submit]'); pg.wait_for_selector('.grid'); shot('today')
    drum(); shot('sheet-start', 560)
    pg.click('[data-act=start]'); pg.wait_for_selector('.item'); pg.fill('#r-time', '08:05'); shot('round-top')
    ids = pg.evaluate("Array.from(document.querySelectorAll('.item')).map(x=>x.id.slice(3))")
    pg.click('#it-%s [data-v=ok]' % ids[0]); pg.click('#it-%s [data-v=ok]' % ids[1]); pg.click('#it-%s [data-v=ng]' % ids[2]); pg.fill('[data-rm="%s"]' % ids[2], TXT[lang]['rm'])
    pg.evaluate("document.getElementById('it-%s').scrollIntoView({block:'center'});0" % ids[2]); shot('answers')
    pg.click('#it-%s img.ph' % ids[0]); pg.wait_for_selector('.lightbox'); shot('photo', 620); pg.click('.lightbox')
    for i in ids[3:]: pg.click('#it-%s [data-v=ok]' % i)
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight);0"); shot('submit-bar')
    pg.click('[data-act=submit]'); pg.wait_for_selector('.modal'); shot('submit-confirm'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.modal >> text=F45'); shot('f45'); pg.click('.modal [data-x="1"]')
    pg.wait_for_selector('.rcard'); pg.evaluate("window.scrollTo(0,0);0"); shot('sheet-submitted', 700)
    signout(); login('siti'); shot('today-checker', 420); drum(); pg.click('.rcard a.btn'); pg.wait_for_selector('[data-act=check]'); pg.evaluate("document.getElementById('it-%s').scrollIntoView({block:'center'});0" % ids[2]); shot('check'); pg.fill('.rv textarea', TXT[lang]['dn']); pg.evaluate("document.querySelector('.rv').scrollIntoView({block:'center'});0"); shot('decision')
    pg.click('[data-act=return]'); pg.fill('#askv', TXT[lang]['ret']); shot('return-dialog'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.rcard')
    signout(); login('ali'); drum(); shot('sheet-returned', 700); pg.click('.rcard a.btn'); pg.wait_for_selector('.banner.bad'); shot('returned', 480)
    pg.click('[data-act=submit]'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.modal >> text=F45'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.rcard')
    signout(); login('siti'); drum(); pg.click('.rcard a.btn'); pg.wait_for_selector('.rv'); pg.fill('.rv textarea', TXT[lang]['dn']); pg.click('.rv [data-s=minor][data-d=go]'); pg.wait_for_selector('.rv .chip.ok'); pg.evaluate("document.querySelector('.rv').scrollIntoView({block:'center'});0"); shot('decision-done'); pg.click('[data-act=check]'); pg.wait_for_selector('.modal'); shot('check-dialog'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.rcard')
    signout(); login('farah@demo.my'); shot('today-verifier', 420); drum(); shot('sheet-verify', 620); pg.click('[data-act=verify]'); pg.wait_for_selector('.modal'); shot('verify-dialog'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.banner.info'); shot('sheet-verified', 700)
    pg.click('[data-act=menu]'); pg.wait_for_selector('.modal'); shot('menu', 560); pg.click('.modal [data-act=closem]')
    pg.set_viewport_size(DESK); pg.evaluate("document.querySelector('.f52-wrap').scrollIntoView({block:'start'});0"); shot('form-view', 520)
    pg.click('.nav a >> nth=1'); pg.wait_for_selector('table.list tr.click'); shot('records', 420)
    signout(); login('admin@demo.my'); pg.click('.nav a >> nth=3'); pg.wait_for_selector('.u-f'); shot('users', 560)
    pg.click('[data-act=uadd]'); pg.fill('#uaddf [name=nm]', TXT[lang]['nm']); pg.fill('#uaddf [name=uid]', 'fadzil'); pg.fill('#uaddf [name=pw]', 'Abc12345'); shot('add-user', 700); pg.click('#uaddf [data-x="0"]')
    pg.click('.nav a >> nth=2'); pg.wait_for_selector('.grid'); pg.click('.mcard >> nth=0'); pg.wait_for_selector('[data-tf=rev]'); shot('setup', 640)
    ctx.close()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--lang=en-GB', '--no-sandbox'])
    for lang in ('en', 'bm'): run(lang, b); print('done', lang)
    b.close()
