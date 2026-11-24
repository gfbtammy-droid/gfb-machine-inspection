"""Builds guide.html (English + Bahasa Malaysia) and the two printable PDFs from the text below and guide/g-*.jpg.
Run from the repo root after tests/guide_shots.py:  python3 tests/build_guide.py"""
import os, html, threading, http.server, functools
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'https://gfbtammy-droid.github.io/gfb-machine-inspection/'
UPDATED = '24/11/2026'
# Each chapter: (id, who, EN title, BM title, [steps]).  Step: (image key or '', EN html, BM html).  'wide' images are PC screens.
WIDE = {'records', 'users', 'add-user', 'setup', 'form-view'}
C = [
('start', 'all', 'Open the app and sign in', 'Buka aplikasi dan log masuk', [
 ('', 'On your phone or PC, open <b>Chrome</b> and go to:<br><span class="url">gfbtammy-droid.github.io/gfb-machine-inspection</span>', 'Di telefon atau PC, buka <b>Chrome</b> dan pergi ke:<br><span class="url">gfbtammy-droid.github.io/gfb-machine-inspection</span>'),
 ('login', 'Type the <b>username</b> and <b>password</b> that your Admin gave you. No spaces. Then tap <b>Sign in</b>.<br>You do not need an email address.', 'Taip <b>nama pengguna</b> dan <b>kata laluan</b> yang diberi oleh Admin. Jangan letak ruang kosong. Kemudian tekan <b>Log masuk</b>.<br>Anda tidak perlukan alamat emel.'),
 ('', 'To change the language, tap the small <b>BM</b> or <b>EN</b> button at the top right.', 'Untuk tukar bahasa, tekan butang kecil <b>EN</b> atau <b>BM</b> di bahagian atas kanan.'),
 ('menu', 'The first time you sign in, change your password: tap <b>&#9776;</b> (top right), then <b>Change my password</b>. Use at least 8 characters and do not share it. Your name is recorded on every checklist you sign.', 'Kali pertama log masuk, tukar kata laluan anda: tekan <b>&#9776;</b> (atas kanan), kemudian <b>Tukar kata laluan saya</b>. Guna sekurang-kurangnya 8 aksara dan jangan kongsi dengan orang lain. Nama anda direkod pada setiap senarai semak yang anda tandatangan.'),
 ('', '<b>Tip:</b> put the app on your phone screen. In Chrome tap <b>&#8942;</b> then <b>Add to Home screen</b>. On iPhone (Safari) tap the Share button, then <b>Add to Home Screen</b>.', '<b>Tip:</b> letak aplikasi di skrin telefon. Dalam Chrome tekan <b>&#8942;</b> kemudian <b>Add to Home screen</b>. Di iPhone (Safari) tekan butang Share, kemudian <b>Add to Home Screen</b>.'),
]),
('inspect', 'fill', 'Operator: do a machine inspection (Done by)', 'Operator: buat pemeriksaan mesin (Done by)', [
 ('', '<b>When:</b> before production starts, and every time the product changes (change-over). Inspect the real machine, part by part. Do not tick from memory.', '<b>Bila:</b> sebelum pengeluaran bermula, dan setiap kali produk bertukar (change-over). Periksa mesin sebenar, satu bahagian demi satu bahagian. Jangan tanda ikut ingatan.'),
 ('today', 'On the <b>Today</b> tab, tap your machine.', 'Di tab <b>Hari ini</b>, tekan mesin anda.'),
 ('sheet-start', 'Tap <b>+ Start inspection round</b>.', 'Tekan <b>+ Mula pusingan pemeriksaan</b>.'),
 ('round-top', 'Check that the <b>TIME</b> is correct. The <b>BATCH NO.</b> is given automatically when you submit, so you do not type it.', 'Pastikan <b>TIME</b> (masa) betul. <b>BATCH NO.</b> diberi secara automatik apabila anda hantar, jadi tidak perlu taip.'),
 ('photo', 'For each part, look at the real part and compare it with the <b>photo</b> and the <b>blue words</b> (the condition it must be in). Tap the photo to make it bigger.', 'Untuk setiap bahagian, lihat bahagian sebenar dan bandingkan dengan <b>gambar</b> dan <b>tulisan biru</b> (keadaan yang sepatutnya). Tekan gambar untuk besarkan.'),
 ('answers', 'Tap one answer for every part:<table class="mini"><tr><td><b class="ok">&#10003; OK</b></td><td>The part is there and in good condition.</td></tr><tr><td><b class="ng">&#10007; Not OK</b></td><td>The part is there but damaged, dirty, loose or not working.</td></tr><tr><td><b class="ng">X Missing</b></td><td>The part is not there.</td></tr><tr><td><b>N/A</b></td><td>This part is not used on this machine.</td></tr></table>For <b>Not OK</b> and <b>Missing</b> you must write what is wrong in the box.', 'Tekan satu jawapan untuk setiap bahagian:<table class="mini"><tr><td><b class="ok">&#10003; OK</b></td><td>Bahagian ada dan dalam keadaan baik.</td></tr><tr><td><b class="ng">&#10007; Tidak OK</b></td><td>Bahagian ada tetapi rosak, kotor, longgar atau tidak berfungsi.</td></tr><tr><td><b class="ng">X Tiada</b></td><td>Bahagian tidak ada.</td></tr><tr><td><b>N/A</b></td><td>Bahagian ini tidak digunakan pada mesin ini.</td></tr></table>Untuk <b>Tidak OK</b> dan <b>Tiada</b>, anda mesti tulis masalahnya dalam kotak.'),
 ('submit-bar', 'The bar at the bottom shows how many parts are done (for example 8 / 8). When every part has an answer, tap <b>Submit for check</b>.', 'Bar di bawah menunjukkan berapa bahagian sudah siap (contohnya 8 / 8). Apabila semua bahagian sudah dijawab, tekan <b>Hantar untuk semakan</b>.'),
 ('submit-confirm', 'Read the message and tap <b>Submit</b>. Your name and the time are recorded as <b>Done by</b>. After this you cannot change the answers.', 'Baca mesej dan tekan <b>Hantar</b>. Nama dan masa anda direkod sebagai <b>Done by</b>. Selepas ini jawapan tidak boleh diubah.'),
 ('f45', 'If any part is Not OK or Missing, this message appears. <b>Do not use the machine.</b> Tell your Production Leader and QC now. The breakdown must be recorded in the <b>Machine Maintenance Upkeep Report (F45)</b>. Tap <b>Understood</b>.', 'Jika ada bahagian Tidak OK atau Tiada, mesej ini akan keluar. <b>Jangan guna mesin.</b> Beritahu Ketua Pengeluaran dan QC sekarang. Kerosakan mesti direkod dalam <b>Machine Maintenance Upkeep Report (F45)</b>. Tekan <b>Faham</b>.'),
 ('sheet-submitted', 'Done. Your round now shows <b>Waiting for check</b> with its batch number. QC will check it.', 'Selesai. Pusingan anda kini menunjukkan <b>Menunggu semakan</b> bersama nombor batch. QC akan menyemaknya.'),
 ('', '<b>Stopped halfway?</b> Your answers are saved by themselves. Open the machine again and tap <b>+ Continue my inspection</b>. If you started by mistake, tap <b>Delete draft</b>.', '<b>Berhenti separuh jalan?</b> Jawapan anda disimpan sendiri. Buka mesin itu semula dan tekan <b>+ Sambung pemeriksaan saya</b>. Jika termula secara tidak sengaja, tekan <b>Padam draf</b>.'),
]),
('returned', 'fill', 'Operator: when QC returns your inspection', 'Operator: apabila QC pulangkan pemeriksaan anda', [
 ('sheet-returned', 'If QC is not satisfied, the round comes back to you with the words <b>Returned for correction</b>. Tap <b>Continue</b>.', 'Jika QC tidak berpuas hati, pusingan itu dipulangkan kepada anda dengan tulisan <b>Dipulangkan untuk pembetulan</b>. Tekan <b>Sambung</b>.'),
 ('returned', 'Read the red message. Check that part on the machine again, correct your answer, then tap <b>Submit for check</b> again. The batch number stays the same.', 'Baca mesej merah. Periksa semula bahagian itu pada mesin, betulkan jawapan anda, kemudian tekan <b>Hantar untuk semakan</b> sekali lagi. Nombor batch kekal sama.'),
]),
('check', 'check', 'Checker (QC): sign Check by', 'Penyemak (QC): tandatangan Check by', [
 ('today-checker', 'A blue bar on the <b>Today</b> tab tells you how many rounds are waiting. Tap the machine that shows <b>to check</b>.', 'Bar biru di tab <b>Hari ini</b> menunjukkan berapa pusingan sedang menunggu. Tekan mesin yang menunjukkan <b>untuk disemak</b>.'),
 ('', 'On the round, tap <b>Check</b>.', 'Pada pusingan itu, tekan <b>Semak</b>.'),
 ('check', 'Go through the answers. Red answers are Not OK or Missing; read the operator\'s remark and look at the machine yourself.', 'Semak semua jawapan. Jawapan merah ialah Tidak OK atau Tiada; baca catatan operator dan lihat sendiri mesin itu.'),
 ('check-dialog', 'If the inspection is correct, tap <b>&#10003; Sign as Check by</b>, then <b>Sign Check by</b>. For Not OK parts, make sure F45 has been raised first.', 'Jika pemeriksaan betul, tekan <b>&#10003; Tandatangan Check by</b>, kemudian <b>Tandatangan Check by</b> sekali lagi. Untuk bahagian Tidak OK, pastikan F45 sudah dibuat dahulu.'),
 ('return-dialog', 'If something is wrong, tap <b>Return for correction</b>, write what the operator must correct, then tap <b>Return</b>.', 'Jika ada yang tidak betul, tekan <b>Pulangkan untuk pembetulan</b>, tulis apa yang operator perlu betulkan, kemudian tekan <b>Pulangkan</b>.'),
 ('', '<b>Rule:</b> you cannot check a round that you filled in yourself. Another checker must do it.', '<b>Peraturan:</b> anda tidak boleh menyemak pusingan yang anda sendiri isi. Penyemak lain mesti melakukannya.'),
]),
('verify', 'verify', 'Verifier (Production Executive): sign Verify by', 'Pengesah (Production Executive): tandatangan Verify by', [
 ('today-verifier', 'A blue bar on the <b>Today</b> tab tells you how many checklists are ready. Open the machine.', 'Bar biru di tab <b>Hari ini</b> menunjukkan berapa senarai semak sudah sedia. Buka mesin itu.'),
 ('sheet-verify', 'When every round shows <b>Checked</b>, tap <b>&#10003; Verify checklist (Verify by)</b>.', 'Apabila semua pusingan menunjukkan <b>Disemak</b>, tekan <b>&#10003; Sahkan senarai semak (Verify by)</b>.'),
 ('verify-dialog', 'Read the message. If there are Not OK parts, confirm the corrective action (F45) is recorded. Tap <b>Verify</b>.', 'Baca mesej. Jika ada bahagian Tidak OK, pastikan tindakan pembetulan (F45) sudah direkod. Tekan <b>Sahkan</b>.'),
 ('sheet-verified', 'The checklist now shows <b>Verified</b> and is locked. Nobody can add or change a round for that machine and date.', 'Senarai semak kini menunjukkan <b>Disahkan</b> dan dikunci. Tiada siapa boleh tambah atau ubah pusingan untuk mesin dan tarikh itu.'),
 ('', '<b>Rule:</b> you cannot verify a checklist that you filled in or checked yourself. The button stays grey until every round is checked.', '<b>Peraturan:</b> anda tidak boleh mengesahkan senarai semak yang anda sendiri isi atau semak. Butang kekal kelabu sehingga semua pusingan disemak.'),
]),
('records', 'all', 'See old checklists, download PDF and print', 'Lihat senarai semak lama, muat turun PDF dan cetak', [
 ('', 'To save a checklist as a file, open the machine and tap <b>Download PDF</b>. It works after at least one round is submitted. If the checklist is not verified yet, the PDF says NOT YET VERIFIED.', 'Untuk simpan senarai semak sebagai fail, buka mesin dan tekan <b>Muat turun PDF</b>. Ia berfungsi selepas sekurang-kurangnya satu pusingan dihantar. Jika senarai semak belum disahkan, PDF akan tertulis NOT YET VERIFIED.'),
 ('form-view', 'Scroll down to <b>Form view</b> to see the checklist in the F52 form layout. <b>Print F52</b> prints it on paper.', 'Tatal ke bawah ke <b>Paparan borang</b> untuk melihat senarai semak dalam susun atur borang F52. <b>Cetak F52</b> mencetaknya di atas kertas.'),
 ('records', 'For other days, tap the <b>Records</b> tab. Choose the dates and machine, tap <b>Show</b>, then tap a row to open it. Checkers, verifiers and Admin can also tap <b>Download (Excel CSV)</b>.', 'Untuk hari lain, tekan tab <b>Rekod</b>. Pilih tarikh dan mesin, tekan <b>Papar</b>, kemudian tekan satu baris untuk membukanya. Penyemak, pengesah dan Admin juga boleh tekan <b>Muat turun (Excel CSV)</b>.'),
]),
('admin', 'admin', 'Admin: users and checklists', 'Admin: pengguna dan senarai semak', [
 ('users', 'Tap the <b>Users</b> tab. Tick the functions each person may do, then tap <b>Save</b> on that row.<table class="mini"><tr><td><b>Inspect (Done by)</b></td><td>Fill in inspections</td></tr><tr><td><b>Check by</b></td><td>Sign or return each round</td></tr><tr><td><b>Verify by</b></td><td>Verify the day\'s checklist</td></tr><tr><td><b>Admin</b></td><td>Users and checklists</td></tr></table>To stop a person from signing in, untick <b>Active</b> and tap <b>Save</b>.', 'Tekan tab <b>Pengguna</b>. Tandakan fungsi yang dibenarkan untuk setiap orang, kemudian tekan <b>Simpan</b> pada baris itu.<table class="mini"><tr><td><b>Periksa (Done by)</b></td><td>Mengisi pemeriksaan</td></tr><tr><td><b>Check by</b></td><td>Tandatangan atau pulangkan setiap pusingan</td></tr><tr><td><b>Verify by</b></td><td>Mengesahkan senarai semak harian</td></tr><tr><td><b>Admin</b></td><td>Pengguna dan senarai semak</td></tr></table>Untuk halang seseorang daripada log masuk, buang tanda <b>Aktif</b> dan tekan <b>Simpan</b>.'),
 ('add-user', 'To add a person, tap <b>+ Add user</b>. Type the full name, a <b>username</b> (no email needed, no spaces) and a password of at least 8 characters. Tick the functions and tap <b>Add user</b>. Give the username and password to the person.', 'Untuk tambah orang, tekan <b>+ Tambah pengguna</b>. Taip nama penuh, <b>nama pengguna</b> (emel tidak diperlukan, tanpa ruang kosong) dan kata laluan sekurang-kurangnya 8 aksara. Tandakan fungsi dan tekan <b>Tambah pengguna</b>. Beri nama pengguna dan kata laluan kepada orang itu.'),
 ('', 'If a person forgets the password, tap <b>Reset password</b> on their row and set a new one.', 'Jika seseorang lupa kata laluan, tekan <b>Set semula kata laluan</b> pada baris mereka dan tetapkan yang baharu.'),
 ('setup', 'Tap the <b>Checklists</b> tab and choose a machine to change the parts, the condition criteria, the <b>Revision</b>, the <b>Effective Date</b> or the machine status. Tap <b>Save checklist</b>. Changes apply to new checklists only.', 'Tekan tab <b>Senarai semak</b> dan pilih mesin untuk mengubah bahagian, kriteria keadaan, <b>Revision</b>, <b>Effective Date</b> atau status mesin. Tekan <b>Simpan senarai semak</b>. Perubahan hanya terpakai kepada senarai semak baharu.'),
 ('', 'To correct a verified checklist, open it and tap <b>Reopen</b>. You must give a reason; it is kept in the change history.', 'Untuk membetulkan senarai semak yang telah disahkan, buka dan tekan <b>Buka semula</b>. Anda mesti beri sebab; ia disimpan dalam sejarah perubahan.'),
]),
]
FAQ = [
 ('I forgot my password.', 'Tell your Admin. The Admin sets a new password for you.', 'Saya lupa kata laluan.', 'Beritahu Admin. Admin akan tetapkan kata laluan baharu untuk anda.'),
 ('It says "Wrong username or password".', 'Check there is no space, and capital letters are correct. Tick <b>Show password</b> to see what you typed.', 'Keluar "Nama pengguna atau kata laluan salah".', 'Pastikan tiada ruang kosong dan huruf besar betul. Tandakan <b>Tunjuk kata laluan</b> untuk melihat apa yang ditaip.'),
 ('There is no Start inspection round button.', 'The machine is marked Not in use, or the checklist is already Verified, or the date is older than yesterday, or your account does not have the Inspect function. Ask your Admin.', 'Tiada butang Mula pusingan pemeriksaan.', 'Mesin ditanda Tidak digunakan, atau senarai semak sudah Disahkan, atau tarikh lebih lama daripada semalam, atau akaun anda tiada fungsi Periksa. Tanya Admin.'),
 ('The app says some parts are not yet inspected.', 'Scroll up and down. Every part needs one answer. Parts without an answer have a grey line on the left.', 'Aplikasi kata ada bahagian belum diperiksa.', 'Tatal ke atas dan ke bawah. Setiap bahagian perlu satu jawapan. Bahagian yang belum dijawab ada garisan kelabu di sebelah kiri.'),
 ('The internet stopped while I was filling in.', 'Keep going. Your answers stay on your phone and are sent when the signal comes back. Do not delete the draft.', 'Internet terputus semasa saya mengisi.', 'Teruskan. Jawapan anda kekal dalam telefon dan dihantar apabila isyarat kembali. Jangan padam draf.'),
 ('Download PDF is grey.', 'Nothing has been submitted for that machine and date yet.', 'Muat turun PDF berwarna kelabu.', 'Belum ada apa-apa yang dihantar untuk mesin dan tarikh itu.'),
 ('I cannot sign Check by or Verify by.', 'You cannot sign for your own inspection. Verify by also needs every round to be Checked first.', 'Saya tidak boleh tandatangan Check by atau Verify by.', 'Anda tidak boleh tandatangan untuk pemeriksaan sendiri. Verify by juga memerlukan semua pusingan Disemak dahulu.'),
 ('The screen looks old or a button is missing.', 'Refresh the page. On a PC press Ctrl + Shift + R. On a phone, close the app and open it again.', 'Skrin nampak lama atau butang tiada.', 'Muat semula halaman. Di PC tekan Ctrl + Shift + R. Di telefon, tutup aplikasi dan buka semula.'),
]
WHO = {'all': ('Everyone', 'Semua orang'), 'fill': ('Operator', 'Operator'), 'check': ('Checker', 'Penyemak'), 'verify': ('Verifier', 'Pengesah'), 'admin': ('Admin', 'Admin')}
def chapter(n, c, L):
    cid, who, ten, tbm, steps = c; i = 0 if L == 'en' else 1
    h = '<section class="ch who-%s" id="%s-%s"><h2><span class="no">%d</span>%s <span class="tag">%s</span></h2><ol class="steps">' % (who, cid, L, n, html.escape((ten, tbm)[i]), WHO[who][i])
    for img, en, bm in steps:
        pic = '<img class="%s" src="guide/g-%s-%s.jpg" alt="" loading="lazy">' % ('wide' if img in WIDE else 'tall', img, L) if img else ''
        h += '<li class="%s"><div class="tx">%s</div>%s</li>' % ('haspic' + (' w' if img in WIDE else '') if img else '', (en, bm)[i], pic)
    return h + '</ol></section>'
