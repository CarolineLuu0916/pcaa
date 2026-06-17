(function () {
  var DATA = window.PCAA_DATA;
  var TRAIT_LABELS = {
    frugality: "节俭度", social: "社交性", risk_appetite: "风险偏好",
    conscientiousness: "责任心", openness: "开放性", agreeableness: "宜人性"
  };
  var BASELINE_COLOR = "#A6A4B0";
  var state = { persona: DATA.personas[0].id };

  function svg(tag, attrs) {
    var el = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (var k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  }
  function findPersona(id) { return DATA.personas.filter(function (p) { return p.id === id; })[0]; }
  function mean(arr) { return arr.reduce(function (a, b) { return a + b; }, 0) / arr.length; }

  // ---------------------------------------------------------------
  // Summary cards
  // ---------------------------------------------------------------
  function renderSummary() {
    var upliftVals = DATA.personas.map(function (p) {
      var c = DATA.consistency[p.id];
      return mean(c.experimental) - mean(c.baseline);
    });
    var avgUplift = mean(upliftVals);

    var divRatios = DATA.personas.map(function (p) {
      var d = DATA.diversity[p.id];
      return d.experimental / d.baseline;
    });
    var avgDivRatio = mean(divRatios);

    var totalAgentRound = DATA.personas.length * 2 * DATA.scenarios.length * DATA.rounds;
    var win = DATA.socialRealism.experimental_win;

    var cards = [
      { label: "MVP 总 Agent-Round", value: totalAgentRound, suffix: "", note: "3 persona × 2 条件 × 5 场景 × 10 轮" },
      { label: "人格一致性提升", value: "+" + avgUplift.toFixed(2), suffix: "", note: "实验组 − 对照组，cosine similarity 均值差", deltaUp: true },
      { label: "多样性保留率", value: (avgDivRatio * 100).toFixed(0), suffix: "%", note: "实验组熵值 / 对照组熵值，越接近 100% 越好", deltaUp: avgDivRatio > 0.85 },
      { label: "社会真实感胜率", value: win, suffix: "%", note: "盲测中实验组轨迹被判定更像真人的比例", deltaUp: true }
    ];

    var wrap = document.getElementById("summary-row");
    wrap.innerHTML = cards.map(function (c) {
      var deltaHtml = c.deltaUp !== undefined
        ? '<div class="delta ' + (c.deltaUp ? "up" : "down") + '">' + (c.deltaUp ? "▲ 符合假设方向" : "▼ 偏离假设") + '</div>'
        : "";
      return '<div class="summary-card">' +
        '<div class="label">' + c.label + '</div>' +
        '<div class="value">' + c.value + (c.suffix ? '<small>' + c.suffix + '</small>' : '') + '</div>' +
        deltaHtml +
        '<div class="panel-sub" style="margin-top:6px">' + c.note + '</div>' +
        '</div>';
    }).join("");
  }

  // ---------------------------------------------------------------
  // Line chart — Persona Consistency over rounds
  // ---------------------------------------------------------------
  function renderConsistencyChart() {
    var persona = findPersona(state.persona);
    var c = DATA.consistency[persona.id];
    var W = 560, H = 230, padL = 36, padR = 14, padT = 16, padB = 28;
    var innerW = W - padL - padR, innerH = H - padT - padB;
    var n = DATA.rounds;

    function x(i) { return padL + (innerW * i) / (n - 1); }
    function y(v) { return padT + innerH * (1 - v); }

    var root = svg("svg", { viewBox: "0 0 " + W + " " + H, width: "100%", height: H });

    // grid + y labels
    [0, 0.25, 0.5, 0.75, 1].forEach(function (v) {
      root.appendChild(svg("line", { x1: padL, x2: W - padR, y1: y(v), y2: y(v), stroke: "#E4E1ED", "stroke-width": 1 }));
      var t = svg("text", { x: 4, y: y(v) + 4, "font-size": 10, fill: "#8C8A99", "font-family": "JetBrains Mono, monospace" });
      t.textContent = v.toFixed(2);
      root.appendChild(t);
    });
    for (var i = 0; i < n; i++) {
      var t2 = svg("text", { x: x(i), y: H - 8, "font-size": 10, fill: "#8C8A99", "text-anchor": "middle" });
      t2.textContent = "R" + (i + 1);
      root.appendChild(t2);
    }

    function path(arr) {
      return arr.map(function (v, i) { return (i === 0 ? "M" : "L") + x(i) + "," + y(v); }).join(" ");
    }

    root.appendChild(svg("path", { d: path(c.baseline), fill: "none", stroke: BASELINE_COLOR, "stroke-width": 2, "stroke-dasharray": "4,4" }));
    root.appendChild(svg("path", { d: path(c.experimental), fill: "none", stroke: persona.color, "stroke-width": 2.5 }));

    c.experimental.forEach(function (v, i) {
      root.appendChild(svg("circle", { cx: x(i), cy: y(v), r: 2.6, fill: persona.color }));
    });

    document.getElementById("chart-consistency").innerHTML = "";
    document.getElementById("chart-consistency").appendChild(root);
    document.getElementById("legend-consistency").innerHTML =
      '<span><span class="dot" style="background:' + persona.color + '"></span>Experimental（Persona Lock）</span>' +
      '<span><span class="dot" style="background:' + BASELINE_COLOR + '"></span>Baseline（纯 LLM）</span>';
  }

  // ---------------------------------------------------------------
  // Grouped bar chart — Behavioral Diversity
  // ---------------------------------------------------------------
  function renderDiversityChart() {
    var W = 560, H = 230, padL = 36, padR = 14, padT = 16, padB = 32;
    var innerW = W - padL - padR, innerH = H - padT - padB;
    var maxV = 2;
    var groupW = innerW / DATA.personas.length;
    var barW = groupW * 0.3;

    var root = svg("svg", { viewBox: "0 0 " + W + " " + H, width: "100%", height: H });

    [0, 0.5, 1, 1.5, 2].forEach(function (v) {
      var yy = padT + innerH * (1 - v / maxV);
      root.appendChild(svg("line", { x1: padL, x2: W - padR, y1: yy, y2: yy, stroke: "#E4E1ED", "stroke-width": 1 }));
      var t = svg("text", { x: 4, y: yy + 4, "font-size": 10, fill: "#8C8A99", "font-family": "JetBrains Mono, monospace" });
      t.textContent = v.toFixed(1);
      root.appendChild(t);
    });

    DATA.personas.forEach(function (p, idx) {
      var d = DATA.diversity[p.id];
      var cx = padL + groupW * idx + groupW / 2;
      [["experimental", p.color], ["baseline", BASELINE_COLOR]].forEach(function (pair, j) {
        var v = d[pair[0]];
        var bh = innerH * (v / maxV);
        var bx = cx - barW - 4 + j * (barW + 8);
        root.appendChild(svg("rect", {
          x: bx, y: padT + innerH - bh, width: barW, height: bh,
          fill: pair[1], rx: 3
        }));
      });
      var lbl = svg("text", { x: cx, y: H - 10, "font-size": 11, fill: "#5B5A66", "text-anchor": "middle" });
      lbl.textContent = p.name;
      root.appendChild(lbl);
    });

    document.getElementById("chart-diversity").innerHTML = "";
    document.getElementById("chart-diversity").appendChild(root);
  }

  // ---------------------------------------------------------------
  // Radar chart — Persona Drift
  // ---------------------------------------------------------------
  function renderDriftRadar() {
    var persona = findPersona(state.persona);
    var drift = DATA.driftRadar[persona.id];
    var keys = Object.keys(TRAIT_LABELS);
    var W = 320, H = 280, cx = W / 2, cy = H / 2 - 6, R = 100;
    var n = keys.length;

    function point(i, v) {
      var angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      var r = R * v;
      return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
    }
    function ring(v) {
      var pts = [];
      for (var i = 0; i < n; i++) pts.push(point(i, v).join(","));
      return pts.join(" ");
    }
    function poly(values) {
      var pts = keys.map(function (k, i) { return point(i, values[k]).join(","); });
      return pts.join(" ");
    }

    var root = svg("svg", { viewBox: "0 0 " + W + " " + H, width: "100%", height: H });

    [0.25, 0.5, 0.75, 1].forEach(function (v) {
      root.appendChild(svg("polygon", { points: ring(v), fill: "none", stroke: "#E4E1ED", "stroke-width": 1 }));
    });
    keys.forEach(function (k, i) {
      var p0 = point(i, 0), p1 = point(i, 1.08);
      root.appendChild(svg("line", { x1: p0[0], y1: p0[1], x2: p1[0], y2: p1[1], stroke: "#E4E1ED", "stroke-width": 1 }));
      var lp = point(i, 1.28);
      var t = svg("text", { x: lp[0], y: lp[1], "font-size": 10.5, fill: "#5B5A66", "text-anchor": "middle" });
      t.textContent = TRAIT_LABELS[k];
      root.appendChild(t);
    });

    root.appendChild(svg("polygon", { points: poly(drift.initial), fill: "none", stroke: BASELINE_COLOR, "stroke-width": 1.5, "stroke-dasharray": "4,3" }));
    root.appendChild(svg("polygon", { points: poly(drift.final), fill: persona.color, "fill-opacity": "0.18", stroke: persona.color, "stroke-width": 2 }));

    document.getElementById("chart-radar").innerHTML = "";
    document.getElementById("chart-radar").appendChild(root);
    document.getElementById("legend-radar").innerHTML =
      '<span><span class="dot" style="background:' + persona.color + '"></span>第 ' + DATA.rounds + ' 轮（实验组）</span>' +
      '<span><span class="dot" style="background:' + BASELINE_COLOR + '"></span>第 1 轮（初始）</span>';
  }

  // ---------------------------------------------------------------
  // Social realism — stacked bar
  // ---------------------------------------------------------------
  function renderSocialRealism() {
    var s = DATA.socialRealism;
    var total = s.experimental_win + s.baseline_win + s.tie;
    var segs = [
      { label: "判定 Experimental 更真实", v: s.experimental_win, color: "#5B4FE5" },
      { label: "判定 Baseline 更真实", v: s.baseline_win, color: BASELINE_COLOR },
      { label: "无法判断 / 平局", v: s.tie, color: "#E4E1ED" }
    ];
    var W = 560, H = 60;
    var root = svg("svg", { viewBox: "0 0 " + W + " " + H, width: "100%", height: H });
    var xCursor = 0;
    segs.forEach(function (seg) {
      var w = (W * seg.v) / total;
      root.appendChild(svg("rect", { x: xCursor, y: 14, width: w, height: 28, fill: seg.color, rx: 0 }));
      if (w > 28) {
        var t = svg("text", { x: xCursor + w / 2, y: 32, "font-size": 12, fill: seg.color === "#E4E1ED" ? "#5B5A66" : "#fff", "text-anchor": "middle", "font-weight": "700" });
        t.textContent = seg.v + "%";
        root.appendChild(t);
      }
      xCursor += w;
    });
    document.getElementById("chart-realism").innerHTML = "";
    document.getElementById("chart-realism").appendChild(root);
    document.getElementById("legend-realism").innerHTML = segs.map(function (seg) {
      return '<span><span class="dot" style="background:' + seg.color + '"></span>' + seg.label + ' (' + seg.v + '%)</span>';
    }).join("");
  }

  // ---------------------------------------------------------------
  // Rounds effect — 10 vs 20 rounds social realism win-rate comparison
  // ---------------------------------------------------------------
  function renderRoundsComparison() {
    var wrap = document.getElementById("chart-rounds-comparison");
    var legendWrap = document.getElementById("legend-rounds-comparison");
    var runs = DATA.roundsComparison || [];
    if (runs.length === 0) {
      wrap.innerHTML = '<div class="panel-sub">暂无数据——需要同时存在 results/mvp_run.jsonl + results/mvp_run_long.jsonl 及对应的 social_realism 结果文件。</div>';
      legendWrap.innerHTML = "";
      return;
    }

    var runColors = ["#A6A4B0", "#5B4FE5", "#1F8A70", "#C97B1E"];
    var categories = [{ key: "__overall__", label: "总体" }].concat(
      DATA.personas.map(function (p) { return { key: p.id, label: p.name }; })
    );

    function expWinPct(run, key) {
      if (key === "__overall__") return run.experimental_win;
      var pp = run.perPersona.filter(function (x) { return x.personaId === key; })[0];
      if (!pp || !pp.total) return 0;
      return Math.round((100 * pp.experimentalWin) / pp.total);
    }

    var W = 560, H = 240, padL = 36, padR = 14, padT = 16, padB = 32;
    var innerW = W - padL - padR, innerH = H - padT - padB;
    var maxV = 100;
    var groupW = innerW / categories.length;
    var barW = Math.min(22, (groupW * 0.7) / runs.length);

    var root = svg("svg", { viewBox: "0 0 " + W + " " + H, width: "100%", height: H });

    [0, 25, 50, 75, 100].forEach(function (v) {
      var yy = padT + innerH * (1 - v / maxV);
      root.appendChild(svg("line", { x1: padL, x2: W - padR, y1: yy, y2: yy, stroke: "#E4E1ED", "stroke-width": 1 }));
      var t = svg("text", { x: 4, y: yy + 4, "font-size": 10, fill: "#8C8A99", "font-family": "JetBrains Mono, monospace" });
      t.textContent = v + "%";
      root.appendChild(t);
    });

    categories.forEach(function (cat, idx) {
      var cx = padL + groupW * idx + groupW / 2;
      var groupStart = cx - (barW * runs.length) / 2;
      runs.forEach(function (run, j) {
        var v = expWinPct(run, cat.key);
        var bh = innerH * (v / maxV);
        var bx = groupStart + j * barW;
        root.appendChild(svg("rect", {
          x: bx, y: padT + innerH - bh, width: barW - 3, height: bh,
          fill: runColors[j % runColors.length], rx: 3
        }));
        if (bh > 14) {
          var t = svg("text", {
            x: bx + (barW - 3) / 2, y: padT + innerH - bh + 11, "font-size": 9.5,
            fill: "#fff", "text-anchor": "middle", "font-weight": "700"
          });
          t.textContent = v;
          root.appendChild(t);
        }
      });
      var lbl = svg("text", { x: cx, y: H - 10, "font-size": 11, fill: "#5B5A66", "text-anchor": "middle" });
      lbl.textContent = cat.label;
      root.appendChild(lbl);
    });

    wrap.innerHTML = "";
    wrap.appendChild(root);
    legendWrap.innerHTML = runs.map(function (run, j) {
      return '<span><span class="dot" style="background:' + runColors[j % runColors.length] + '"></span>'
        + run.label + '（实验组胜率 ' + run.experimental_win + '%）</span>';
    }).join("") + '<span class="panel-sub" style="margin-top:6px">柱状高度 = 该 persona 在该轮次设置下 Experimental 被判定更像真人的比例</span>';
  }

  // ---------------------------------------------------------------
  // Sample data table
  // ---------------------------------------------------------------
  function renderTable() {
    var rows = DATA.sampleRows.map(function (r) {
      return "<tr>" +
        "<td>" + r.persona + "</td>" +
        '<td><span class="badge ' + (r.condition === "experimental" ? "exp" : "base") + '">' + (r.condition === "experimental" ? "Experimental" : "Baseline") + "</span></td>" +
        "<td>" + r.round + "</td>" +
        "<td>" + r.scenario + "</td>" +
        '<td class="action">' + r.action + "</td>" +
        "<td>" + r.mood + "</td>" +
        "<td>" + r.wealth + "</td>" +
        "</tr>";
    }).join("");
    document.getElementById("sample-table-body").innerHTML = rows;
  }

  // ---------------------------------------------------------------
  // Persona chips
  // ---------------------------------------------------------------
  function renderChips() {
    var wrap = document.getElementById("persona-chips");
    wrap.innerHTML = DATA.personas.map(function (p) {
      return '<button class="chip ' + (p.id === state.persona ? "active" : "") + '" data-id="' + p.id + '">' + p.name + "</button>";
    }).join("");
    Array.prototype.slice.call(wrap.querySelectorAll(".chip")).forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.persona = btn.getAttribute("data-id");
        renderChips();
        renderConsistencyChart();
        renderDriftRadar();
      });
    });
  }

  // ---------------------------------------------------------------
  // Demo / real data banner
  // ---------------------------------------------------------------
  function renderDataSourceNotice() {
    var banner = document.getElementById("dash-banner");
    var bannerText = document.getElementById("dash-banner-text");
    var footer = document.getElementById("page-footer");
    if (DATA.demo) {
      banner.style.display = "";
      bannerText.innerHTML = "当前展示的是<b>占位示例数据</b>，用于验证面板设计与交互。MVP 实验（300 agent-round）跑完后，把 <code>js/dashboard-data.js</code> 换成真实聚合结果即可，页面逻辑无需改动。";
      footer.innerHTML = '数据来源：占位示例（demo=true）· 详见 <a href="index.html#metrics">评测指标定义</a>';
    } else {
      banner.style.display = "none";
      footer.innerHTML = '数据来源：真实 MVP 实验（demo=false，300 agent-round）· 详见 <a href="index.html#metrics">评测指标定义</a>';
    }
  }

  function renderAll() {
    renderDataSourceNotice();
    renderSummary();
    renderChips();
    renderConsistencyChart();
    renderDiversityChart();
    renderDriftRadar();
    renderSocialRealism();
    renderRoundsComparison();
    renderTable();
  }

  document.addEventListener("DOMContentLoaded", renderAll);
})();
