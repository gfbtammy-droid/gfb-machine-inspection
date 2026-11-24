// GFB Machine Inspection Checklist: lets an Admin create a username account for staff who have no email.
// Runs on Supabase (server side), so the secret key never reaches the browser or the repository.
// Only ever creates accounts of the form <username>@mic.gfbfood.com; it cannot touch real email accounts.
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const reply = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return reply({ ok: false, error: "method" }, 405);
  try {
    const url = Deno.env.get("SUPABASE_URL")!;
    const anon = Deno.env.get("SUPABASE_ANON_KEY")!;
    const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const authz = req.headers.get("Authorization") ?? "";

    // 1. the caller must be a signed-in, active Admin of the inspection app
    const caller = createClient(url, anon, {
      global: { headers: { Authorization: authz } },
      auth: { persistSession: false, autoRefreshToken: false },
    });
    const { data: isAdmin, error: e1 } = await caller.rpc("mic_can", { p_f: "admin" });
    if (e1 || isAdmin !== true) return reply({ ok: false, error: "not_admin" });

    // 2. validate
    const body = await req.json().catch(() => ({}));
    const username = String(body.username ?? "").trim().toLowerCase();
    const password = String(body.password ?? "");
    const name = String(body.name ?? "").trim().slice(0, 80);
    if (!/^[a-z0-9._+-]{3,60}$/.test(username)) return reply({ ok: false, error: "bad_username" });
    if (password.length < 8 || password.length > 72) return reply({ ok: false, error: "bad_password" });

    // 3. create the account, already confirmed, so no email is ever sent
    const admin = createClient(url, service, { auth: { persistSession: false, autoRefreshToken: false } });
    const { data, error } = await admin.auth.admin.createUser({
      email: username + "@mic.gfbfood.com",
      password,
      email_confirm: true,
      user_metadata: { name },
    });
    if (error) {
      const taken = /already|registered|exists/i.test(error.message);
      return reply({ ok: false, error: taken ? "taken" : "create_failed", detail: error.message });
    }
    return reply({ ok: true, id: data.user?.id });
  } catch (e) {
    return reply({ ok: false, error: "server", detail: String((e as Error)?.message ?? e) }, 500);
  }
});
