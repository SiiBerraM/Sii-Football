/* Sii-Football API client - Owner: Berra. Use in SiiMatchMind (web + app). */
(function (root) {
  var BASE = "https://siiberram.github.io/Sii-Football/data/api/v1/";
  var TTL = 10 * 60 * 1000;

  function cacheGet(k) {
    try { var r = localStorage.getItem("siifb:" + k); return r ? JSON.parse(r) : null; } catch (e) { return null; }
  }
  function cacheSet(k, v) {
    try { localStorage.setItem("siifb:" + k, JSON.stringify({ t: Date.now(), v: v })); } catch (e) {}
  }
  async function get(path) {
    var c = cacheGet(path);
    if (c && Date.now() - c.t < TTL) return c.v;
    try {
      var r = await fetch(BASE + path);
      if (!r.ok) throw new Error("HTTP " + r.status);
      var j = await r.json();
      cacheSet(path, j);
      return j;
    } catch (e) {
      if (c) return c.v;
      throw e;
    }
  }
  function path(sport, file) { return sport ? "sports/" + sport + "/" + file + ".json" : file + ".json"; }

  function toMatch(m) {
    return {
      id: m.match_id, sport: m.sport, competition: m.competition,
      date: m.date_utc ? new Date(m.date_utc) : null, status: m.status,
      home: m.home_team.name, homeCode: m.home_team.code, homeScore: m.home_team.score,
      away: m.away_team.name, awayCode: m.away_team.code, awayScore: m.away_team.score,
      venue: m.venue, stale: m.is_stale, source: m.source_url
    };
  }

  root.SiiFootball = {
    sports: function () { return get("sports.json").then(function (j) { return j.data; }); },
    competitions: function (sport) { return get(path(sport, "competitions")).then(function (j) { return j.data; }); },
    fixtures: function (sport) { return get(path(sport, "fixtures")).then(function (j) { return j.data.map(toMatch); }); },
    results: function (sport) { return get(path(sport, "results")).then(function (j) { return j.data.map(toMatch); }); }
  };
})(typeof window !== "undefined" ? window : this);
