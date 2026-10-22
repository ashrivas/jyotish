"use strict";
const $ = (id) => document.getElementById(id);
const state = { output: null, fixtures: [], sources: null };
const SIGNS = [
  "Aries",
  "Taurus",
  "Gemini",
  "Cancer",
  "Leo",
  "Virgo",
  "Libra",
  "Scorpio",
  "Sagittarius",
  "Capricorn",
  "Aquarius",
  "Pisces",
];
const PLANETS = [
  "sun",
  "moon",
  "mars",
  "mercury",
  "jupiter",
  "venus",
  "saturn",
  "rahu",
  "ketu",
];
const ABBR = {
  sun: "Su",
  moon: "Mo",
  mars: "Ma",
  mercury: "Me",
  jupiter: "Ju",
  venus: "Ve",
  saturn: "Sa",
  rahu: "Ra",
  ketu: "Ke",
};
const PLACES = {
  lucknow: [26.8467, 80.9462, "Asia/Kolkata"],
  delhi: [28.6139, 77.209, "Asia/Kolkata"],
  mumbai: [19.076, 72.8777, "Asia/Kolkata"],
  kolkata: [22.5726, 88.3639, "Asia/Kolkata"],
  bengaluru: [12.9716, 77.5946, "Asia/Kolkata"],
  saratoga: [37.2638, -122.023, "America/Los_Angeles"],
  london: [51.5074, -0.1278, "Europe/London"],
  dubai: [25.2048, 55.2708, "Asia/Dubai"],
  singapore: [1.3521, 103.8198, "Asia/Singapore"],
  sydney: [-33.8688, 151.2093, "Australia/Sydney"],
};
const COLORS = [
  "#68836c",
  "#ba905b",
  "#788d9d",
  "#b7b79a",
  "#a78d92",
  "#809e94",
];
function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = String(text);
  return n;
}
function add(parent, ...children) {
  children.forEach((n) => parent.append(n));
  return parent;
}
function clear(id) {
  const n = typeof id === "string" ? $(id) : id;
  n.replaceChildren();
  return n;
}
function title(text) {
  return String(text)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
function badge(status) {
  return el(
    "span",
    "tag" +
      (["passed", "stable", "matched", "computed", "fires"].includes(status)
        ? ""
        : ["failed", "mismatch", "checks_failed_or_blocked"].includes(status)
          ? " red"
          : " amber"),
    title(status),
  );
}
function text(p, t, cls) {
  return add(p, el("p", cls, t));
}
function heading(p, t) {
  return add(p, el("h3", null, t));
}
function table(headers, rows) {
  const wrap = el("div", "table-wrap"),
    t = el("table"),
    thead = el("thead"),
    tr = el("tr");
  headers.forEach((h) => tr.append(el("th", null, h)));
  thead.append(tr);
  t.append(thead);
  const body = el("tbody");
  rows.forEach((row) => {
    const r = el("tr");
    row.forEach((value) => {
      const d = el("td");
      d.append(
        value instanceof Node ? value : document.createTextNode(String(value)),
      );
      r.append(d);
    });
    body.append(r);
  });
  t.append(body);
  wrap.append(t);
  return wrap;
}
async function api(path, options) {
  const response = await fetch(path, options);
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The server did not return JSON.");
  }
  if (!response.ok) {
    const d = data.detail || data.error || "Request failed";
    throw new Error(
      Array.isArray(d)
        ? d.map((x) => x.loc.join(".") + ": " + x.msg).join("\n")
        : String(d),
    );
  }
  return data;
}
function post(path, data) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}
function showTab(name) {
  document.querySelectorAll("[data-tab]").forEach((b) => {
    const selected = b.dataset.tab === name;
    b.setAttribute("aria-selected", String(selected));
    b.tabIndex = selected ? 0 : -1;
  });
  document.querySelectorAll(".panel").forEach((p) => {
    p.hidden = p.id !== "panel-" + name;
  });
}
document.querySelectorAll("[data-tab]").forEach((button) => {
  button.addEventListener("click", () => showTab(button.dataset.tab));
  button.addEventListener("keydown", (event) => {
    const tabs = [...document.querySelectorAll("[data-tab]")],
      i = tabs.indexOf(button);
    let next;
    if (event.key === "ArrowRight") next = (i + 1) % tabs.length;
    if (event.key === "ArrowLeft") next = (i + tabs.length - 1) % tabs.length;
    if (next !== undefined) {
      event.preventDefault();
      tabs[next].focus();
      showTab(tabs[next].dataset.tab);
    }
  });
});
$("place").addEventListener("change", () => {
  const p = PLACES[$("place").value];
  if (p) {
    ["latitude", "longitude", "timezone"].forEach(
      (k, i) => ($(k).value = p[i]),
    );
    $("offset").value = "";
    $("offset-source").value = "";
  } else $("coordinates").open = true;
});
function confidenceChanged() {
  const unknown = $("confidence").value === "unknown";
  $("birth-time").disabled = unknown;
  $("custom-window").hidden = $("confidence").value !== "custom";
}
$("confidence").addEventListener("change", confidenceChanged);
$("fixture").addEventListener("change", () => {
  const f = state.fixtures.find((f) => f.id === $("fixture").value);
  if (!f) return;
  const b = f.input.birth;
  $("birth-date").value = b.date;
  $("birth-time").value = b.time || "";
  $("latitude").value = b.latitude;
  $("longitude").value = b.longitude;
  $("timezone").value = b.timezone;
  $("confidence").value = b.confidence;
  $("place").value = "manual";
  $("fold").value = b.fold === undefined ? "" : String(b.fold);
  $("offset").value = b.civil_offset_seconds ?? "";
  $("offset-source").value = b.civil_offset_source || "";
  $("as-of").value = f.input.as_of.replace("Z", "");
  $("coordinates").open = true;
  confidenceChanged();
});
function requestInput() {
  const birth = {
    date: $("birth-date").value,
    time:
      $("confidence").value === "unknown"
        ? null
        : $("birth-time").value || null,
    latitude: Number($("latitude").value),
    longitude: Number($("longitude").value),
    timezone: $("timezone").value.trim(),
    place:
      $("place").value === "manual"
        ? "Manual coordinates"
        : $("place").selectedOptions[0].textContent,
    confidence: $("confidence").value,
  };
  if ($("confidence").value === "custom")
    birth.uncertainty_minutes = Number($("uncertainty").value);
  if ($("fold").value !== "") birth.fold = Number($("fold").value);
  if ($("offset").value !== "") {
    birth.civil_offset_seconds = Number($("offset").value);
    birth.civil_offset_source = $("offset-source").value.trim() || null;
  }
  if (!$("as-of").value)
    throw new Error("Supply the current-period calculation epoch.");
  return {
    birth,
    as_of: $("as-of").value + "Z",
    conventions: {
      nodes: $("nodes").value,
      dasha_year_days: Number($("year-days").value),
    },
    include_robustness: true,
  };
}
$("birth-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("form-error").hidden = true;
  $("compute").disabled = true;
  $("live-status").textContent =
    "Computing the chart and searching time-window boundaries…";
  try {
    const out = await post("/api/chart", requestInput());
    state.output = out;
    renderChart(out);
    renderUncertainty(out);
    renderEvidence(out);
    $("raw-output").textContent = JSON.stringify(out, null, 2);
    $("download").disabled = false;
    $("live-status").textContent =
      `Computed in ${out.runtime_ms.toFixed(0)} ms · ${out.robustness.event_count ?? 0} boundary events · ${out.provenance.swiss_ephemeris_version} Swiss Ephemeris`;
    showTab("chart");
  } catch (error) {
    $("form-error").textContent = error.message;
    $("form-error").hidden = false;
    $("live-status").textContent =
      "Input could not be resolved. See the message beside the form.";
  } finally {
    $("compute").disabled = false;
  }
});
function metric(parent, label, value, sub) {
  const n = el("div", "metric");
  add(
    n,
    el("div", "metric-label", label),
    el("div", "metric-value", value),
    el("div", "metric-sub", sub),
  );
  parent.append(n);
}
function date(v) {
  return String(v).slice(0, 10);
}
function chartSvg(output, division) {
  const ns = "http://www.w3.org/2000/svg",
    svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 300 300");
  svg.classList.add("kundli");
  svg.setAttribute("role", "img");
  svg.setAttribute(
    "aria-label",
    `North Indian ${division} chart at the nominal birth time`,
  );
  const draw = (tag, attrs) => {
    const n = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, String(v)));
    svg.append(n);
    return n;
  };
  draw("rect", { x: 1, y: 1, width: 298, height: 298, rx: 1, class: "grid" });
  draw("path", {
    d: "M0 0 L300 300 M300 0 L0 300 M150 0 L300 150 L150 300 L0 150 Z",
    class: "grid",
  });
  const locs = [
    [150, 65],
    [75, 19],
    [25, 69],
    [75, 140],
    [25, 219],
    [75, 269],
    [150, 215],
    [225, 269],
    [275, 219],
    [225, 140],
    [275, 69],
    [225, 19],
  ];
  const origin =
    output.vargas.lagna?.[division] ?? output.vargas.moon[division];
  locs.forEach(([x, y], i) => {
    const sign = (origin + i) % 12;
    const s = draw("text", { x, y, "text-anchor": "middle", class: "h-sign" });
    s.textContent = String(sign + 1);
    const names = PLANETS.filter(
      (p) => output.vargas[p][division] === sign,
    ).map((p) => ABBR[p] + (output.chart.planets[p].retrograde ? "℞" : ""));
    for (let k = 0; k < names.length; k += 3) {
      const t = draw("text", {
        x,
        y: y + 13 + (k / 3) * 11,
        "text-anchor": "middle",
        class: "h-planet",
      });
      t.textContent = names.slice(k, k + 3).join(" ");
    }
  });
  return svg;
}
function renderChart(out) {
  const p = clear("panel-chart");
  const top = el("div", "section-top");
  const group = el("div");
  add(
    group,
    el(
      "div",
      "eyebrow",
      "NOMINAL CHART · " + out.chart.house_basis.toUpperCase() + " BASIS",
    ),
    el("h2", null, out.input.birth.place),
  );
  add(top, group, badge("reference validation pending"));
  p.append(top);
  const grid = el("div", "chart-grid"),
    visual = el("div"),
    chartHeading = el("div", "chart-title"),
    selector = el("select");
  selector.setAttribute("aria-label", "Divisional chart");
  Object.keys(out.vargas.moon).forEach((k) => {
    const o = el("option", null, k);
    o.value = k;
    selector.append(o);
  });
  add(
    chartHeading,
    el("span", "micro", "North Indian · signs numbered 1–12"),
    selector,
  );
  visual.append(chartHeading);
  const imageHolder = el("div");
  imageHolder.append(chartSvg(out, "D1"));
  visual.append(imageHolder);
  selector.addEventListener("change", () =>
    imageHolder.replaceChildren(chartSvg(out, selector.value)),
  );
  const m = el("div", "metrics"),
    moon = out.chart.planets.moon;
  metric(
    m,
    out.chart.lagna ? "Ascendant" : "Chart basis",
    out.chart.lagna?.sign || "Moon chart",
    out.chart.lagna
      ? out.chart.lagna.degree_in_sign.toFixed(4) + "° · nominal time"
      : "No ascendant inferred",
  );
  metric(m, "Moon", moon.sign, moon.nakshatra + " · pada " + moon.pada);
  metric(
    m,
    "Civil time",
    out.resolved_time.local.slice(11, 19),
    out.resolved_time.local.slice(0, 10) + " · " + out.input.birth.timezone,
  );
  metric(
    m,
    "Julian day · TT",
    out.chart.jd_tt.toFixed(6),
    "Lahiri ayanamsa " + out.chart.ayanamsa_degrees.toFixed(6) + "°",
  );
  add(grid, visual, m);
  p.append(grid);
  out.technical_summary.forEach((r) => text(p, r.text, "summary-line"));
  heading(p, "Planetary positions");
  p.append(
    table(
      [
        "Graha",
        "Sidereal sign",
        "Degree",
        "House",
        "Nakshatra · pada",
        "D9",
        "Sign stability",
      ],
      PLANETS.map((name) => {
        const b = out.chart.planets[name],
          st = out.robustness.facts[name + ".sign_index"];
        return [
          title(name) + (b.retrograde ? " ℞" : ""),
          b.sign,
          b.degree_in_sign.toFixed(5) + "°",
          b.house,
          b.nakshatra + " · " + b.pada,
          SIGNS[out.vargas[name].D9],
          badge(st?.stability || "not_checked"),
        ];
      }),
    ),
  );
  text(
    p,
    "Degrees are displayed rounded; classification uses unrounded values. A stable sign does not imply stable houses, vargas or dasha dates.",
    "micro",
  );
  heading(p, "Current Vimshottari periods");
  const labels = ["Mahadasha", "Antardasha", "Pratyantardasha"];
  out.dasha.current.forEach((d, i) => {
    const row = el("div", "dasha-row");
    add(
      row,
      el("span", null, labels[i]),
      add(
        el("div"),
        el("b", null, title(d.lord)),
        el("div", "micro", date(d.start) + " → " + date(d.end) + " · UTC"),
      ),
    );
    p.append(row);
  });
  text(
    p,
    out.dasha.uncertainty.status === "not_certified"
      ? "Nominal dates only. Dasha uncertainty is not yet continuously certified; endpoint scenarios are included in the JSON."
      : "Dates use the exact supplied instant; this does not establish that the recorded birth time is exact.",
    "notice",
  );
  heading(p, "Ashtakavarga");
  if (out.ashtakavarga.status === "computed") {
    p.append(
      table(
        [
          "Graha",
          ...[
            "Ar",
            "Ta",
            "Ge",
            "Cn",
            "Le",
            "Vi",
            "Li",
            "Sc",
            "Sg",
            "Cp",
            "Aq",
            "Pi",
          ],
          "Total",
        ],
        [
          ...PLANETS.slice(0, 7).map((n) => [
            title(n),
            ...out.ashtakavarga.bhinna[n],
            out.ashtakavarga.bhinna[n].reduce((a, b) => a + b, 0),
          ]),
          ["Sarva", ...out.ashtakavarga.sarva, 337],
        ],
      ),
    );
    text(
      p,
      "Benefic points; seven-planet SAV excludes the separate Lagna BAV. Fixed totals are checked. Reference-software comparison is pending.",
      "micro",
    );
  } else text(p, out.ashtakavarga.reason, "notice");
  heading(p, "Panchang at birthplace sunrise");
  if (out.panchang.status === "computed") {
    const a = out.panchang;
    p.append(
      table(
        ["Sunrise local", "Vara", "Tithi", "Nakshatra", "Nitya yoga"],
        [
          [
            a.sunrise_local.slice(11, 19),
            a.vara,
            a.tithi + " · " + a.paksha,
            a.nakshatra,
            a.nitya_yoga_number,
          ],
        ],
      ),
    );
    text(p, a.definition + " PAC table validation pending.", "micro");
  } else text(p, out.panchang.reason, "notice");
  heading(p, "Validation limits");
  out.warnings.forEach((w) => text(p, w, "micro"));
  const d = el("details");
  add(
    d,
    el("summary", null, "Computations not yet implemented"),
    el("p", "micro", out.not_implemented.map(title).join(" · ")),
  );
  p.append(d);
  text(p, out.chart_hash, "hash");
}
function renderUncertainty(out) {
  const p = clear("panel-uncertainty");
  add(
    p,
    el("div", "eyebrow", "BIRTH-TIME ROBUSTNESS"),
    el("h2", null, "Which facts survive the time window?"),
  );
  const facts = Object.entries(out.robustness.facts),
    stable = facts.filter(([, v]) => v.stability === "stable"),
    changed = facts.filter(([, v]) => v.stability !== "stable");
  const cards = el("div", "mini-grid");
  [
    [stable.length, "Unanimous geometric facts"],
    [changed.length, "Sensitive / uncertified"],
    [out.robustness.event_count ?? 0, "Detected boundary events"],
  ].forEach(([n, t]) =>
    cards.append(
      add(el("div", "mini-card"), el("b", null, n), el("span", null, t)),
    ),
  );
  p.append(cards);
  text(
    p,
    out.resolved_time.window_start_utc +
      " → " +
      out.resolved_time.window_end_utc,
    "micro",
  );
  text(p, out.robustness.method, "micro");
  text(
    p,
    "Stable means unchanged across all event-delimited intervals in this numerical analysis. Duration fractions describe a time window, not the probability of a prediction.",
    "notice",
  );
  (out.robustness.limitations || []).forEach((s) => text(p, s, "micro"));
  heading(p, "Facts that change");
  if (!changed.length)
    text(
      p,
      "No geometric classification changed within this window. Timing and strength measures have separate validation limits.",
      "micro",
    );
  changed.forEach(([key, v]) => {
    const row = el("div", "fact-card"),
      line = el("div", "section-top");
    add(line, el("strong", null, key), badge(v.stability));
    row.append(line);
    const bar = el("div", "bar");
    v.alternatives.forEach((a, i) => {
      const segment = el("span");
      segment.style.width = a.duration_fraction * 100 + "%";
      segment.style.background = COLORS[i % COLORS.length];
      bar.append(segment);
    });
    row.append(bar);
    text(
      row,
      v.alternatives
        .map((a) => {
          const value = key.endsWith("sign_index") ? SIGNS[a.value] : a.value;
          return (
            value +
            " · " +
            (a.duration_fraction * 100).toFixed(2) +
            "% of window"
          );
        })
        .join(" / "),
      "fact-detail",
    );
    p.append(row);
  });
  const d = el("details");
  d.append(el("summary", null, "Inspect " + stable.length + " stable facts"));
  stable.forEach(([key, v]) =>
    text(
      d,
      key + " = " + (key.endsWith("sign_index") ? SIGNS[v.value] : v.value),
      "micro",
    ),
  );
  p.append(d);
}
function renderEvidence(out) {
  const p = clear("panel-evidence");
  add(
    p,
    el("div", "eyebrow", "NO RULE, NO PREDICTIVE CLAIM"),
    el("h2", null, "An inspectable evidence trail"),
  );
  text(p, out.evidence.message, "notice");
  text(
    p,
    "LLM interpretation remains disabled until computation dependencies and a reviewed classical rule base pass their gates. Model credentials have not been found in this checkout.",
    "micro",
  );
  heading(p, "Source-linked technical drafts");
  out.evidence.rules.forEach((r) => {
    const card = el("div", "rule-card"),
      top = el("div", "section-top");
    add(top, el("h3", null, r.name), badge(r.state));
    card.append(top);
    text(
      card,
      r.source_id + " · " + r.locator + " · " + r.review_status,
      "micro",
    );
    r.evidence.forEach((e) =>
      text(
        card,
        e.fact_id +
          " = " +
          (e.fact_id.endsWith("sign_index")
            ? SIGNS[e.value]
            : String(e.value)) +
          " · " +
          e.stability,
        "evidence-line",
      ),
    );
    text(card, r.caveat, "micro");
    text(
      card,
      "Eligible for prediction: no. A configuration alone does not prove an interpretive result.",
      "micro",
    );
    p.append(card);
  });
  heading(p, "Calculated attributes");
  p.append(
    table(
      ["Graha", "Dignity", "Sign lord", "Relationship", "Own houses"],
      PLANETS.slice(0, 7).map((n) => {
        const a = out.attributes[n];
        return [
          title(n),
          title(a.dignity),
          title(a.sign_lord),
          title(a.compound_relationship_to_sign_lord),
          a.owns_houses.join(", ") || "Unknown",
        ];
      }),
    ),
  );
  text(
    p,
    "Continuous Shadbala, combustion, planetary war and functional-nature adjudication remain pending. These technical attributes are not substitutes for them.",
    "notice",
  );
  heading(p, "Run provenance");
  p.append(
    el(
      "pre",
      null,
      JSON.stringify(
        {
          chart_hash: out.chart_hash,
          run_hash: out.run_hash,
          conventions: out.conventions,
          provenance: out.provenance,
          rule_base: out.evidence.version,
        },
        null,
        2,
      ),
    ),
  );
}
function renderSources(data) {
  const p = clear("source-list");
  data.sources.forEach((s) => {
    const row = el("div", "source-card"),
      link = el("a", null, s.title);
    link.href = s.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    add(
      row,
      link,
      el("p", null, s.author + " · " + title(s.role)),
      badge(s.status),
      el("p", null, s.scope),
      el("p", "micro", "Edition: " + (s.edition || "Not selected")),
      el("p", "micro", s.notes),
    );
    p.append(row);
  });
  const triage = clear("triage-list");
  data.triage.forEach((t) => {
    const n = el("div", "fact-card");
    add(
      n,
      el("strong", null, t.id),
      el("p", "micro", t.explanation),
      badge(t.status),
    );
    triage.append(n);
  });
}
function renderEvals(report, suites) {
  const p = clear("eval-results");
  if (report?.local_checks) {
    const c = el("div", "mini-grid");
    [
      [report.local_checks.passed, "Code tests passed"],
      [
        report.dual_engine?.comparisons ?? "—",
        "Independent longitude comparisons",
      ],
      ["Blocked", "Release readiness"],
    ].forEach(([n, t]) =>
      c.append(
        add(el("div", "mini-card"), el("b", null, n), el("span", null, t)),
      ),
    );
    p.append(c);
    if (report.dual_engine?.worst_by_planet) {
      const worst = Math.max(
        ...Object.values(report.dual_engine.worst_by_planet).map(
          (v) => v.arcseconds,
        ),
      );
      text(
        p,
        "Maximum measured longitude difference: " +
          worst.toFixed(6) +
          " arcseconds. Limit: 1 arcsecond. " +
          report.dual_engine.scope,
        "micro",
      );
    }
    const details = el("details");
    add(
      details,
      el("summary", null, "Test output"),
      el("pre", null, report.local_checks.output),
    );
    p.append(details);
  }
  heading(p, "The 19 specification suites");
  (report?.spec_suites || suites || []).forEach((s) => {
    const row = el("div", "suite-row"),
      body = el("div");
    add(body, el("strong", null, s.name), el("p", null, s.detail));
    add(
      row,
      el("span", "suite-no", String(s.id).padStart(2, "0")),
      body,
      badge(s.status),
    );
    p.append(row);
  });
}
async function waitForEval(jobId) {
  for (;;) {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    const job = await api("/api/evals/jobs/" + encodeURIComponent(jobId));
    if (job.state === "completed") return job.report;
    if (job.state === "failed") throw new Error(job.error);
  }
}
$("run-evals").addEventListener("click", async () => {
  const button = $("run-evals");
  button.disabled = true;
  button.textContent = "Running checks…";
  $("live-status").textContent =
    "Running the code tests and 7,000 independent longitude comparisons. Reference gaps will stay blocked.";
  try {
    const job = await post("/api/evals/run", {});
    const report = await waitForEval(job.job_id);
    renderEvals(report);
    $("live-status").textContent =
      title(report.status) + " · public-release gates remain blocked";
  } catch (e) {
    text(clear("eval-results"), e.message, "error");
    $("live-status").textContent =
      "Evaluation did not complete. The error is shown below.";
  } finally {
    button.disabled = false;
    button.textContent = "Run local evaluations";
  }
});
$("reference-file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  const target = clear("reference-results");
  try {
    if (file.size > 2000000) throw new Error("Reference file exceeds 2 MB.");
    const ref = JSON.parse(await file.text());
    text(target, "Comparing the supplied reference…", "micro");
    const report = await post("/api/compare", ref);
    target.replaceChildren();
    target.append(badge(report.status));
    text(target, report.note, "micro");
    target.append(el("pre", null, JSON.stringify(report, null, 2)));
  } catch (e) {
    text(target, e.message, "error");
  } finally {
    event.target.value = "";
  }
});
$("download").addEventListener("click", () => {
  if (!state.output) return;
  const blob = new Blob([JSON.stringify(state.output, null, 2)], {
      type: "application/json",
    }),
    url = URL.createObjectURL(blob),
    a = el("a");
  a.href = url;
  a.download = "jyoti-chart-" + state.output.chart_hash.slice(7, 19) + ".json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
async function init() {
  const results = await Promise.allSettled([
    api("/api/fixtures"),
    api("/api/sources"),
    api("/api/status"),
    api("/api/evals"),
  ]);
  if (results[0].status === "fulfilled") {
    state.fixtures = results[0].value.cases;
    state.fixtures.forEach((f) => {
      const o = el("option", null, title(f.id));
      o.value = f.id;
      $("fixture").append(o);
    });
  }
  if (results[1].status === "fulfilled") renderSources(results[1].value);
  if (results[2].status === "fulfilled")
    renderEvals(
      results[3].status === "fulfilled" ? results[3].value : null,
      results[2].value.spec_suites,
    );
  results
    .filter((r) => r.status === "rejected")
    .forEach((r) => console.error(r.reason));
  text(
    $("panel-evidence"),
    "Compute a chart to inspect its facts, draft rule matches and source references.",
    "micro",
  );
  confidenceChanged();
}
init();
