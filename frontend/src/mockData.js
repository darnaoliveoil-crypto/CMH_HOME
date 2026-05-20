// ─── Mock Data for Check My Hits Dashboard ────────────────────────────────────

export const mockKPIs = {
  total_ips: 248,
  safe_ips: 141,
  risk_ips: 67,
  dangerous_ips: 29,
  blocked_ips: 11,
  avg_r_sent: 14320,
  avg_sent_ratio: 78.4,
  global_error_rate: 6.2,
};

export const mockIPs = [
  { ip: "192.168.1.10", entity: "cmh2", server: "s_cmh2_6101", last_datetime: "2024-05-18 14:32", risk_label: "Dangerous", last_error: "SPF", last_r_sent: 48200, sent_ratio: 42.1, growth_rate: +18.3 },
  { ip: "10.0.0.45",   entity: "cmh2", server: "s_cmh2_6102", last_datetime: "2024-05-18 13:55", risk_label: "Dangerous", last_error: "DKIM", last_r_sent: 36800, sent_ratio: 38.7, growth_rate: +12.1 },
  { ip: "172.16.5.22", entity: "cmh2", server: "s_cmh1_5501", last_datetime: "2024-05-18 12:10", risk_label: "Dangerous", last_error: "Rate limit", last_r_sent: 55000, sent_ratio: 31.5, growth_rate: +24.7 },
  { ip: "10.10.2.88",  entity: "cmh2", server: "s_cmh2_6101", last_datetime: "2024-05-18 11:40", risk_label: "Risk",      last_error: "Netblock",  last_r_sent: 22100, sent_ratio: 61.3, growth_rate: +5.2  },
  { ip: "192.168.3.77",entity: "cmh2", server: "s_cmh2_6102", last_datetime: "2024-05-18 10:22", risk_label: "Dangerous", last_error: "SPF",  last_r_sent: 41700, sent_ratio: 35.9, growth_rate: +16.8 },
  { ip: "10.0.5.101",  entity: "cmh2", server: "s_cmh1_5501", last_datetime: "2024-05-18 09:55", risk_label: "Blocked",   last_error: "Rate limit", last_r_sent: 68300, sent_ratio: 18.2, growth_rate: +42.5 },
  { ip: "172.16.9.33", entity: "cmh2", server: "s_cmh2_6101", last_datetime: "2024-05-18 09:30", risk_label: "Risk",      last_error: "DKIM", last_r_sent: 18900, sent_ratio: 67.8, growth_rate: -2.1  },
  { ip: "192.168.7.55",entity: "cmh2", server: "s_cmh2_6102", last_datetime: "2024-05-18 08:15", risk_label: "Safe",      last_error: null,        last_r_sent: 8400,  sent_ratio: 91.2, growth_rate: +0.3  },
  { ip: "10.20.1.200", entity: "cmh2", server: "s_cmh1_5501", last_datetime: "2024-05-17 23:50", risk_label: "Risk",      last_error: "Netblock",  last_r_sent: 27600, sent_ratio: 55.4, growth_rate: +8.7  },
  { ip: "172.16.0.99", entity: "cmh2", server: "s_cmh2_6101", last_datetime: "2024-05-17 22:30", risk_label: "Dangerous", last_error: "SPF",  last_r_sent: 39200, sent_ratio: 29.6, growth_rate: +21.4 },
  { ip: "192.168.4.12",entity: "cmh2", server: "s_cmh2_6102", last_datetime: "2024-05-17 21:00", risk_label: "Safe",      last_error: null,        last_r_sent: 6100,  sent_ratio: 95.3, growth_rate: +1.1  },
  { ip: "10.0.8.67",   entity: "cmh2", server: "s_cmh1_5501", last_datetime: "2024-05-17 19:45", risk_label: "Safe",      last_error: null,        last_r_sent: 11200, sent_ratio: 88.7, growth_rate: -0.5  },
  { ip: "172.16.3.44", entity: "cmh2", server: "s_cmh2_6101", last_datetime: "2024-05-17 18:20", risk_label: "Risk",      last_error: "Rate limit", last_r_sent: 24300, sent_ratio: 58.1, growth_rate: +6.9  },
  { ip: "10.10.6.150", entity: "cmh2", server: "s_cmh2_6102", last_datetime: "2024-05-17 17:00", risk_label: "Safe",      last_error: null,        last_r_sent: 9800,  sent_ratio: 93.4, growth_rate: +0.8  },
  { ip: "192.168.9.88",entity: "cmh2", server: "s_cmh1_5501", last_datetime: "2024-05-17 15:30", risk_label: "Blocked",   last_error: "SPF",  last_r_sent: 71500, sent_ratio: 12.6, growth_rate: +55.2 },
];

