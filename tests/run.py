"""Click-through test of index.html against the in-memory fake (dummy data only).
Run from the repo root:  python3 tests/run.py   (needs: pip install playwright, and Google Chrome)"""
import os, sys, threading, http.server, functools, json
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'tests', 'out'); os.makedirs(OUT, exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8765), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
FAKE = open(os.path.join(ROOT, 'tests', 'fake-supabase.js')).read()
errs = []; ok = 0
def check(c, m):
    global ok
    if c: ok += 1
    else: errs.append(m); print('FAIL', m)
def setup(ctx):
    pg = ctx.new_page()
    pg.route('**/vendor/supabase.js', lambda r: r.fulfill(body=FAKE, content_type='application/javascript'))
    pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: errs.append('console: ' + m.text) if m.type == 'error' and 'favicon' not in m.text else None)
    pg.goto('http://127.0.0.1:8765/index.html'); pg.wait_for_selector('#authf'); return pg
def login(pg, user):
    pg.fill('[name=uid]', user); pg.fill('[name=pw]', 'x'); pg.click('#authf button[type=submit]'); pg.wait_for_selector('.grid')
def signout(pg):
    pg.evaluate("document.querySelectorAll('.toast').forEach(x=>x.remove());0")
    pg.click('[data-act=menu]'); pg.click('.modal [data-act=signout]'); pg.wait_for_selector('#authf')
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--lang=en-GB', '--no-sandbox'])
    phone = b.new_context(viewport={'width': 390, 'height': 800}, device_scale_factor=1, has_touch=True, is_mobile=True, locale='en-GB')
    desk = b.new_context(viewport={'width': 1366, 'height': 850}, device_scale_factor=1, locale='en-GB')
    # --- operator on a phone ---
    pg = setup(phone); pg.screenshot(path=OUT + '/01-login-phone.png')
    pg.fill('[name=uid]', 'ali'); pg.fill('[name=pw]', 'x'); pg.click('#authf button[type=submit]'); pg.wait_for_selector('text=have not been loaded'); check(True, 'operator told to wait for admin'); pg.click('[data-act=signout]'); pg.wait_for_selector('#authf')
    login(pg, 'admin@demo.my'); signout(pg)
    login(pg, 'ali'); check(pg.locator('.mcard').count() == 8, '8 machine cards'); pg.screenshot(path=OUT + '/02-today-phone.png')
    check(pg.locator('.nav a').count() == 2, 'operator sees 2 tabs')
    pg.click('.mcard >> text=Semi-Auto Packing Machine 3'); pg.wait_for_selector('.f52')
    check(pg.locator('[data-act=start]').count() == 0, 'PM3 not in use: no start button')
    pg.go_back(); pg.wait_for_selector('.grid')
    pg.click('.mcard >> text=Auto-Packing Machine 1'); pg.wait_for_selector('[data-act=start]'); check(pg.locator('[data-act=pdf]').is_disabled(), 'pdf button disabled before any submission'); pg.click('[data-act=start]'); pg.wait_for_selector('.item')
    n = pg.locator('.item').count(); check(n == 53, 'AP1 has 53 parts, got %d' % n)
    pg.screenshot(path=OUT + '/03-round-phone.png')
    pg.click('[data-act=submit]'); check('not yet inspected' in pg.locator('.toast').inner_text(), 'submit blocked while incomplete')
    ids = pg.evaluate("Array.from(document.querySelectorAll('.item')).map(x=>x.id.slice(3))")
    for i in ids: pg.click('#it-%s [data-v=ok]' % i)
    pg.click('#it-%s [data-v=ng]' % ids[1]); pg.click('#it-%s [data-v=miss]' % ids[5]); pg.click('#it-%s [data-v=na]' % ids[6])
    check(pg.locator('#pcount').inner_text() == '53 / 53', 'progress 53/53')
    pg.fill('[data-ref]', 'W60/03')
    pg.click('[data-act=submit]'); check('what is wrong' in pg.locator('.toast').inner_text().lower(), 'remark required for Not OK')
    pg.fill('[data-rm="%s"]' % ids[1], 'Auger dented at tip'); pg.fill('[data-rm="%s"]' % ids[5], 'Knocker removed')
    pg.evaluate("window.scrollTo(0, 900);0"); pg.wait_for_timeout(300); pg.screenshot(path=OUT + '/04-round-answers-phone.png')
    pg.wait_for_timeout(1800); check('Saved' in pg.locator('#savest').inner_text(), 'draft auto-saved')
    pg.click('[data-act=submit]'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.modal >> text=F45'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.rcard')
    check(pg.locator('[data-act=pdf]').is_enabled(), 'pdf button enabled after submit')
    with pg.expect_download(timeout=90000) as d: pg.click('[data-act=pdf]')
    d.value.save_as(OUT + '/download-ap1-phone.pdf'); check('not-verified' in d.value.suggested_filename, 'unverified pdf is labelled')
    pg.close()
    # fake state is per page, so run the whole flow in one desktop page from here
    pg = setup(desk); pg.screenshot(path=OUT + '/05-login-desktop.png'); login(pg, 'admin@demo.my'); signout(pg); login(pg, 'ali')
    pg.click('.mcard >> text=Drum Mixer 250 kg'); pg.click('[data-act=start]'); pg.wait_for_selector('.item')
    ids = pg.evaluate("Array.from(document.querySelectorAll('.item')).map(x=>x.id.slice(3))"); check(len(ids) == 8, 'drum 8 parts')
    for i in ids: pg.click('#it-%s [data-v=ok]' % i)
    pg.click('#it-%s [data-v=ng]' % ids[2]); pg.fill('[data-rm="%s"]' % ids[2], 'Valve handle loose')
    pg.screenshot(path=OUT + '/06-round-desktop.png')
    pg.click('[data-act=submit]'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.modal >> text=F45'); pg.screenshot(path=OUT + '/07-f45-reminder.png'); pg.click('.modal [data-x="1"]')
    pg.wait_for_selector('.rcard'); check('Waiting for check' in pg.locator('.rcard').inner_text(), 'round waiting for check')
    ym = pg.evaluate("S.today.slice(0,7).replace('-','')"); check('Batch ' + ym + '-001' in pg.locator('.rcard').inner_text(), 'auto batch number YYYYMM-001'); 
    check(pg.locator('.rcard a.btn').inner_text() == 'View', 'operator can only view own submitted round')
    # second round (change-over) by the same operator
    pg.click('[data-act=start]'); pg.wait_for_selector('.item')
    for i in ids: pg.click('#it-%s [data-v=ok]' % i)
    pg.click('[data-act=submit]'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.rcard'); check(pg.locator('.rcard').count() == 2, '2 rounds'); check('Batch ' + ym + '-002' in pg.locator('.rcard >> nth=1').inner_text(), 'second round gets -002')
    signout(pg)
    # --- checker ---
    login(pg, 'siti'); check('2 round(s) waiting for Check by' in pg.locator('main').inner_text(), 'checker banner')
    pg.click('.mcard >> text=Drum Mixer 250 kg'); pg.wait_for_selector('.rcard'); check(pg.locator('[data-act=verify]').count() == 0, 'checker has no verify button')
    pg.click('.rcard >> nth=0 >> a.btn'); pg.wait_for_selector('[data-act=check]'); pg.screenshot(path=OUT + '/08-check-desktop.png')
    pg.click('[data-act=return]'); pg.fill('#askv', 'Recheck the butterfly valve'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.rcard'); check('Returned for correction' in pg.locator('.rcard >> nth=0').inner_text(), 'round returned')
    pg.click('.rcard >> nth=1 >> a.btn'); pg.click('[data-act=check]'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.rcard')
    signout(pg)
    login(pg, 'ali'); pg.click('.mcard >> text=Drum Mixer 250 kg'); pg.click('.rcard >> nth=0 >> a.btn'); pg.wait_for_selector('.banner.bad')
    pg.click('#it-%s [data-v=ok]' % ids[2]); pg.click('[data-act=submit]'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.rcard'); signout(pg)
    login(pg, 'siti'); pg.click('.mcard >> text=Drum Mixer 250 kg'); pg.click('.rcard >> nth=0 >> a.btn'); pg.click('[data-act=check]'); pg.fill('#askv', 'Valve tightened'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.rcard'); signout(pg)
    # --- verifier ---
    login(pg, 'farah@demo.my'); check('1 checklist(s) ready for Verify by' in pg.locator('main').inner_text(), 'verifier banner')
    pg.click('.mcard >> text=Drum Mixer 250 kg'); pg.wait_for_selector('[data-act=verify]'); pg.click('[data-act=verify]'); pg.click('.modal [data-x="1"]'); pg.wait_for_selector('.banner.info >> text=Verify by')
    check(pg.locator('[data-act=start]').count() == 0, 'verified sheet is locked')
    pg.screenshot(path=OUT + '/09-sheet-verified-desktop.png', full_page=True)
    check(pg.locator('table.f52 td.sig >> nth=0').inner_text() == 'Siti QC', 'check by on form view'); check(pg.locator('table.f52 td.sig >> nth=1').inner_text() == 'Farah Exec', 'verify by on form view')
    # print layout
    pg.evaluate("window.print = () => { window.__printed = true };0"); pg.click('[data-act=print][data-ph="1"]'); pg.wait_for_function('window.__printed === true', timeout=15000)
    check(pg.locator('#print .pg').count() == 1 and 'F52/1' in pg.locator('#print').inner_text(), 'print built')
    pg.emulate_media(media='print'); pg.pdf(path=OUT + '/print-drum250.pdf', prefer_css_page_size=True); pg.emulate_media(media='screen')
    with pg.expect_download(timeout=60000) as d: pg.click('[data-act=pdf]')
    d.value.save_as(OUT + '/download-drum250.pdf'); check(d.value.suggested_filename == 'F52-1_Drum-Mixer-250-kg_' + pg.evaluate('S.sheet.date') + '.pdf', 'pdf name ' + d.value.suggested_filename); check(os.path.getsize(OUT + '/download-drum250.pdf') > 20000, 'pdf has content')
    pg.click('.nav >> text=Records'); pg.wait_for_selector('table.list tr.click'); pg.screenshot(path=OUT + '/10-records-desktop.png')
    with pg.expect_download() as d: pg.click('[data-act=csv]')
    csv = open(d.value.path(), encoding='utf-8-sig').read(); check(csv.count('\n') == 16 and 'Valve handle' not in csv and 'Farah Exec' in csv, 'csv rows %d' % csv.count('\n'))
    signout(pg)
    # --- admin ---
    login(pg, 'admin@demo.my'); check(pg.locator('.nav a').count() == 4, 'admin sees 4 tabs')
    pg.click('.nav >> text=Checklists'); pg.click('.mcard >> text=Semi-Auto Packing Machine 3'); pg.wait_for_selector('[data-tf=rev]'); pg.screenshot(path=OUT + '/11-setup-desktop.png')
    pg.fill('[data-tf=rev]', '02'); pg.select_option('select[data-tf=status]', 'active'); pg.fill('[data-if=crit] >> nth=0', 'Intact, No dent, No Broken, Clean'); pg.click('[data-act=tsave] >> nth=0'); pg.wait_for_selector('.grid')
    check('Rev 02' in pg.locator('.mcard >> text=Semi-Auto Packing Machine 3').locator('xpath=..').inner_text(), 'template saved')
    pg.click('.nav >> text=Users'); pg.wait_for_selector('.u-role'); pg.screenshot(path=OUT + '/12-users-desktop.png')
    pg.click('.nav >> text=Today'); pg.click('.mcard >> text=IBC'); pg.wait_for_selector('.f52'); pg.evaluate("window.__printed=false; window.print = () => { window.__printed = true };0")
    pg.click('[data-act=print][data-ph="1"]'); pg.wait_for_function('window.__printed === true', timeout=20000); pg.emulate_media(media='print'); pg.pdf(path=OUT + '/print-ibc-blank.pdf', prefer_css_page_size=True); pg.emulate_media(media='screen')
    signout(pg)
    # --- self registration ---
    pg.click('[data-v=reg]'); pg.fill('[name=name]', 'Kumar Raj'); pg.fill('[name=uid]', 'kumar'); pg.fill('[name=pw]', 'password1'); pg.fill('[name=pw2]', 'password1'); pg.click('#authf button[type=submit]')
    pg.wait_for_selector('text=Waiting for activation'); check(True, 'pending screen'); pg.screenshot(path=OUT + '/13-pending.png')
    pg.click('[data-act=lang]'); check('Menunggu pengaktifan' in pg.locator('#app').inner_text(), 'BM toggle')
    b.close()
print('passed %d checks, %d problems' % (ok, len(errs))); [print(' -', e) for e in errs]; sys.exit(1 if errs else 0)