def lang_block(L):
    i = 0 if L == 'en' else 1
    T = lambda en, bm: (en, bm)[i]
    h = '<div class="lang" data-l="%s"%s>' % (L, '' if L == 'en' else ' hidden')
    h += '<header class="cover"><img src="gfb-logo.png" alt="GFB Food"><div><h1>%s</h1><p>%s</p><p class="small">%s</p></div></header>' % (
        T('Machine Inspection Checklist (F52)<br>User Guide', 'Senarai Semak Pemeriksaan Mesin (F52)<br>Panduan Pengguna'),
        T('Step by step, for operators, QC and executives. GFB Food Sdn Bhd.', 'Langkah demi langkah, untuk operator, QC dan eksekutif. GFB Food Sdn Bhd.'),
        T('Updated %s. The screens shown are from a test copy with made-up names.' % UPDATED, 'Dikemas kini %s. Skrin yang ditunjukkan adalah daripada salinan ujian dengan nama rekaan.' % UPDATED))
    h += '<nav class="toc no-print"><b>%s</b>' % T('Go to:', 'Pergi ke:') + ''.join('<a href="#%s-%s">%d. %s</a>' % (c[0], L, n + 1, html.escape(c[2 + i])) for n, c in enumerate(C)) + '<a href="#faq-%s">%d. %s</a></nav>' % (L, len(C) + 1, T('Common problems', 'Masalah biasa'))
    h += '<section class="ch flow"><h2>%s</h2><div class="fl"><div><b>1. Done by</b><span>%s</span></div><i>&#10140;</i><div><b>2. Check by</b><span>%s</span></div><i>&#10140;</i><div><b>3. Verify by</b><span>%s</span></div></div><p class="small">%s</p></section>' % (
        T('How the checklist moves', 'Aliran senarai semak'), T('Operator inspects the machine and submits', 'Operator memeriksa mesin dan hantar'), T('QC checks each round', 'QC menyemak setiap pusingan'), T('Production Executive verifies the day', 'Production Executive mengesahkan hari itu'),
        T('Every machine is inspected before production starts and at each product change-over (procedure P07). Each inspection is called a round.', 'Setiap mesin diperiksa sebelum pengeluaran bermula dan pada setiap pertukaran produk (prosedur P07). Setiap pemeriksaan dipanggil satu pusingan.'))
    h += ''.join(chapter(n + 1, c, L) for n, c in enumerate(C))
    h += '<section class="ch" id="faq-%s"><h2><span class="no">%d</span>%s</h2><table class="faq"><tr><th>%s</th><th>%s</th></tr>' % (L, len(C) + 1, T('Common problems', 'Masalah biasa'), T('Problem', 'Masalah'), T('What to do', 'Apa perlu dibuat'))
    h += ''.join('<tr><td>%s</td><td>%s</td></tr>' % ((q, a) if L == 'en' else (qb, ab)) for q, a, qb, ab in FAQ) + '</table></section></div>'
    return h
