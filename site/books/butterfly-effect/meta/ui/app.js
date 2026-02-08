/* StoryOS Dashboard — vanilla JS SPA */
(function () {
  "use strict";

  let DATA = null;
  let mermaidReady = false;

  // ── Data loading ──────────────────────────

  async function loadData() {
    var resp = await fetch("../storyos.json");
    if (!resp.ok) throw new Error("Failed to load storyos.json");
    DATA = await resp.json();
    renderAll();
  }

  // ── Lightweight markdown → HTML ───────────

  function mdToHtml(src) {
    if (!src) return "";
    var lines = src.split("\n");
    var out = [];
    var inCode = false;
    var inList = false;
    var inTable = false;

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];

      // Fenced code blocks
      if (line.trimStart().startsWith("```")) {
        if (inCode) {
          out.push("</code></pre>");
          inCode = false;
        } else {
          if (inList) { out.push("</ul>"); inList = false; }
          if (inTable) { out.push("</tbody></table>"); inTable = false; }
          var lang = line.trim().slice(3);
          out.push('<pre class="md-code"><code' + (lang ? ' data-lang="' + esc(lang) + '"' : '') + '>');
          inCode = true;
        }
        continue;
      }
      if (inCode) {
        out.push(esc(line));
        continue;
      }

      var trimmed = line.trim();

      // Blank line
      if (!trimmed) {
        if (inList) { out.push("</ul>"); inList = false; }
        if (inTable) { out.push("</tbody></table>"); inTable = false; }
        continue;
      }

      // Headings
      var hm = trimmed.match(/^(#{1,6})\s+(.+)$/);
      if (hm) {
        if (inList) { out.push("</ul>"); inList = false; }
        if (inTable) { out.push("</tbody></table>"); inTable = false; }
        var level = hm[1].length;
        out.push("<h" + level + ">" + inline(hm[2]) + "</h" + level + ">");
        continue;
      }

      // Horizontal rule
      if (/^[-*_]{3,}$/.test(trimmed)) {
        if (inList) { out.push("</ul>"); inList = false; }
        if (inTable) { out.push("</tbody></table>"); inTable = false; }
        out.push("<hr>");
        continue;
      }

      // Table rows
      if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
        // Skip separator rows
        if (/^\|[\s:|-]+\|$/.test(trimmed)) continue;
        var cells = trimmed.slice(1, -1).split("|").map(function (c) { return c.trim(); });
        if (!inTable) {
          out.push('<table class="md-table"><thead><tr>');
          cells.forEach(function (c) { out.push("<th>" + inline(c) + "</th>"); });
          out.push("</tr></thead><tbody>");
          inTable = true;
        } else {
          out.push("<tr>");
          cells.forEach(function (c) { out.push("<td>" + inline(c) + "</td>"); });
          out.push("</tr>");
        }
        continue;
      }

      // Blockquote
      if (trimmed.startsWith("> ")) {
        if (inList) { out.push("</ul>"); inList = false; }
        out.push('<blockquote class="md-bq">' + inline(trimmed.slice(2)) + "</blockquote>");
        continue;
      }

      // Unordered list
      if (/^[-*+]\s/.test(trimmed)) {
        if (!inList) { out.push("<ul>"); inList = true; }
        out.push("<li>" + inline(trimmed.replace(/^[-*+]\s+/, "")) + "</li>");
        continue;
      }

      // Ordered list
      if (/^\d+\.\s/.test(trimmed)) {
        if (!inList) { out.push('<ol class="md-ol">'); inList = true; }
        out.push("<li>" + inline(trimmed.replace(/^\d+\.\s+/, "")) + "</li>");
        continue;
      }

      // Paragraph
      if (inList) { out.push("</ul>"); inList = false; }
      if (inTable) { out.push("</tbody></table>"); inTable = false; }
      out.push("<p>" + inline(trimmed) + "</p>");
    }
    if (inList) out.push("</ul>");
    if (inTable) out.push("</tbody></table>");
    if (inCode) out.push("</code></pre>");
    return out.join("\n");
  }

  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function inline(s) {
    s = esc(s);
    s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/\*(.+?)\*/g, "<em>$1</em>");
    s = s.replace(/__(.+?)__/g, "<strong>$1</strong>");
    s = s.replace(/_(.+?)_/g, "<em>$1</em>");
    s = s.replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>');
    s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
    return s;
  }

  // ── Navigation ────────────────────────────

  function initNav() {
    document.querySelectorAll(".nav-link").forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        switchView(link.dataset.view);
      });
    });
    var hash = location.hash.replace("#", "");
    if (hash && document.getElementById("view-" + hash)) {
      switchView(hash);
    }
  }

  function switchView(name) {
    document.querySelectorAll(".view").forEach(function (v) {
      v.classList.remove("active");
    });
    document.querySelectorAll(".nav-link").forEach(function (l) {
      l.classList.remove("active");
    });
    var el = document.getElementById("view-" + name);
    if (el) el.classList.add("active");
    var link = document.querySelector('[data-view="' + name + '"]');
    if (link) link.classList.add("active");
    location.hash = name;

    if (name === "graphs" && !mermaidReady && DATA) {
      initMermaid();
    }
  }

  // ── Search ────────────────────────────────

  function initSearch() {
    var input = document.getElementById("search");
    input.addEventListener("input", function () {
      var q = input.value.toLowerCase().trim();
      document.querySelectorAll("table tbody tr").forEach(function (tr) {
        var text = tr.textContent.toLowerCase();
        tr.classList.toggle("hidden", q.length > 0 && text.indexOf(q) === -1);
      });
      document.querySelectorAll(".entity-card").forEach(function (card) {
        var text = card.textContent.toLowerCase();
        card.style.display = q.length > 0 && text.indexOf(q) === -1 ? "none" : "";
      });
    });
  }

  // ── Render views ──────────────────────────

  function renderAll() {
    renderOverview();
    renderDocs();
    renderStoryMap();
    renderEntities();
    renderThreads();
    renderGraphsPlaceholder();
  }

  function h(tag, attrs, children) {
    var el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { el.setAttribute(k, attrs[k]); });
    if (typeof children === "string") el.textContent = children;
    else if (Array.isArray(children)) children.forEach(function (c) { if (c) el.appendChild(c); });
    else if (children instanceof Node) el.appendChild(children);
    return el;
  }

  function renderOverview() {
    var el = document.getElementById("view-overview");
    var s = DATA.stats;
    var book = DATA.book;

    el.innerHTML = "";
    el.appendChild(h("h2", null, book.title + " \u2014 " + (book.subtitle || "")));

    if (book.working_title) {
      el.appendChild(h("p", { style: "margin-bottom:.3rem;color:#5a4d3a" }, "Working title: " + book.working_title));
    }
    if (book.core_question) {
      el.appendChild(h("p", { style: "font-style:italic;margin-bottom:1.2rem;color:#5a4d3a" }, book.core_question));
    }

    var grid = h("div", { class: "stats" });
    [
      ["Chapters Planned", s.total_chapters],
      ["Chapters Drafted", s.chapters_drafted],
      ["Continuity Logged", s.continuity_chapters_logged + "/" + s.total_chapters],
      ["Revision Open", s.revision_queue_open],
    ].forEach(function (item) {
      grid.appendChild(h("div", { class: "stat-card" }, [
        h("div", { class: "label" }, item[0]),
        h("div", { class: "value" }, String(item[1])),
      ]));
    });
    el.appendChild(grid);

    var pins = DATA.dashboard_pins || [];
    if (pins.length) {
      var pinsDiv = h("div", { class: "pins" });
      pins.forEach(function (p) { pinsDiv.appendChild(h("span", { class: "pin" }, p)); });
      el.appendChild(pinsDiv);
    }

    el.appendChild(h("h3", null, "Arcs"));
    var arcList = h("ul", { style: "list-style:none;margin-bottom:1rem" });
    (DATA.arcs || []).forEach(function (arc) {
      arcList.appendChild(h("li", { style: "margin-bottom:.3rem" },
        "Arc " + arc.id + ": " + arc.title + " (Ch " + arc.chapter_range[0] + "\u2013" + arc.chapter_range[1] + ") \u2014 " + (arc.purpose || "")));
    });
    el.appendChild(arcList);
    el.appendChild(h("p", { style: "font-size:.78rem;color:#9ca3af" }, "Generated " + DATA.generated_at));
  }

  // ── Docs view with inline reader ──────────

  function renderDocs() {
    var el = document.getElementById("view-docs");
    el.innerHTML = "";
    el.appendChild(h("h2", null, "Docs Index"));

    // Detail panel (hidden by default)
    var detail = h("div", { id: "doc-detail", class: "doc-detail" });
    detail.style.display = "none";

    var backBtn = h("button", { class: "doc-back-btn" }, "\u2190 Back to index");
    var detailTitle = h("h3", { id: "doc-detail-title" });
    var detailPath = h("p", { class: "doc-detail-path" });
    var detailBody = h("div", { id: "doc-detail-body", class: "md-body" });
    detail.appendChild(backBtn);
    detail.appendChild(detailTitle);
    detail.appendChild(detailPath);
    detail.appendChild(detailBody);

    // Index panel
    var index = h("div", { id: "doc-index" });

    var docs = DATA.docs_index || [];
    var byCat = {};
    docs.forEach(function (d) {
      if (!byCat[d.category]) byCat[d.category] = [];
      byCat[d.category].push(d);
    });

    ["root", "bible", "outline", "review", "style", "schema", "agents", "assets"].forEach(function (cat) {
      var items = byCat[cat];
      if (!items || !items.length) return;
      index.appendChild(h("h3", null, cat.charAt(0).toUpperCase() + cat.slice(1)));

      var table = h("table");
      table.appendChild(h("thead", null, [
        h("tr", null, [h("th", null, "File"), h("th", null, "Synopsis"), h("th", null, "Modified")]),
      ]));
      var tbody = h("tbody");
      items.sort(function (a, b) { return a.path < b.path ? -1 : 1; });
      items.forEach(function (item) {
        var link = h("a", { href: "#", class: "doc-link" }, item.name);
        link.addEventListener("click", function (e) {
          e.preventDefault();
          showDoc(item, index, detail, detailTitle, detailPath, detailBody);
        });
        tbody.appendChild(h("tr", null, [
          h("td", null, link),
          h("td", null, (item.synopsis || "").slice(0, 80)),
          h("td", null, item.mtime_iso.slice(0, 10)),
        ]));
      });
      table.appendChild(tbody);
      index.appendChild(table);
    });

    backBtn.addEventListener("click", function () {
      detail.style.display = "none";
      index.style.display = "";
    });

    el.appendChild(detail);
    el.appendChild(index);
  }

  function showDoc(item, index, detail, titleEl, pathEl, bodyEl) {
    index.style.display = "none";
    detail.style.display = "";
    titleEl.textContent = item.name;
    pathEl.textContent = item.path;
    bodyEl.innerHTML = mdToHtml(item.content || "");
  }

  // ── Story Map ─────────────────────────────

  function renderStoryMap() {
    var el = document.getElementById("view-storymap");
    el.innerHTML = "";
    el.appendChild(h("h2", null, "Story Map"));

    var filtersDiv = h("div", { class: "filters" });
    var povSelect = h("select", { id: "filter-pov" });
    povSelect.appendChild(h("option", { value: "" }, "All POVs"));
    var povSet = {};
    (DATA.chapters || []).forEach(function (ch) { povSet[ch.pov] = true; });
    Object.keys(povSet).sort().forEach(function (p) {
      povSelect.appendChild(h("option", { value: p }, p));
    });

    var worldSelect = h("select", { id: "filter-world" });
    worldSelect.appendChild(h("option", { value: "" }, "All Worlds"));
    ["continental", "antarctic", "dual"].forEach(function (w) {
      worldSelect.appendChild(h("option", { value: w }, w));
    });

    filtersDiv.appendChild(h("label", null, "POV: "));
    filtersDiv.appendChild(povSelect);
    filtersDiv.appendChild(h("label", null, "World: "));
    filtersDiv.appendChild(worldSelect);
    el.appendChild(filtersDiv);

    var table = h("table", { id: "chapter-table" });
    table.appendChild(h("thead", null, [
      h("tr", null, [
        h("th", null, "Ch"), h("th", null, "Title"), h("th", null, "POV"),
        h("th", null, "World"), h("th", null, "Location"), h("th", null, "Timeline"),
        h("th", null, "Hook"),
      ]),
    ]));

    var tbody = h("tbody");
    (DATA.chapters || []).forEach(function (ch) {
      tbody.appendChild(h("tr", { "data-pov": ch.pov, "data-world": ch.world }, [
        h("td", null, String(ch.chapter)),
        h("td", null, ch.title || ""),
        h("td", null, ch.pov || ""),
        h("td", null, ch.world || ""),
        h("td", { style: "max-width:150px" }, ch.location || ""),
        h("td", null, ch.timeline || ""),
        h("td", { style: "max-width:200px;font-size:.8rem" }, (ch.hook || "").slice(0, 80)),
      ]));
    });
    table.appendChild(tbody);
    el.appendChild(table);

    function applyFilters() {
      var pov = povSelect.value;
      var world = worldSelect.value;
      tbody.querySelectorAll("tr").forEach(function (tr) {
        tr.classList.toggle("hidden", !((!pov || tr.dataset.pov === pov) && (!world || tr.dataset.world === world)));
      });
    }
    povSelect.addEventListener("change", applyFilters);
    worldSelect.addEventListener("change", applyFilters);
  }

  function renderEntities() {
    var el = document.getElementById("view-entities");
    el.innerHTML = "";
    el.appendChild(h("h2", null, "Entities"));

    var entities = DATA.entities || {};
    ["characters", "places", "concepts"].forEach(function (etype) {
      var items = entities[etype];
      if (!items || !items.length) return;
      el.appendChild(h("h3", null, etype.charAt(0).toUpperCase() + etype.slice(1)));
      var list = h("div", { class: "entity-list" });
      items.forEach(function (e) {
        var notes = (e.notes || []).join("; ");
        var tags = (e.voice_tags || e.tags || []).join(", ");
        var card = h("div", { class: "entity-card" }, [
          h("span", { class: "ename" }, e.name || e.id),
          h("span", { class: "emeta", style: "margin-left:.6rem" }, (e.culture || "") + (tags ? " \u00b7 " + tags : "")),
        ]);
        if (notes) card.appendChild(h("div", { style: "font-size:.82rem;margin-top:.2rem;color:#5a4d3a" }, notes));
        list.appendChild(card);
      });
      el.appendChild(list);
    });

    var dnt = DATA.do_not_translate_tokens || [];
    if (dnt.length) {
      el.appendChild(h("h3", null, "Do Not Translate"));
      var dntP = h("p", { style: "font-size:.85rem" });
      dntP.innerHTML = dnt.map(function (t) { return "<code>" + esc(t) + "</code>"; }).join(", ");
      el.appendChild(dntP);
    }
  }

  function renderThreads() {
    var el = document.getElementById("view-threads");
    el.innerHTML = "";
    el.appendChild(h("h2", null, "Threads & Promises"));

    el.appendChild(h("h3", null, "Threads"));
    var tList = h("div", { class: "entity-list" });
    (DATA.threads || []).forEach(function (t) {
      var card = h("div", { class: "entity-card" }, [
        h("span", { class: "ename" }, t.title),
        h("span", { class: "status-" + t.status, style: "margin-left:.6rem;font-size:.82rem" }, t.status),
        h("span", { class: "emeta", style: "margin-left:.6rem" },
          "Ch " + t.introduced_in_chapter + "\u2013" + t.last_touched_chapter),
      ]);
      if (t.next_action) {
        card.appendChild(h("div", { style: "font-size:.82rem;margin-top:.2rem" }, "Next: " + t.next_action));
      }
      tList.appendChild(card);
    });
    el.appendChild(tList);

    el.appendChild(h("h3", null, "Promises"));
    var table = h("table");
    table.appendChild(h("thead", null, [
      h("tr", null, [
        h("th", null, "Status"), h("th", null, "Question"),
        h("th", null, "Intro"), h("th", null, "Payoff"),
      ]),
    ]));
    var tbody = h("tbody");
    (DATA.promises || []).forEach(function (p) {
      tbody.appendChild(h("tr", null, [
        h("td", null, p.status === "closed" ? "\u2705" : "\uD83D\uDD35"),
        h("td", null, p.question || ""),
        h("td", null, "Ch " + p.introduced_in_chapter),
        h("td", null, "Ch " + (p.payoff_target_chapter || "?")),
      ]));
    });
    table.appendChild(tbody);
    el.appendChild(table);
  }

  function renderGraphsPlaceholder() {
    var el = document.getElementById("view-graphs");
    el.innerHTML = "";
    el.appendChild(h("h2", null, "Graphs"));
    el.appendChild(h("p", { style: "color:#9ca3af" }, "Diagrams will render when this tab is selected."));
  }

  function initMermaid() {
    if (typeof mermaid === "undefined") return;
    mermaid.initialize({ startOnLoad: false, theme: "neutral" });
    mermaidReady = true;

    var el = document.getElementById("view-graphs");
    el.innerHTML = "";
    el.appendChild(h("h2", null, "Graphs"));

    var diagrams = DATA.mermaid || {};
    var pending = [];
    [["Pipeline", "pipeline"], ["Arc Map", "arc_map"], ["Butterfly Graph", "butterfly"]].forEach(function (pair) {
      var code = diagrams[pair[1]];
      if (!code) return;
      el.appendChild(h("h3", null, pair[0]));
      var container = h("div", { class: "mermaid-container" });
      var pre = h("pre", { class: "mermaid" }, code);
      container.appendChild(pre);
      el.appendChild(container);
      pending.push(pre);
    });
    mermaid.run({ nodes: pending });
  }

  // ── Init ──────────────────────────────────

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    initSearch();
    loadData().catch(function (err) {
      document.getElementById("view-overview").textContent = "Error: " + err.message;
    });
  });
})();
