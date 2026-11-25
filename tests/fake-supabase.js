// In-memory stand-in for Supabase, for testing the screens only (dummy data, no real passwords).
// The real rules live in setup.sql; this copy follows them closely enough to click through every screen.
(function () {
  const U = [
    {id: 'u1', email: 'admin@demo.my', name: 'Demo Admin', funcs: ['fill', 'check', 'verify', 'admin'], active: true},
    {id: 'u2', email: 'ali@mic.gfbfood.com', name: 'Ali bin Abu', funcs: ['fill'], active: true},
    {id: 'u3', email: 'siti@mic.gfbfood.com', name: 'Siti QC', funcs: ['fill', 'check'], active: true},
    {id: 'u4', email: 'farah@demo.my', name: 'Farah Exec', funcs: ['fill', 'check', 'verify'], active: true}
  ];
  const DB = {users: U, tpls: [], insp: [], log: [], ctr: {}, del: []};
  window.__DB = DB;
  let me = null, n = 0;
  const today = () => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
  const E = m => { throw {message: m}; };
  const rk = () => !me || !me.active ? 0 : me.funcs.includes('admin') ? 4 : me.funcs.includes('verify') ? 3 : me.funcs.includes('check') ? 2 : 1;
  const has = x => me && me.active && me.funcs.includes(x);
  const need = r => { if (!me) E('Sila log masuk / Please sign in'); if (rk() < r) E('Akaun anda tidak dibenarkan untuk tindakan ini / Your account is not allowed to do this'); };
  const isNg = x => x.c === 'ng' || x.p === 'n';
  const rj = (r, full) => { const o = Object.assign({}, r); o.rv_pending = Object.values(r.items).filter(x => isNg(x) && !x.rv).length; o.rv_hold = Object.values(r.items).filter(x => x.rv && x.rv.d === 'hold').length; if (!full) { delete o.items; delete o.refs; } return o; };
  const findR = id => { for (const i of DB.insp) { const r = i.rounds.find(x => x.id === id); if (r) return [i, r]; } E('Pusingan tidak dijumpai / Round not found'); };
  const lg = (act, i, detail) => DB.log.push({at: new Date().toISOString(), name: me.name, act, insp: i && i.id, detail});
  const F = {
    mic_me(a) { if (!me) E('Please sign in'); if (a.p_name && !me.named) { me.name = a.p_name; me.named = true; } return {id: me.id, name: me.name, login: me.email.replace('@mic.gfbfood.com', ''), funcs: me.funcs, active: me.active, today: today()}; },
    mic_boot() { need(1); return {today: today(), templates: JSON.parse(JSON.stringify(DB.tpls))}; },
    mic_seed_templates(a) { need(4); let k = 0; a.p_data.forEach(t => { if (!DB.tpls.some(x => x.key === t.key)) { DB.tpls.push(JSON.parse(JSON.stringify(t))); k++; } }); return k; },
    mic_users_list() { need(4); return DB.users.filter(u => u.listed !== false).map(u => ({id: u.id, name: u.name, login: u.email.replace('@mic.gfbfood.com', ''), funcs: u.funcs, active: u.active, created_at: '2026-11-24T00:00:00Z', username: u.email.endsWith('@mic.gfbfood.com')})); },
    mic_save_user(a) { need(4); const u = DB.users.find(x => x.id === a.p_id); if (!(a.p_funcs.includes('admin') && a.p_active) && !DB.users.some(x => x.funcs.includes('admin') && x.active && x.id !== a.p_id)) E('Mesti ada sekurang-kurangnya seorang Admin aktif / There must be at least one active Admin'); u.name = a.p_name; u.funcs = a.p_funcs; u.active = a.p_active; },
    mic_add_user(a) { need(4); let e = a.p_login.toLowerCase(); if (!e.includes('@')) e += '@mic.gfbfood.com'; const u = DB.users.find(x => x.email === e); if (!u) return 'no_account'; if (u.listed !== false) return 'exists'; u.listed = true; u.name = a.p_name; u.funcs = a.p_funcs; u.active = a.p_active; return 'added'; },
    mic_reset_password(a) { need(4); if (a.p_password.length < 8) E('x / Password must be at least 8 characters'); DB.users.find(x => x.id === a.p_id).pw = a.p_password; },
    mic_save_template(a) { need(4); const i = DB.tpls.findIndex(t => t.key === a.p_key); DB.tpls[i] = JSON.parse(JSON.stringify(a.p_data)); },
    mic_delete_inspection(a) { need(4); if (!String(a.p_reason).trim()) E('x / Please give a reason'); const i = DB.insp.find(x => x.id === a.p_id); if (i.status === 'verified') E('x / A verified checklist must be reopened first'); DB.del.unshift({at: new Date().toISOString(), by: me.name, detail: {name: i.template.name, date: i.date, reason: a.p_reason, inspections: i.rounds.map(r => ({no: r.seq, batch: r.batch, status: r.status, done_by: r.done_name, check_by: r.check_name}))}}); DB.insp = DB.insp.filter(x => x !== i); },
    mic_deleted_log() { need(4); return DB.del; },
    mic_range(a) { need(1); return DB.insp.filter(i => i.rounds.length && i.date >= a.p_from && i.date <= a.p_to).map(i => ({id: i.id, machine: i.machine, date: i.date, status: i.status, verify_name: i.verify_name, verify_at: i.verify_at, formNo: i.template.formNo, rev: i.template.rev, name: i.template.name, rounds: i.rounds.map(r => rj(r, false))})); },
    mic_sheet(a) { need(1); const i = DB.insp.find(x => x.machine === a.p_machine && x.date === a.p_date); if (!i) return null; return JSON.parse(JSON.stringify(Object.assign({}, i, {rounds: i.rounds.map(r => rj(r, true)), log: rk() >= 2 ? DB.log.filter(l => l.insp === i.id) : []}))); },
    mic_export(a) { need(2); return DB.insp.filter(i => i.date >= a.p_from && i.date <= a.p_to).map(i => F.mic_sheet({p_machine: i.machine, p_date: i.date})); },
    mic_start_round(a) {
      need(1); if (!has('fill')) E('x / Your account is not allowed to do this'); const t = DB.tpls.find(x => x.key === a.p_machine); if (t.status === 'not_in_use') E('Mesin ini ditanda Tidak Digunakan / This machine is marked Not in use');
      let i = DB.insp.find(x => x.machine === a.p_machine && x.date === a.p_date);
      if (!i) { i = {id: 'i' + (++n), machine: a.p_machine, date: a.p_date, status: 'open', template: JSON.parse(JSON.stringify(t)), rounds: []}; DB.insp.push(i); }
      if (i.status === 'verified') E('Senarai semak ini telah disahkan / This checklist has already been verified');
      const d = i.rounds.find(r => r.done_by === me.id && r.status === 'draft'); if (d) return d.id;
      const r = {id: 'r' + (++n), seq: i.rounds.reduce((m, x) => Math.max(m, x.seq), 0) + 1, time: a.p_time, batch: '', status: 'draft', ng: 0, done_by: me.id, done_name: me.name, items: {}, refs: {}, updated_at: new Date().toISOString()};
      i.rounds.push(r); lg('round_start', i, {round: r.seq}); return r.id;
    },
    mic_save_round(a) {
      need(1); const [i, r] = findR(a.p_id); if (r.done_by !== me.id && rk() < 4) E('x / Only the person who started this round can fill it in'); if (r.status !== 'draft') E('Pusingan ini telah dihantar / This round has already been submitted');
      let missing = 0, bad = 0; const clean = {};
      i.template.sections.forEach(s => s.items.forEach(it => { const x = (a.p_items || {})[it.id]; if (x && x.c && (x.c === 'na' || x.p)) { if (x.c === 'ng' || x.p === 'n') { bad++; if (a.p_submit && !String(x.r || '').trim()) E('x / Please write a remark for every part that is Not OK or missing'); } clean[it.id] = {c: x.c, p: x.c === 'na' ? '' : x.p, r: x.r || ''}; } else missing++; }));
      if (a.p_submit && missing) E(missing + ' bahagian belum diperiksa / ' + missing + ' part(s) not yet inspected');
      if (a.p_submit && !a.p_time) E('Masa diperlukan / Time is required');
      if (a.p_submit && !/^\d{6}-\d+$/.test(r.batch)) { const ym = i.date.slice(0, 7).replace('-', ''); DB.ctr[ym] = (DB.ctr[ym] || 0) + 1; r.batch = ym + '-' + String(DB.ctr[ym]).padStart(3, '0'); }
      Object.assign(r, {time: a.p_time, refs: a.p_refs || {}, items: clean, ng: bad, status: a.p_submit ? 'submitted' : 'draft', submitted_at: a.p_submit ? new Date().toISOString() : null, updated_at: new Date().toISOString()});
      if (a.p_submit) { r.note = null; lg('round_submit', i, {round: r.seq}); }
      return {status: r.status, ng: bad, missing, batch: r.batch};
    },
    mic_delete_round(a) { need(1); const [i, r] = findR(a.p_id); if (r.status !== 'draft') E('x / Only a draft can be deleted'); i.rounds = i.rounds.filter(x => x !== r); if (!i.rounds.length) DB.insp = DB.insp.filter(x => x !== i); },
    mic_check_round(a) {
      need(1); if (!has('check')) E('x / Your account is not allowed to do this'); const [i, r] = findR(a.p_id); if (i.status === 'verified') E('x / This checklist has already been verified');
      if (a.p_ok) { if (r.status !== 'submitted') E('x / This round is not waiting for a check'); if (r.done_by === me.id) E('x / You cannot check your own inspection'); if (Object.values(r.items).some(x => isNg(x) && !x.rv)) E('x / Decide Can proceed or Hold for every Not OK part first'); Object.assign(r, {status: 'checked', check_by: me.id, check_name: me.name, check_at: new Date().toISOString(), note: a.p_note || null}); lg('round_check', i, {round: r.seq, note: a.p_note}); }
      else { if (!a.p_note) E('x / Please give a reason'); Object.assign(r, {status: 'draft', check_by: null, check_name: null, check_at: null, submitted_at: null, note: a.p_note}); lg('round_return', i, {round: r.seq, reason: a.p_note}); }
    },
    mic_review_item(a) { need(1); if (!has('check') && !has('verify')) E('x / Your account is not allowed to do this'); const [i, r] = findR(a.p_round); if (i.status === 'verified') E('x / This checklist has already been verified'); if (r.done_by === me.id) E('x / You cannot decide on your own inspection'); const x = r.items[a.p_item]; const d = a.p_sev === 'major' ? 'hold' : a.p_dec; if (d === 'go' && !String(a.p_note).trim()) E('x / Please write why the machine can proceed'); x.rv = {s: a.p_sev, d, r: a.p_note, by: me.id, name: me.name, at: new Date().toISOString()}; lg('item_review', i, {round: r.seq, note: a.p_note}); },
    mic_verify(a) {
      need(1); if (!has('verify')) E('x / Your account is not allowed to do this'); const i = DB.insp.find(x => x.id === a.p_id); if (i.rounds.some(r => r.status !== 'checked')) E('x / Every round must be checked (Check by) first');
      if (i.rounds.some(r => r.done_by === me.id || r.check_by === me.id)) E('x / You cannot verify a checklist that you filled in or checked yourself');
      Object.assign(i, {status: 'verified', verify_by: me.id, verify_name: me.name, verify_at: new Date().toISOString(), verify_note: a.p_note || null}); lg('verify', i, {note: a.p_note});
    },
    mic_reopen(a) { need(4); const i = DB.insp.find(x => x.id === a.p_id); Object.assign(i, {status: 'open', verify_by: null, verify_name: null, verify_at: null}); lg('reopen', i, {reason: a.p_reason}); }
  };
  window.supabase = {createClient(u_, k_, opt) {
    const tmp = opt && opt.auth && opt.auth.persistSession === false;
    return {
      auth: {
        async getSession() { return {data: {session: me ? {user: me} : null}}; },
        async signInWithPassword(c) { const u = DB.users.find(x => x.email === c.email); if (!u) return {error: {message: 'Invalid login credentials'}}; me = u; return {data: {session: {}}, error: null}; },
        async signUp(c) { if (DB.users.some(x => x.email === c.email)) return {data: null, error: {message: 'User already registered'}}; const u = {id: 'u' + (DB.users.length + 1), email: c.email, name: c.options.data.name, funcs: ['fill'], active: false, listed: tmp ? false : true}; DB.users.push(u); if (!tmp) me = u; return {data: {session: tmp ? null : {}, user: {id: u.id}}, error: null}; },
        async signOut() { if (!tmp) me = null; return {}; },
        async updateUser() { return {error: null}; },
        async resetPasswordForEmail() { return {error: null}; },
        onAuthStateChange() { return {data: {subscription: {unsubscribe() {}}}}; }
      },
      functions: {async invoke(name, o) { const b = o.body; if (!has('admin')) return {data: {ok: false, error: 'not_admin'}, error: null}; const e = b.username + '@mic.gfbfood.com'; if (DB.users.some(x => x.email === e)) return {data: {ok: false, error: 'taken'}, error: null}; DB.users.push({id: 'u' + (DB.users.length + 1), email: e, name: b.name, funcs: ['fill'], active: false, listed: false}); return {data: {ok: true}, error: null}; }},
      async rpc(fn, args) { try { const d = F[fn](args || {}); return {data: d === undefined ? null : JSON.parse(JSON.stringify(d)), error: null}; } catch (e) { if (e && e.message && !(e instanceof Error)) return {data: null, error: e}; throw e; } }
    };
  }};
})();
