
import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  BarChart3,
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  Clock3,
  Database,
  FileSearch,
  LayoutDashboard,
  LoaderCircle,
  MessageSquareText,
  Search,
  Send,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Wallet,
  X,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

const money = (value) => {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) {
    return "—";
  }

  const amount = Number(value);

  if (Math.abs(amount) >= 1e12) return `₹${(amount / 1e12).toFixed(2)}T`;
  if (Math.abs(amount) >= 1e9) return `₹${(amount / 1e9).toFixed(2)}B`;
  if (Math.abs(amount) >= 1e7) return `₹${(amount / 1e7).toFixed(2)}Cr`;

  return `₹${amount.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
};

const percent = (value, digits = 2) => {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) {
    return "—";
  }

  return `${Number(value).toFixed(digits)}%`;
};

const number = (value, digits = 2) => {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) {
    return "—";
  }

  return Number(value).toFixed(digits);
};

const shortDate = (value) => {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return String(value);

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "2-digit",
  });
};

const companyName = (row) => row?.Company || row?.company || "Unknown company";

function MetricCard({ label, value, detail, icon: Icon, tone = "teal" }) {
  return (
    <article className="metric-card">
      <div className="metric-card-top">
        <span className="metric-label">{label}</span>
        <span className={`metric-icon ${tone}`}>
          <Icon size={19} />
        </span>
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-detail">{detail}</div>
    </article>
  );
}

function StatusPill({ status }) {
  const value = status || "Not assessed";
  const verification = value.toLowerCase().includes("verification");
  const clear = value.toLowerCase().includes("no configured flags");

  return (
    <span
      className={`status-pill ${
        verification ? "warning" : clear ? "clear" : "neutral"
      }`}
    >
      <span className="status-dot" />
      {value}
    </span>
  );
}

function EmptyState({
  icon: Icon = Database,
  title,
  detail,
}) {
  return (
    <div className="empty-state">
      <Icon size={26} />
      <strong>{title}</strong>
      <span>{detail}</span>
    </div>
  );
}

export default function App() {
  const [dashboard, setDashboard] = useState(null);
  const [selectedCompany, setSelectedCompany] = useState("");
  const [history, setHistory] = useState([]);
  const [companyDetail, setCompanyDetail] = useState(null);
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [apiError, setApiError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");
  const [chartMode, setChartMode] = useState("price");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Ask me about company financials, risk flags, revenue contraction, or the metrics in this dashboard. My answers use the platform’s available dataset.",
    },
  ]);
  const [asking, setAsking] = useState(false);

  // Stable references prevent unnecessary useMemo recalculations.
  const companies = useMemo(() => dashboard?.companies ?? [], [dashboard]);
  const marketSummary = useMemo(
    () => dashboard?.market_summary ?? [],
    [dashboard],
  );

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoadingDashboard(true);
      setApiError("");

      try {
        const response = await fetch(`${API_BASE}/api/dashboard`);

        if (!response.ok) {
          throw new Error(`Dashboard API returned HTTP ${response.status}`);
        }

        const data = await response.json();

        if (cancelled) return;

        setDashboard(data);

        const companyRows = data.companies || [];

        if (companyRows.length > 0) {
          setSelectedCompany((current) =>
            current &&
            companyRows.some((item) => companyName(item) === current)
              ? current
              : companyName(
                  companyRows.find((item) => item.Company === "ITC") ||
                    companyRows[0],
                ),
          );
        }
      } catch (error) {
        if (!cancelled) {
          setApiError(
            `Could not connect to the backend. Make sure FastAPI is running at ${API_BASE}. Details: ${error.message}`,
          );
        }
      } finally {
        if (!cancelled) setLoadingDashboard(false);
      }
    }

    loadDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedCompany) return undefined;

    let cancelled = false;

    async function loadCompanyHistory() {
      setLoadingHistory(true);

      try {
        const encoded = encodeURIComponent(selectedCompany);

        const [historyResponse, detailResponse] = await Promise.all([
          fetch(
            `${API_BASE}/api/company/${encoded}/history?metric=${encodeURIComponent(
              "Net Profit Margin %",
            )}`,
          ),
          fetch(`${API_BASE}/api/company/${encoded}`),
        ]);

        if (!historyResponse.ok) {
          throw new Error(
            `History API returned HTTP ${historyResponse.status}`,
          );
        }

        const historyData = await historyResponse.json();
        let detailData = null;

        if (detailResponse.ok) {
          detailData = await detailResponse.json();
        }

        if (cancelled) return;

        setHistory(historyData.history || []);

        setCompanyDetail({
          ...(detailData || {}),
          market_prices: historyData.market_prices || [],
        });
      } catch {
        if (!cancelled) {
          setHistory([]);
          setCompanyDetail(null);
        }
      } finally {
        if (!cancelled) setLoadingHistory(false);
      }
    }

    loadCompanyHistory();

    return () => {
      cancelled = true;
    };
  }, [selectedCompany]);

  const selectedRow = useMemo(
    () =>
      companies.find((item) => companyName(item) === selectedCompany) || null,
    [companies, selectedCompany],
  );

  const selectedMarket = useMemo(
    () =>
      marketSummary.find((item) => item.company === selectedCompany) || null,
    [marketSummary, selectedCompany],
  );

  const filteredCompanies = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();

    return companies.filter((item) => {
      const matchesSearch =
        !term ||
        companyName(item).toLowerCase().includes(term) ||
        String(item.Ticker || "").toLowerCase().includes(term);

      const status = String(item["Review Status"] || "").toLowerCase();

      const matchesRisk =
        riskFilter === "all" ||
        (riskFilter === "review" && status.includes("verification")) ||
        (riskFilter === "clear" && status.includes("no configured flags"));

      return matchesSearch && matchesRisk;
    });
  }, [companies, searchTerm, riskFilter]);

  const chartData = useMemo(() => {
    if (chartMode === "margin") {
      return history
        .filter(
          (item) => item.value !== null && item.value !== undefined,
        )
        .map((item) => ({
          date: item.period,
          label: shortDate(item.period),
          value: Number(item.value),
        }));
    }

    return (companyDetail?.market_prices || []).map((item) => ({
      date: item.date,
      label: shortDate(item.date),
      value: Number(item.close),
    }));
  }, [chartMode, history, companyDetail]);

  const latestChartValue = chartData.length
    ? chartData[chartData.length - 1].value
    : null;

  const firstChartValue = chartData.length ? chartData[0].value : null;

  const chartChange =
    latestChartValue !== null &&
    firstChartValue !== null &&
    firstChartValue !== 0
      ? ((latestChartValue - firstChartValue) /
          Math.abs(firstChartValue)) *
        100
      : null;

  const flaggedCompanies = useMemo(
    () =>
      companies.filter((item) =>
        String(item["Review Status"] || "")
          .toLowerCase()
          .includes("verification"),
      ),
    [companies],
  );

  async function submitQuestion(event) {
    event?.preventDefault();

    const prompt = question.trim();

    if (!prompt || asking) return;

    setMessages((current) => [
      ...current,
      { role: "user", text: prompt },
    ]);
    setQuestion("");
    setAsking(true);

    try {
      const response = await fetch(`${API_BASE}/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: prompt }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail || `Question API returned HTTP ${response.status}`,
        );
      }

      const answer =
        typeof data === "string"
          ? data
          : data.answer ||
            data.response ||
            data.result ||
            data.message ||
            JSON.stringify(data, null, 2);

      setMessages((current) => [
        ...current,
        { role: "assistant", text: String(answer) },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          text: `I couldn't retrieve an answer. Check that the backend is running and /api/ask is available. ${error.message}`,
        },
      ]);
    } finally {
      setAsking(false);
    }
  }

  const suggestedQuestions = [
    "Why was ITC flagged?",
    "Which companies have revenue contraction?",
    "Explain Reliance Industries",
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Activity size={24} strokeWidth={2.4} />
          </div>
          <div className="brand-copy">
            <strong>
              FinSight<span> AI</span>
            </strong>
            <small>FINANCIAL INTELLIGENCE</small>
          </div>
        </div>

        <div className="sidebar-section-label">WORKSPACE</div>

        <nav className="sidebar-nav">
          <a className="nav-item active" href="#overview">
            <LayoutDashboard size={18} />
            <span>Overview</span>
          </a>
          <a className="nav-item" href="#market">
            <TrendingUp size={18} />
            <span>Market analytics</span>
          </a>
          <a className="nav-item" href="#companies">
            <Building2 size={18} />
            <span>Company intelligence</span>
          </a>
          <a className="nav-item" href="#risk">
            <ShieldCheck size={18} />
            <span>Risk monitoring</span>
            {flaggedCompanies.length > 0 && (
              <span className="nav-count">{flaggedCompanies.length}</span>
            )}
          </a>
          <a className="nav-item" href="#assistant">
            <MessageSquareText size={18} />
            <span>AI research assistant</span>
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-status">
            <span className={`connection-light ${apiError ? "offline" : ""}`} />
            <div>
              <strong>
                {apiError ? "Backend disconnected" : "Data workspace"}
              </strong>
              <small>
                {apiError ? "Check API connection" : "Local API connection"}
              </small>
            </div>
          </div>

          <div className="sidebar-footer">
            <div className="avatar">FS</div>
            <div className="profile-copy">
              <strong>Research workspace</strong>
              <small>Financial analytics</small>
            </div>
            <ChevronDown size={16} />
          </div>
        </div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span className="breadcrumb-slash">/</span>
            <strong>Overview</strong>
          </div>

          <div className="topbar-actions">
            <span className="environment-badge">
              <span className="status-dot" />
              Research environment
            </span>
            <button
              className="icon-button"
              type="button"
              aria-label="Notifications"
            >
              <Bell size={18} />
              <span className="notification-dot" />
            </button>
            <div className="topbar-date">
              <Clock3 size={15} />
              <span>
                Reporting period: {shortDate(dashboard?.latest_reporting_period)}
              </span>
            </div>
          </div>
        </header>

        <div className="page-content">
          {apiError && (
            <div className="error-banner">
              <ShieldAlert size={19} />
              <div>
                <strong>Unable to load dashboard data</strong>
                <p>{apiError}</p>
              </div>
            </div>
          )}

          <section className="welcome-row">
            <div>
              <div className="eyebrow">
                <Sparkles size={14} /> EVIDENCE-GROUNDED ANALYTICS
              </div>
              <h1>
                Financial intelligence, <span>in focus.</span>
              </h1>
              <p className="page-subtitle">
                A consolidated view of market performance, company fundamentals,
                and risk signals.
              </p>
            </div>

            <button
              className="primary-button"
              type="button"
              onClick={() => window.location.reload()}
            >
              <Activity size={17} />
              Refresh workspace
            </button>
          </section>

          <section className="metric-grid" aria-label="Dashboard metrics">
            <MetricCard
              label="Companies tracked"
              value={
                loadingDashboard
                  ? "…"
                  : dashboard?.company_count ?? companies.length
              }
              detail="Across the current coverage universe"
              icon={BriefcaseBusiness}
              tone="teal"
            />
            <MetricCard
              label="Require verification"
              value={
                loadingDashboard
                  ? "…"
                  : dashboard?.verification_required_count ??
                    flaggedCompanies.length
              }
              detail="Review underlying financial figures"
              icon={ShieldAlert}
              tone="amber"
            />
            <MetricCard
              label="Business signals"
              value={
                loadingDashboard
                  ? "…"
                  : dashboard?.companies_with_signals ?? 0
              }
              detail="Preliminary rules-based indicators"
              icon={BarChart3}
              tone="blue"
            />
            <MetricCard
              label="Latest reporting period"
              value={
                dashboard?.latest_reporting_period
                  ? shortDate(dashboard.latest_reporting_period)
                  : "—"
              }
              detail="Most recent period in the dataset"
              icon={Database}
              tone="violet"
            />
          </section>

          <section className="content-grid main-panels" id="market">
            <article className="panel chart-panel">
              <div className="panel-heading">
                <div>
                  <div className="panel-kicker">MARKET & FUNDAMENTALS</div>
                  <h2>Performance explorer</h2>
                  <p>
                    Inspect price history or annual net profit margin for a
                    selected company.
                  </p>
                </div>

                <div className="select-wrap">
                  <select
                    aria-label="Select company"
                    value={selectedCompany}
                    onChange={(event) => setSelectedCompany(event.target.value)}
                  >
                    {companies.map((item) => (
                      <option
                        key={companyName(item)}
                        value={companyName(item)}
                      >
                        {companyName(item)}
                      </option>
                    ))}
                  </select>
                  <ChevronDown size={15} />
                </div>
              </div>

              <div className="chart-summary">
                <div>
                  <span className="summary-label">
                    {chartMode === "price"
                      ? "Latest available close"
                      : "Latest net profit margin"}
                  </span>
                  <div className="chart-main-value">
                    {chartData.length
                      ? chartMode === "price"
                        ? money(latestChartValue)
                        : percent(latestChartValue)
                      : "—"}
                  </div>
                </div>

                <div
                  className={`chart-change ${
                    chartChange === null
                      ? ""
                      : chartChange >= 0
                        ? "positive"
                        : "negative"
                  }`}
                >
                  {chartChange !== null &&
                    (chartChange >= 0 ? (
                      <ArrowUpRight size={16} />
                    ) : (
                      <ArrowDownRight size={16} />
                    ))}
                  {chartChange === null
                    ? "Not available"
                    : `${chartChange >= 0 ? "+" : ""}${chartChange.toFixed(2)}%`}
                  <small>
                    {chartMode === "price"
                      ? "Change across available history"
                      : "Change across available periods"}
                  </small>
                </div>
              </div>

              <div className="chart-controls">
                <button
                  type="button"
                  className={chartMode === "price" ? "chart-tab active" : "chart-tab"}
                  onClick={() => setChartMode("price")}
                >
                  <TrendingUp size={15} /> Share price
                </button>
                <button
                  type="button"
                  className={chartMode === "margin" ? "chart-tab active" : "chart-tab"}
                  onClick={() => setChartMode("margin")}
                >
                  <BarChart3 size={15} /> Profit margin
                </button>
                <span className="chart-period">
                  {chartMode === "price"
                    ? "Historical daily data"
                    : "Annual reporting data"}
                </span>
              </div>

              <div className="chart-container">
                {loadingHistory ? (
                  <div className="chart-loading">
                    <LoaderCircle className="spin" size={25} />
                    Loading chart data…
                  </div>
                ) : chartData.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={chartData}
                      margin={{ top: 12, right: 8, left: 0, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient
                          id="priceGradient"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="0%"
                            stopColor="#31d6b0"
                            stopOpacity={0.26}
                          />
                          <stop
                            offset="95%"
                            stopColor="#31d6b0"
                            stopOpacity={0.01}
                          />
                        </linearGradient>
                      </defs>
                      <CartesianGrid
                        stroke="#253346"
                        strokeDasharray="3 5"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="label"
                        tick={{ fill: "#7f91a8", fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        minTickGap={32}
                      />
                      <YAxis
                        tick={{ fill: "#7f91a8", fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        width={64}
                        domain={["auto", "auto"]}
                        tickFormatter={(value) =>
                          chartMode === "price" ? `₹${value}` : `${value}%`
                        }
                      />
                      <Tooltip
                        contentStyle={{
                          background: "#111d2b",
                          border: "1px solid #2b3b4f",
                          borderRadius: 10,
                          color: "#e8eef7",
                          fontSize: 12,
                        }}
                        labelStyle={{
                          color: "#9aabc0",
                          marginBottom: 5,
                        }}
                        formatter={(value) => [
                          chartMode === "price" ? money(value) : percent(value),
                          chartMode === "price"
                            ? "Share price"
                            : "Net profit margin",
                        ]}
                      />
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke="#31d6b0"
                        strokeWidth={2}
                        fill="url(#priceGradient)"
                        activeDot={{
                          r: 4,
                          fill: "#31d6b0",
                          stroke: "#0d1825",
                          strokeWidth: 2,
                        }}
                        dot={false}
                        connectNulls={false}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState
                    icon={BarChart3}
                    title="No chart data available"
                    detail="The selected company has no usable observations for this view."
                  />
                )}
              </div>

              <div className="chart-footnote">
                <span>
                  <span className="legend-dot" />
                  {chartMode === "price"
                    ? "Historical closing price"
                    : "Reported net profit margin"}
                </span>
                <span>{chartData.length} observations</span>
              </div>
            </article>

            <article className="panel company-panel">
              <div className="panel-heading compact">
                <div>
                  <div className="panel-kicker">COMPANY SNAPSHOT</div>
                  <h2>{selectedCompany || "Company overview"}</h2>
                  <p>{selectedRow?.Ticker || "Select a company to explore"}</p>
                </div>
                <span className="snapshot-icon">
                  <Building2 size={20} />
                </span>
              </div>

              <div className="company-status-row">
                <span className="metric-label">Automated review</span>
                <StatusPill status={selectedRow?.["Review Status"]} />
              </div>

              <div className="snapshot-metrics">
                <div className="snapshot-metric">
                  <span>Revenue</span>
                  <strong>{money(selectedRow?.Revenue)}</strong>
                  <small>Latest reporting period</small>
                </div>
                <div className="snapshot-metric">
                  <span>Net profit margin</span>
                  <strong>{percent(selectedRow?.["Net Profit Margin %"])}</strong>
                  <small>Net income / revenue</small>
                </div>
                <div className="snapshot-metric">
                  <span>Revenue growth</span>
                  <strong
                    className={
                      Number(selectedRow?.["Revenue Growth %"]) < 0
                        ? "negative-text"
                        : "positive-text"
                    }
                  >
                    {percent(selectedRow?.["Revenue Growth %"])}
                  </strong>
                  <small>Year over year</small>
                </div>
                <div className="snapshot-metric">
                  <span>Return on assets</span>
                  <strong>{percent(selectedRow?.["Return on Assets %"])}</strong>
                  <small>Reported ratio</small>
                </div>
              </div>

              <div className="snapshot-divider" />
              <div className="snapshot-section-title">
                <FileSearch size={16} /> Review notes
              </div>

              {selectedRow?.["Business Signals"] &&
              selectedRow["Business Signals"] !== "None" ? (
                <div className="signal-box">
                  <ShieldAlert size={16} />
                  <div>
                    <strong>Business signal</strong>
                    <p>{selectedRow["Business Signals"]}</p>
                  </div>
                </div>
              ) : (
                <div className="signal-box calm">
                  <CheckCircle2 size={16} />
                  <div>
                    <strong>No configured business signal</strong>
                    <p>This does not mean the company is risk-free.</p>
                  </div>
                </div>
              )}

              {selectedRow?.["Data Quality Warnings"] &&
                selectedRow["Data Quality Warnings"] !== "None" && (
                  <div className="warning-note">
                    <CircleHelp size={15} />
                    <span>{selectedRow["Data Quality Warnings"]}</span>
                  </div>
                )}

              {selectedRow?.Evidence && (
                <p className="evidence-text">{selectedRow.Evidence}</p>
              )}

              {selectedMarket && (
                <div className="market-mini-card">
                  <div className="market-mini-icon">
                    <Wallet size={17} />
                  </div>
                  <div>
                    <span>
                      Latest market close · {shortDate(selectedMarket.latest_date)}
                    </span>
                    <strong>{money(selectedMarket.latest_close)}</strong>
                  </div>
                  <span
                    className={
                      Number(selectedMarket.period_change_pct) >= 0
                        ? "positive-text"
                        : "negative-text"
                    }
                  >
                    {percent(selectedMarket.period_change_pct)}
                  </span>
                </div>
              )}
            </article>
          </section>

          <section className="panel table-panel" id="companies">
            <div className="panel-heading table-heading">
              <div>
                <div className="panel-kicker">COVERAGE UNIVERSE</div>
                <h2>Company intelligence</h2>
                <p>
                  Compare reported fundamentals and identify records that need
                  further review.
                </p>
              </div>

              <div className="table-tools">
                <div className="search-box">
                  <Search size={16} />
                  <input
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                    placeholder="Search company or ticker"
                    aria-label="Search companies"
                  />
                  {searchTerm && (
                    <button
                      type="button"
                      onClick={() => setSearchTerm("")}
                      aria-label="Clear search"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>

                <select
                  className="filter-select"
                  value={riskFilter}
                  onChange={(event) => setRiskFilter(event.target.value)}
                  aria-label="Filter companies by review status"
                >
                  <option value="all">All reviews</option>
                  <option value="review">Needs verification</option>
                  <option value="clear">No configured flags</option>
                </select>
              </div>
            </div>

            <div className="table-scroll">
              <table className="company-table">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Revenue</th>
                    <th>Revenue growth</th>
                    <th>Net margin</th>
                    <th>Debt / equity</th>
                    <th>Review status</th>
                    <th aria-label="Open company" />
                  </tr>
                </thead>
                <tbody>
                  {filteredCompanies.map((item) => {
                    const name = companyName(item);
                    const growth = Number(item["Revenue Growth %"]);

                    return (
                      <tr
                        key={name}
                        className={name === selectedCompany ? "selected-row" : ""}
                        onClick={() => setSelectedCompany(name)}
                      >
                        <td>
                          <div className="company-cell">
                            <div className="company-avatar">
                              {name
                                .split(" ")
                                .map((part) => part[0])
                                .join("")
                                .slice(0, 2)}
                            </div>
                            <div>
                              <strong>{name}</strong>
                              <small>{item.Ticker || "—"}</small>
                            </div>
                          </div>
                        </td>
                        <td className="numeric-cell">{money(item.Revenue)}</td>
                        <td>
                          <span
                            className={`table-percent ${
                              growth < 0 ? "negative-text" : "positive-text"
                            }`}
                          >
                            {growth < 0 ? (
                              <ArrowDownRight size={14} />
                            ) : (
                              <ArrowUpRight size={14} />
                            )}
                            {percent(item["Revenue Growth %"])}
                          </span>
                        </td>
                        <td className="numeric-cell">
                          {percent(item["Net Profit Margin %"])}
                        </td>
                        <td className="numeric-cell">
                          {number(item["Debt to Equity"])}
                        </td>
                        <td>
                          <StatusPill status={item["Review Status"]} />
                        </td>
                        <td>
                          <button
                            className="row-open"
                            type="button"
                            aria-label={`View ${name}`}
                            onClick={(event) => {
                              event.stopPropagation();
                              setSelectedCompany(name);
                            }}
                          >
                            ↗
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {!filteredCompanies.length && (
                <EmptyState
                  icon={Search}
                  title="No companies found"
                  detail="Try a different search term or review filter."
                />
              )}
            </div>

            <div className="table-footer">
              <span>
                Showing <strong>{filteredCompanies.length}</strong> of{" "}
                <strong>{companies.length}</strong> companies
              </span>
              <span>
                <Database size={14} /> Latest period:{" "}
                {shortDate(dashboard?.latest_reporting_period)}
              </span>
            </div>
          </section>

          <section className="content-grid bottom-panels">
            <article className="panel risk-panel" id="risk">
              <div className="panel-heading compact">
                <div>
                  <div className="panel-kicker">ATTENTION REQUIRED</div>
                  <h2>Risk review queue</h2>
                  <p>Rule-based flags that need analyst verification.</p>
                </div>
                <span className="risk-count">
                  {flaggedCompanies.length} to review
                </span>
              </div>

              {flaggedCompanies.length ? (
                <div className="risk-list">
                  {flaggedCompanies.map((item) => (
                    <button
                      type="button"
                      className="risk-item"
                      key={companyName(item)}
                      onClick={() => setSelectedCompany(companyName(item))}
                    >
                      <div className="risk-item-icon">
                        <ShieldAlert size={18} />
                      </div>
                      <div className="risk-item-copy">
                        <strong>{companyName(item)}</strong>
                        <span>
                          {item["Business Signals"] &&
                          item["Business Signals"] !== "None"
                            ? item["Business Signals"]
                            : "Data quality review"}
                        </span>
                      </div>
                      <span className="review-link">
                        Review <span>↗</span>
                      </span>
                    </button>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={CheckCircle2}
                  title="No verification flags"
                  detail="No companies currently require verification under the configured rules."
                />
              )}

              <div className="risk-disclaimer">
                <CircleHelp size={15} />
                These are preliminary rules, not validated predictions of future
                loss.
              </div>
            </article>

            <article className="panel assistant-panel" id="assistant">
              <div className="assistant-heading">
                <div className="assistant-brand-icon">
                  <Sparkles size={19} />
                </div>
                <div>
                  <div className="panel-kicker">FINANCIAL RESEARCH</div>
                  <h2>AI research assistant</h2>
                </div>
                <span className="assistant-online">
                  <span className="status-dot" /> Connected
                </span>
              </div>

              <p className="assistant-description">
                Ask questions about the financial dataset and the rules behind
                company review flags.
              </p>

              <div className="suggested-questions">
                {suggestedQuestions.map((suggestion) => (
                  <button
                    type="button"
                    key={suggestion}
                    onClick={() => setQuestion(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>

              <div className="chat-messages" aria-live="polite">
                {messages.map((message, index) => (
                  <div
                    className={`chat-message ${message.role}`}
                    key={`${message.role}-${index}`}
                  >
                    {message.role === "assistant" && (
                      <div className="chat-avatar">
                        <Sparkles size={14} />
                      </div>
                    )}
                    <div className="chat-bubble">{message.text}</div>
                  </div>
                ))}

                {asking && (
                  <div className="chat-message assistant">
                    <div className="chat-avatar">
                      <Sparkles size={14} />
                    </div>
                    <div className="chat-bubble typing">
                      <LoaderCircle size={15} className="spin" />
                      Analysing dataset…
                    </div>
                  </div>
                )}
              </div>

              <form className="chat-input-row" onSubmit={submitQuestion}>
                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder="Ask about company financials…"
                  aria-label="Ask a financial question"
                  disabled={asking}
                />
                <button
                  type="submit"
                  aria-label="Send question"
                  disabled={asking || !question.trim()}
                >
                  {asking ? (
                    <LoaderCircle size={17} className="spin" />
                  ) : (
                    <Send size={17} />
                  )}
                </button>
              </form>

              <div className="assistant-footnote">
                Evidence-grounded answers · Verify important figures against
                official filings.
              </div>
            </article>
          </section>

          <footer className="page-footer">
            <div className="footer-brand">
              <Activity size={15} /> FinSight AI <span>·</span>{" "}
              Evidence-grounded financial intelligence
            </div>
            <div className="footer-source">
              {dashboard?.source_note ||
                "Financial data may be incomplete and has not been independently reconciled against official filings."}
            </div>
          </footer>
        </div>
      </main>
    </div>
  );
}