CSS = """
:root{--bg:#eef2f2;--surface:#fff;--ink:#152226;--muted:#5a6b70;--line:#d5dddd;--accent:#0d6b5f;--soft:#dcefeb;--ok:#2e7d3c;--bad:#b3261e}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.bar{position:sticky;top:0;z-index:5;background:var(--accent);color:#fff;display:flex;gap:8px;align-items:center;padding:8px 12px;flex-wrap:wrap}
.bar b{flex:1;min-width:120px}.bar button,.bar a{background:transparent;border:1px solid rgba(255,255,255,.55);color:#fff;border-radius:8px;padding:6px 10px;font:inherit;font-size:14px;cursor:pointer;text-decoration:none}
.bar button.on{background:#fff;color:var(--accent);font-weight:700}
main{max-width:900px;margin:0 auto;padding:14px 12px 60px}
.cover{display:flex;gap:16px;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px}
.cover img{height:76px;border-radius:8px}.cover h1{margin:0 0 6px;font-size:22px;line-height:1.25}.cover p{margin:0}.small{font-size:13.5px;color:var(--muted)}
.toc{display:flex;flex-wrap:wrap;gap:6px 8px;margin:12px 0;align-items:center}.toc a{background:var(--surface);border:1px solid var(--line);border-radius:99px;padding:5px 12px;text-decoration:none;color:var(--accent);font-size:14px;font-weight:600}
.ch{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px;margin-top:14px;scroll-margin-top:60px}
.ch h2{margin:0 0 12px;font-size:19px;line-height:1.3;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.no{background:var(--accent);color:#fff;border-radius:50%;width:32px;height:32px;display:inline-flex;align-items:center;justify-content:center;font-size:16px;flex:none}
.tag{font-size:12.5px;background:var(--soft);color:var(--accent);padding:2px 10px;border-radius:99px;font-weight:700}
.steps{list-style:none;margin:0;padding:0;counter-reset:s}
.steps li{counter-increment:s;display:grid;grid-template-columns:34px 1fr;gap:4px 10px;padding:12px 0;border-top:1px solid var(--line);align-items:start}
.steps li::before{content:counter(s);font-weight:800;color:var(--accent);border:2px solid var(--accent);border-radius:8px;width:30px;height:30px;display:flex;align-items:center;justify-content:center;font-size:15px}
.steps li.haspic{grid-template-columns:34px 1fr 250px}.steps li.haspic.w{grid-template-columns:34px 1fr}
.steps img{border:1px solid var(--line);border-radius:10px;width:100%;display:block;box-shadow:0 1px 5px rgba(0,0,0,.12)}
.steps li.w img{grid-column:2}
@media (max-width:640px){.steps li.haspic{grid-template-columns:34px 1fr}.steps li.haspic img{grid-column:2;max-width:300px}.cover{flex-direction:column;text-align:center}}
.url{display:inline-block;background:var(--soft);padding:3px 8px;border-radius:6px;font-weight:700;word-break:break-all;margin-top:4px}
table.mini{border-collapse:collapse;margin:8px 0;width:100%}table.mini td{border:1px solid var(--line);padding:6px 8px;vertical-align:top;font-size:15px}table.mini td:first-child{white-space:nowrap}
.ok{color:var(--ok)}.ng{color:var(--bad)}
.fl{display:flex;gap:8px;align-items:stretch;flex-wrap:wrap}.fl div{flex:1;min-width:150px;background:var(--soft);border-radius:10px;padding:10px}.fl b{display:block;color:var(--accent)}.fl span{font-size:14.5px}.fl i{align-self:center;font-style:normal;color:var(--accent);font-size:20px}
table.faq{border-collapse:collapse;width:100%}table.faq th,table.faq td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}table.faq th{background:var(--soft)}table.faq td:first-child{font-weight:600;width:38%}
[hidden]{display:none!important}
@media print{@page{size:A4;margin:12mm}body{background:#fff;font-size:11pt}.no-print,.bar{display:none!important}main{max-width:none;padding:0}
 .ch,.cover{border:0;padding:0;border-radius:0}.ch{page-break-before:always;break-before:page}.ch.flow{page-break-before:auto;break-before:auto;margin-top:8mm}
 .steps li{break-inside:avoid;page-break-inside:avoid;padding:3mm 0}.steps li.haspic{grid-template-columns:34px 1fr 62mm}.steps li.haspic.w{grid-template-columns:34px 1fr}.steps li.w img{max-width:150mm}
 .steps img{box-shadow:none}.no,.tag,.fl div,table.faq th,.url,.steps li::before{-webkit-print-color-adjust:exact;print-color-adjust:exact}table.faq tr{break-inside:avoid}}
"""
JS = """
var L='en';try{L=localStorage.getItem('mic_lang')||'en'}catch(e){}var q=(location.search.match(/lang=(en|bm)/)||[])[1];if(q)L=q;
function setL(l){L=l;document.querySelectorAll('.lang').forEach(function(d){d.hidden=d.dataset.l!==l});document.querySelectorAll('[data-setl]').forEach(function(b){b.classList.toggle('on',b.dataset.setl===l)});
 document.documentElement.lang=l==='bm'?'ms':'en';document.getElementById('back').textContent=l==='bm'?'Buka aplikasi':'Open the app';document.getElementById('prt').textContent=l==='bm'?'Cetak / simpan PDF':'Print / save as PDF';document.getElementById('dl').textContent='PDF';document.getElementById('dl').href='guide/GFB-Machine-Inspection-User-Guide-'+(l==='bm'?'BM':'EN')+'.pdf';try{localStorage.setItem('mic_lang',l)}catch(e){}}
document.addEventListener('click',function(e){var b=e.target.closest('[data-setl]');if(b)setL(b.dataset.setl)});setL(L);
"""
page = '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>GFB Machine Inspection Checklist (F52) - User Guide / Panduan Pengguna</title><meta name="theme-color" content="#0d6b5f"><link rel="icon" href="icon-192.png"><style>' + CSS + '</style></head><body>' \
  '<div class="bar no-print"><b>F52 User Guide / Panduan</b><button data-setl="en">English</button><button data-setl="bm">Bahasa Malaysia</button><button id="prt" onclick="window.print()">Print</button><a id="dl" href="#" download>PDF</a><a id="back" href="./">Open the app</a></div><main>' \
  + lang_block('en') + lang_block('bm') + '</main><script>' + JS + '</script></body></html>\n'
open(os.path.join(ROOT, 'guide.html'), 'w', encoding='utf-8').write(page)
# PDFs
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8767), functools.partial(Q, directory=ROOT)); threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    for L in ('en', 'bm'):
        pg = b.new_page(); pg.goto('http://127.0.0.1:8767/guide.html?lang=' + L); pg.evaluate("document.querySelectorAll('img').forEach(i=>i.loading='eager');0"); pg.wait_for_load_state('networkidle')
        pg.wait_for_function("Array.from(document.querySelectorAll('.lang:not([hidden]) img')).every(i=>i.complete&&i.naturalWidth>0)")
        pg.emulate_media(media='print'); pg.pdf(path=os.path.join(ROOT, 'guide', 'GFB-Machine-Inspection-User-Guide-%s.pdf' % L.upper()), format='A4', print_background=True, prefer_css_page_size=True); pg.close()
    b.close()
print('guide built')
