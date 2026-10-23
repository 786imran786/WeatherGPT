const CHIPS = ["What's the weather today in Phagwara?", "Will it rain tomorrow?", "Give me a 5-day forecast for Delhi.", "Is there any heatwave alert in Punjab?", "What should I wear tomorrow?", "Show weather map for India."];
let unit = "C", city = "Phagwara", cache = {};
const $ = id => document.getElementById(id);
const cv = t => (unit === "C" ? Math.round(t) : Math.round(t * 9 / 5 + 32)) + "°";
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function renderWeather(w) {
  $("hcity").textContent = w.city; $("hloc").textContent = w.city;
  $("hdate").textContent = new Date(w.datetime).toLocaleString("en-IN", { weekday: "short", day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  $("htemp").textContent = cv(w.temp) + unit; $("hicon").textContent = w.icon; $("hcond").textContent = w.condition;
  $("hf").textContent = cv(w.feels_like) + unit; $("hh").textContent = w.humidity + "%";
  $("hw").textContent = w.wind + " km/h"; $("hp").textContent = w.pressure + " hPa"; $("hv").textContent = w.visibility + " km";
}
function renderForecast(f) {
  $("hourly").innerHTML = f.hourly.map(h => `<div class="c">${esc(h.time)}<span class="i">${h.icon}</span><b>${cv(h.temp)}</b></div>`).join("");
  const d = f.daily.map(x => `<div class="c">${esc(x.day)}<span class="i">${x.icon}</span><b>${cv(x.min)} | ${cv(x.max)}</b></div>`).join("");
  $("daily").innerHTML = d; $("daily2").innerHTML = d;
}
function renderAlerts(list) {
  const html = list.map(a => `<div class="al ${a.level === "high" ? "r" : "y"}"><span>${a.level === "high" ? "🔺" : "⚠️"}</span><div><b>${esc(a.title)}</b>${esc(a.message)}<small>Source: ${esc(a.source)} • ${esc(a.time)}</small></div></div>`).join("") || '<p style="color:var(--mu)">No active alerts.</p>';
  $("alertlist").innerHTML = html; $("alertlist2").innerHTML = html;
}
function renderLocations(list) {
  const p = list.map(l => `<button class="pl" data-city="${esc(l.city)}"><span class="i">${l.icon}</span><span><small>${esc(l.city)}</small><b>${cv(l.temp)}${unit}</b></span></button>`).join("");
  $("pop").innerHTML = p; $("pop2").innerHTML = p;
}
function paint() { if (cache.w) renderWeather(cache.w); if (cache.f) renderForecast(cache.f); if (cache.l) renderLocations(cache.l); }

async function loadCity(c) {
  city = c;
  $("hcond").textContent = "Loading…";
  const [w, f] = await Promise.all([api.weather(c), api.forecast(c)]);
  cache.w = w; cache.f = f; paint();
}
async function init() {
  $("chips").innerHTML = CHIPS.map(c => `<button class="chip" data-q="${esc(c)}">💬 ${esc(c)}</button>`).join("");
  const [alerts, locs] = await Promise.all([api.alerts("Punjab"), api.locations(), loadCity(city)]);
  cache.l = locs; renderLocations(locs); renderAlerts(alerts);
}

function show(p) {
  document.querySelectorAll(".pg").forEach(e => e.classList.toggle("on", e.id === p));
  document.querySelectorAll(".nav").forEach(e => e.classList.toggle("on", e.dataset.p === p));
}
async function ask(q) {
  q = (q || "").trim(); if (!q) return;
  const log = $("log");
  log.insertAdjacentHTML("beforeend", `<div class="m u">${esc(q)}</div><div class="m b">…</div>`);
  $("q").value = ""; log.scrollTop = log.scrollHeight;
  const bubble = log.lastElementChild;
  try { const r = await api.chat(q, city, "en"); bubble.textContent = r.reply; }
  catch (e) { bubble.textContent = "Something went wrong. Please try again."; }
  log.scrollTop = log.scrollHeight;
}

document.addEventListener("click", e => {
  const t = e.target.closest("[data-p],[data-go],[data-q],[data-city]"); if (!t) return;
  if (t.dataset.p) show(t.dataset.p);
  if (t.dataset.go) show(t.dataset.go);
  if (t.dataset.q) ask(t.dataset.q);
  if (t.dataset.city) { loadCity(t.dataset.city); show("home"); }
});
$("send").onclick = () => ask($("q").value);
$("q").addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask($("q").value); } });
$("search").addEventListener("keydown", e => { if (e.key === "Enter") { const v = $("search").value; $("search").value = ""; show("home"); ask(v); $("askcard").scrollIntoView({ behavior: "smooth" }); } });
$("unit").onchange = function () { unit = this.value; paint(); };
$("theme").onclick = function () {
  const r = document.documentElement, d = r.dataset.theme === "dark" || (!r.dataset.theme && matchMedia("(prefers-color-scheme:dark)").matches);
  r.dataset.theme = d ? "light" : "dark"; this.textContent = d ? "☀️" : "🌙";
};
init();
