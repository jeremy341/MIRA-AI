const menuButton = document.querySelector(".menu-button");
const siteNav = document.querySelector(".site-nav");

if (menuButton && siteNav) {
  menuButton.addEventListener("click", () => {
    const isOpen = siteNav.classList.toggle("is-open");
    menuButton.setAttribute("aria-expanded", String(isOpen));
  });

  siteNav.addEventListener("click", (event) => {
    if (event.target.closest("a")) {
      siteNav.classList.remove("is-open");
      menuButton.setAttribute("aria-expanded", "false");
    }
  });
}

const revealItems = document.querySelectorAll("[data-reveal]");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (reducedMotion || !("IntersectionObserver" in window)) {
  revealItems.forEach((item) => item.classList.add("is-visible"));
} else {
  const revealObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { rootMargin: "0px 0px -8%", threshold: 0.08 },
  );

  revealItems.forEach((item) => revealObserver.observe(item));
}

document.querySelectorAll(".copy-button").forEach((button) => {
  button.addEventListener("click", async () => {
    const block = button.closest(".code-block");
    const code = block?.querySelector("code")?.textContent ?? "";

    try {
      await navigator.clipboard.writeText(code);
      button.textContent = "Copied";
      window.setTimeout(() => {
        button.textContent = "Copy";
      }, 1600);
    } catch {
      button.textContent = "Select text";
    }
  });
});

const docsSearch = document.querySelector("#docs-search");
const docSections = [...document.querySelectorAll(".doc-section")];
const searchStatus = document.querySelector("#search-status");
const docsEmpty = document.querySelector("#docs-empty");

if (docsSearch && docSections.length) {
  docsSearch.addEventListener("input", () => {
    const query = docsSearch.value.trim().toLowerCase();
    let visibleCount = 0;

    docSections.forEach((section) => {
      const searchableText = `${section.dataset.docTitle ?? ""} ${section.textContent}`.toLowerCase();
      const matches = !query || searchableText.includes(query);
      section.classList.toggle("is-filtered", !matches);
      if (matches) visibleCount += 1;
    });

    if (searchStatus) {
      searchStatus.textContent = query
        ? `${visibleCount} section${visibleCount === 1 ? "" : "s"} found`
        : "";
    }

    if (docsEmpty) docsEmpty.hidden = visibleCount !== 0;
  });
}

const docsLinks = [...document.querySelectorAll(".docs-nav a")];

if (docSections.length && docsLinks.length && "IntersectionObserver" in window) {
  const sectionObserver = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

      if (!visible) return;

      docsLinks.forEach((link) => {
        link.classList.toggle("active", link.hash === `#${visible.target.id}`);
      });
    },
    { rootMargin: "-18% 0px -70%", threshold: [0.05, 0.2] },
  );

  docSections.forEach((section) => sectionObserver.observe(section));
}

if (docSections.length > 1) {
  docSections.forEach((section, index) => {
    const sectionNav = document.createElement("nav");
    sectionNav.className = "doc-section-nav";
    sectionNav.setAttribute("aria-label", "Documentation section navigation");

    if (index > 0) {
      const previous = document.createElement("a");
      previous.href = "#" + docSections[index - 1].id;
      previous.textContent = "← Previous";
      sectionNav.append(previous);
    }

    if (index < docSections.length - 1) {
      const next = document.createElement("a");
      next.href = "#" + docSections[index + 1].id;
      next.textContent = "Next →";
      sectionNav.append(next);
    }

    section.append(sectionNav);
  });
}
const chartData = {
  detectors: {
    unit: "mAP50",
    min: 30,
    values: [
      ["EXP-005", 82.3],
      ["EXP-006", 39.4],
      ["EXP-008", 39.6],
      ["EXP-009", 72.8],
      ["EXP-011", 35.0],
      ["EXP-013", 55.1],
      ["EXP-014", 60.7],
      ["EXP-015", 56.0],
      ["EXP-016", 58.8],
      ["EXP-017", 59.3],
      ["EXP-018", 90.6],
      ["EXP-019", 90.58],
    ],
  },
  classifiers: {
    unit: "validation accuracy",
    min: 55,
    values: [
      ["EXP-001", 61.0],
      ["EXP-002", 84.28],
      ["EXP-003", 87.42],
      ["EXP-004", 87.42],
    ],
  },
  classes: [
    ["Glass", 90.8],
    ["Metal", 94.8],
    ["Paper", 88.7],
    ["Plastic", 81.1],
    ["Trash", 97.5],
  ],
  dataset: [
    ["Train", 5108],
    ["Validation", 415],
    ["Test", 1375],
  ],
};

function createDataTable(values, valueHeading) {
  const table = document.createElement("table");
  table.className = "chart-table";
  const caption = document.createElement("caption");
  caption.textContent = "Chart data";
  const head = document.createElement("thead");
  const headRow = document.createElement("tr");
  ["Label", valueHeading].forEach((text) => {
    const cell = document.createElement("th");
    cell.scope = "col";
    cell.textContent = text;
    headRow.append(cell);
  });
  head.append(headRow);
  const body = document.createElement("tbody");
  values.forEach(([label, value]) => {
    const row = document.createElement("tr");
    [label, String(value)].forEach((text) => {
      const cell = document.createElement("td");
      cell.textContent = text;
      row.append(cell);
    });
    body.append(row);
  });
  table.append(caption, head, body);
  return table;
}