export const mockRiskDistribution = [
  { name: "Safe",      value: 141, color: "#22c55e" },
  { name: "Risk",      value: 67,  color: "#f59e0b" },
  { name: "Dangerous", value: 29,  color: "#ef4444" },
];

export const mockDailyVolume = [
  { date: "05-09", volume: 182400 },
  { date: "05-10", volume: 198700 },
  { date: "05-11", volume: 175300 },
  { date: "05-12", volume: 221800 },
  { date: "05-13", volume: 245600 },
  { date: "05-14", volume: 208900 },
  { date: "05-15", volume: 189200 },
  { date: "05-16", volume: 234100 },
  { date: "05-17", volume: 267800 },
  { date: "05-18", volume: 312400 },
  { date: "05-19", volume: 289500 },
];

export const mockErrors = [
  { type: "SPF",        count: 1842, volume: 38400 },
  { type: "DKIM",       count: 1127, volume: 24100 },
  { type: "Rate limit", count: 934,  volume: 51700 },
  { type: "Netblock",   count: 612,  volume: 18900 },
];

export const mockTransitions = [
  { from: "Safe",      to: "Safe",      count: 118 },
  { from: "Safe",      to: "Risk",      count: 23  },
  { from: "Safe",      to: "Dangerous", count: 6   },
  { from: "Risk",      to: "Safe",      count: 19  },
  { from: "Risk",      to: "Risk",      count: 31  },
  { from: "Risk",      to: "Dangerous", count: 17  },
  { from: "Dangerous", to: "Risk",      count: 9   },
  { from: "Dangerous", to: "Dangerous", count: 14  },
  { from: "Dangerous", to: "Blocked",   count: 6   },
];

// Heatmap: hours 0-23, error intensity (deterministic)
export const mockHourlyHeatmap = Array.from({ length: 24 }, (_, h) => ({
  hour: h,
  SPF: Math.round(20 + Math.sin((h - 9) * 0.4) * 15 + (h % 5) * 2),
  DKIM: Math.round(15 + Math.sin((h - 11) * 0.3) * 12 + (h % 3) * 2),
  'Rate limit': Math.round(10 + Math.sin((h - 14) * 0.5) * 20 + (h % 4) * 3),
  Netblock: Math.round(8 + Math.sin((h - 8) * 0.4) * 8 + (h % 2) * 2),
}));

export const mockDayHeatmap = [
  { day: "Mon", SPF: 72, DKIM: 48, 'Rate limit': 91, Netblock: 34 },
  { day: "Tue", SPF: 65, DKIM: 52, 'Rate limit': 78, Netblock: 29 },
  { day: "Wed", SPF: 88, DKIM: 61, 'Rate limit': 95, Netblock: 41 },
  { day: "Thu", SPF: 79, DKIM: 55, 'Rate limit': 83, Netblock: 36 },
  { day: "Fri", SPF: 93, DKIM: 67, 'Rate limit': 102, Netblock: 45 },
  { day: "Sat", SPF: 42, DKIM: 31, 'Rate limit': 51, Netblock: 18 },
  { day: "Sun", SPF: 38, DKIM: 27, 'Rate limit': 44, Netblock: 15 },
];

export const entities = ["All", "cmh2", "cmh1", "Acme Corp", "TechFlow"];
export const years = ["All", "2024", "2025", "2026"];
export const months = ["All", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"];
export const days = ["All", ...Array.from({ length: 31 }, (_, i) => String(i + 1).padStart(2, "0"))];
