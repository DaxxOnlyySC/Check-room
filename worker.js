export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    if (url.pathname === "/room" || url.pathname === "/get-rooms" || url.pathname === "/process") {
      const mapType = url.searchParams.get("id");
      if (!mapType) {
        return new Response(JSON.stringify({ error: "Missing ?id= parameter" }), {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }

      const t = Math.floor(Date.now() / 1000);
      const rid = crypto.randomUUID().replace(/-/g, "").slice(0, 32);

      const apiUrl = `http://openroom-inaz.miniworldgame.com:8080/server/room?cmd=get_map_room_list_show_oversea&map_type=${mapType}&time=${t}&uin=${env.UIN}&auth=${env.AUTH}&ver=1.7.15&apdqs=1&requestid=${rid}&channel=410&country=ID&language=1`;

      try {
        const resp = await fetch(apiUrl);
        const data = await resp.text();
        return new Response(data, {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 502,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
    }

    return new Response(JSON.stringify({
      name: "Mini World Room Proxy",
      usage: "GET /room?id=<map_type>",
    }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  },
};
