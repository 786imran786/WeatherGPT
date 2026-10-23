/* ===== API layer: the only file that talks to your FastAPI backend =====
   Set BASE_URL to your FastAPI server. If a request fails and USE_MOCK_FALLBACK
   is true, sample data is returned so the UI still renders.

   Endpoints expected:
   GET  /api/weather?city=Phagwara
        -> {city, datetime, temp, feels_like, humidity, wind, pressure, visibility, condition, icon}
   GET  /api/forecast?city=Phagwara
        -> {hourly:[{time,icon,temp}], daily:[{day,icon,min,max}]}
   GET  /api/alerts?region=Punjab
        -> [{level:"high"|"medium", title, message, source, time}]
   GET  /api/locations
        -> [{city, temp, icon}]
   POST /api/chat   body {message, city, language}
        -> {reply}
   Temperatures are in Celsius; the UI converts to Fahrenheit if chosen. */
const API_CONFIG = { BASE_URL: "http://localhost:8000", USE_MOCK_FALLBACK: true };

async function request(path, options) {
  const res = await fetch(API_CONFIG.BASE_URL + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error("API " + res.status + " on " + path);
  return res.json();
}

const MOCK = {
  weather: { city: "Phagwara, Punjab", datetime: new Date().toISOString(), temp: 32, feels_like: 35, humidity: 62, wind: 12, pressure: 1008, visibility: 8, condition: "Partly Cloudy", icon: "⛅" },
  forecast: {
    hourly: [["Now","⛅",32],["11 AM","⛅",33],["12 PM","⛅",34],["1 PM","⛅",34],["2 PM","⛅",33],["3 PM","⛅",32],["4 PM","🌧️",31],["5 PM","🌧️",30]].map(a => ({ time: a[0], icon: a[1], temp: a[2] })),
    daily: [["Today","🌧️",24,34],["Tue","⛅",25,33],["Wed","🌧️",25,32],["Thu","⛅",24,31],["Fri","☀️",24,32]].map(a => ({ day: a[0], icon: a[1], min: a[2], max: a[3] })),
  },
  alerts: [
    { level: "high", title: "Heavy Rainfall Alert", message: "Moderate to heavy rainfall expected in Punjab on 13–14 Aug.", source: "IMD", time: "2 hours ago" },
    { level: "medium", title: "Thunderstorm Warning", message: "Thunderstorm with lightning likely in nearby districts.", source: "IMD", time: "5 hours ago" },
  ],
  locations: [{ city: "Phagwara", temp: 32, icon: "⛅" }, { city: "Delhi", temp: 31, icon: "☀️" }, { city: "Mumbai", temp: 28, icon: "🌧️" }, { city: "Bengaluru", temp: 27, icon: "☁️" }],
};

async function withFallback(fn, mock) {
  try { return await fn(); }
  catch (e) {
    console.warn(e.message);
    if (API_CONFIG.USE_MOCK_FALLBACK) return mock;
    throw e;
  }
}

const api = {
  weather: city => withFallback(() => request("/api/weather?city=" + encodeURIComponent(city)), MOCK.weather),
  forecast: city => withFallback(() => request("/api/forecast?city=" + encodeURIComponent(city)), MOCK.forecast),
  alerts: (region = "Punjab") => withFallback(() => request("/api/alerts?region=" + encodeURIComponent(region)), MOCK.alerts),
  locations: () => withFallback(() => request("/api/locations"), MOCK.locations),
  chat: (message, city, language) => withFallback(
    () => request("/api/chat", { method: "POST", body: JSON.stringify({ message, city, language }) }),
    { reply: "Backend not reachable. Start your FastAPI server and check BASE_URL in api.js." }
  ),
};