function renderLineChart(element, data) {
  const namespace = "http://www.w3.org/2000/svg";
  const chartOnDark = Boolean(element.closest(".figure-section"));
  const gridColor = chartOnDark ? "rgba(248, 246, 239, .22)" : "#c7c8bf";
  const mutedColor = chartOnDark ? "#aebbb3" : "#69736d";
  const lineColor = chartOnDark ? "#f1a17f" : "#285c45";
  const pointColor = chartOnDark ? "#f1a17f" : "#285c45";
  const width = 900;
  const height = 340;
  const margin = { top: 18, right: 18, bottom: 58, left: 48 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const x = (index) => margin.left + (plotWidth * index) / (data.values.length - 1);
  const y = (value) => margin.top + plotHeight * (1 - (value - data.min) / (100 - data.min));
  const svg = document.createElementNS(namespace, "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("aria-hidden", "true");

  [40, 60, 80, 100].filter((value) => value >= data.min).forEach((value) => {
    const line = document.createElementNS(namespace, "line");
    line.setAttribute("x1", margin.left);
    line.setAttribute("x2", width - margin.right);
    line.setAttribute("y1", y(value));
    line.setAttribute("y2", y(value));
    line.setAttribute("stroke", gridColor);
    line.setAttribute("stroke-width", "1");
    const label = document.createElementNS(namespace, "text");
    label.setAttribute("x", margin.left - 10);
    label.setAttribute("y", y(value) + 4);
    label.setAttribute("text-anchor", "end");
    label.setAttribute("fill", mutedColor);
    label.setAttribute("font-family", "IBM Plex Mono, monospace");
    label.setAttribute("font-size", "10");
    label.textContent = `${value}%`;
    svg.append(line, label);
  });

  const area = document.createElementNS(namespace, "path");
  const linePoints = data.values.map(([, value], index) => `${x(index)},${y(value)}`);
  area.setAttribute("d", `M${linePoints.join(" L")} L${x(data.values.length - 1)},${y(data.min)} L${x(0)},${y(data.min)} Z`);
  area.setAttribute("fill", chartOnDark ? "rgba(241, 161, 127, .12)" : "rgba(40, 92, 69, .08)");
  const path = document.createElementNS(namespace, "polyline");
  path.setAttribute("points", linePoints.join(" "));
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", lineColor);
  path.setAttribute("stroke-width", "3");
  path.setAttribute("stroke-linejoin", "round");
  path.setAttribute("stroke-linecap", "round");
  svg.append(area, path);

  data.values.forEach(([labelText, value], index) => {
    const point = document.createElementNS(namespace, "circle");
    point.setAttribute("cx", x(index));
    point.setAttribute("cy", y(value));
    point.setAttribute("r", index === data.values.length - 1 ? "7" : "4.5");
    point.setAttribute("fill", index === data.values.length - 1 ? "#f1a17f" : pointColor);
    point.setAttribute("stroke", "#f8f6ef");
    point.setAttribute("stroke-width", "3");
    const title = document.createElementNS(namespace, "title");
    title.textContent = `${labelText}: ${value}% ${data.unit}`;
    point.append(title);
    const label = document.createElementNS(namespace, "text");
    label.setAttribute("x", x(index));
    label.setAttribute("y", height - 24);
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("fill", "#69736d");
    label.setAttribute("font-family", "IBM Plex Mono, monospace");
    label.setAttribute("font-size", data.values.length > 8 ? "8" : "10");
    label.textContent = labelText.replace("EXP-", "");
    svg.append(point, label);
  });

  element.setAttribute("role", "group");
  element.replaceChildren(svg, createDataTable(data.values, `${data.unit} (%)`));
}

function renderBarChart(element, values) {
  const fragment = document.createDocumentFragment();
  const columns = document.createElement("div");
  columns.className = "bar-column-grid";

  values.forEach(([label, value]) => {
    const column = document.createElement("div");
    column.className = "bar-column";

    const score = document.createElement("strong");
    score.textContent = value + "%";

    const track = document.createElement("div");
    track.className = "bar-track";
    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.setProperty("--value", String(value / 100));
    track.append(fill);

    const name = document.createElement("span");
    name.textContent = label;

    column.append(score, track, name);
    columns.append(column);
  });

  fragment.append(columns, createDataTable(values, "mAP50 (%)"));
  element.setAttribute("role", "group");
  element.replaceChildren(fragment);
}
function renderSplitChart(element, values) {
  const total = values.reduce((sum, [, value]) => sum + value, 0);
  const track = document.createElement("div");
  track.className = "split-track";
  values.forEach(([, value]) => {
    const segment = document.createElement("span");
    segment.style.width = `${(value / total) * 100}%`;
    track.append(segment);
  });
  const legend = document.createElement("div");
  legend.className = "split-legend";
  values.forEach(([label, value]) => {
    const item = document.createElement("div");
    item.style.setProperty("--share", `${(value / total) * 100}%`);
    const name = document.createElement("span");
    name.textContent = label;
    const count = document.createElement("strong");
    count.textContent = value.toLocaleString("en-US");
    item.append(name, count);
    legend.append(item);
  });
  element.setAttribute("role", "group");
  element.replaceChildren(track, legend, createDataTable(values, "Images"));
}

document.querySelectorAll("[data-chart]").forEach((element) => {
  const type = element.dataset.chart;
  if (type === "detectors" || type === "classifiers") renderLineChart(element, chartData[type]);
  if (type === "classes") renderBarChart(element, chartData.classes);
  if (type === "dataset") renderSplitChart(element, chartData.dataset);
});
