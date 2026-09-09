/**
 * 统一线性图标库（Line Icon Set）
 * 规范：24x24 viewBox · stroke-width 1.75 · round cap/join · currentColor
 * 风格：几何简洁、无装饰、无填充（少数语义图标除外：play / stop / star / sparkles / dot）
 */
export const ICONS = {
  /* ---------- 导航 ---------- */
  home: '<path d="M3.5 10.3 12 3.4l8.5 6.9v8.8a1.5 1.5 0 0 1-1.5 1.5H5a1.5 1.5 0 0 1-1.5-1.5z"/><path d="M9.5 20.6v-6.4h5v6.4"/>',
  grid: '<rect x="3.6" y="3.6" width="7" height="7" rx="2.2"/><rect x="13.4" y="3.6" width="7" height="7" rx="2.2"/><rect x="3.6" y="13.4" width="7" height="7" rx="2.2"/><rect x="13.4" y="13.4" width="7" height="7" rx="2.2"/>',
  users: '<path d="M16 20.5v-1.7a3.7 3.7 0 0 0-3.7-3.7H6.7A3.7 3.7 0 0 0 3 18.8v1.7"/><circle cx="9.5" cy="8" r="3.6"/><path d="M21 20.5v-1.7a3.7 3.7 0 0 0-2.8-3.6"/><path d="M15.7 4.6a3.6 3.6 0 0 1 0 6.9"/>',
  calendar: '<rect x="3.6" y="5" width="16.8" height="16" rx="3"/><path d="M8 3v4M16 3v4M3.6 10.2h16.8"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4.8 20.5v-1.4a4.2 4.2 0 0 1 4.2-4.2h6a4.2 4.2 0 0 1 4.2 4.2v1.4"/>',

  /* ---------- 操作 ---------- */
  plus: '<path d="M12 5.2v13.6M5.2 12h13.6"/>',
  minus: '<path d="M5.2 12h13.6"/>',
  check: '<path d="M20 6.6 9.2 17.4 4 12.2"/>',
  close: '<path d="M18 6 6 18M6 6l12 12"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20.2 20.2-4.4-4.4"/>',
  edit: '<path d="M16.6 3.9a2.3 2.3 0 0 1 3.3 3.3L8.2 18.9l-4.1 1.1 1.1-4.1z"/>',
  trash: '<path d="M4 6.6h16M9.6 6.6V4.9a1.3 1.3 0 0 1 1.3-1.3h2.2a1.3 1.3 0 0 1 1.3 1.3v1.7"/><path d="M6.6 6.6 7.5 19a1.5 1.5 0 0 0 1.5 1.4h6a1.5 1.5 0 0 0 1.5-1.4l.9-12.4"/>',
  filter: '<path d="M3.6 4.6h16.8l-6.5 7.7v5.6l-3.8 2.1v-7.7z"/>',
  refresh: '<path d="M20.4 12a8.4 8.4 0 1 1-2.5-6"/><path d="M20.4 4.2v5h-5"/>',
  share: '<path d="M4 13v6.4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V13"/><path d="M12 15.5V3.2M8 7 12 3l4 4"/>',
  more: '<circle cx="5.6" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="18.4" cy="12" r="1.4" fill="currentColor" stroke="none"/>',
  copy: '<rect x="8.6" y="8.6" width="11.8" height="11.8" rx="2.6"/><path d="M15.4 5.6H6.6a2 2 0 0 0-2 2v8.8"/>',
  upload: '<path d="M12 16.4V7.4M8.4 11 12 7.4 15.6 11"/><path d="M4.6 15.2v3.4a2 2 0 0 0 2 2h10.8a2 2 0 0 0 2-2v-3.4"/>',
  download: '<path d="M12 7.6v9M8.4 13 12 16.6 15.6 13"/><path d="M4.6 15.2v3.4a2 2 0 0 0 2 2h10.8a2 2 0 0 0 2-2v-3.4"/>',
  link: '<path d="M10 13.6a4 4 0 0 0 5.7 0l2.8-2.8a4 4 0 0 0-5.7-5.7l-1.4 1.4"/><path d="M14 10.4a4 4 0 0 0-5.7 0l-2.8 2.8a4 4 0 0 0 5.7 5.7l1.4-1.4"/>',

  /* ---------- 方向 ---------- */
  'chevron-right': '<path d="m9.6 5 7 7-7 7"/>',
  'chevron-left': '<path d="m14.4 5-7 7 7 7"/>',
  'chevron-down': '<path d="m5 9.4 7 7 7-7"/>',
  'chevron-up': '<path d="m5 14.6 7-7 7 7"/>',
  'arrow-right': '<path d="M4 12h15.6M14 6.4l5.6 5.6L14 17.6"/>',
  'arrow-left': '<path d="M20 12H4.4M10 6.4 4.4 12 10 17.6"/>',
  'arrow-up': '<path d="M12 20V4.4M6.4 10 12 4.4 17.6 10"/>',
  'arrow-down': '<path d="M12 4v15.6M17.6 14 12 19.6 6.4 14"/>',

  /* ---------- 状态 ---------- */
  'check-circle': '<circle cx="12" cy="12" r="8.8"/><path d="m8.4 12.2 2.6 2.6 4.6-4.6"/>',
  circle: '<circle cx="12" cy="12" r="8.8"/>',
  'alert-circle': '<circle cx="12" cy="12" r="8.8"/><path d="M12 7.6v5M12 16.2h.01"/>',
  'x-circle': '<circle cx="12" cy="12" r="8.8"/><path d="m15 9-6 6M9 9l6 6"/>',
  info: '<circle cx="12" cy="12" r="8.8"/><path d="M12 11.2v5M12 7.8h.01"/>',
  help: '<circle cx="12" cy="12" r="8.8"/><path d="M9.6 9.4a2.5 2.5 0 1 1 3.4 2.3c-.6.3-1 .9-1 1.5v.4M12 17h.01"/>',
  clock: '<circle cx="12" cy="12" r="8.8"/><path d="M12 7.2v5.2l3.4 2"/>',
  bell: '<path d="M18 8.8a6 6 0 0 0-12 0c0 4.8-2 6.2-2 6.2h16s-2-1.4-2-6.2z"/><path d="M10.4 18.8a2 2 0 0 0 3.2 0"/>',
  eye: '<path d="M2.6 12S6.2 5.8 12 5.8 21.4 12 21.4 12 17.8 18.2 12 18.2 2.6 12 2.6 12z"/><circle cx="12" cy="12" r="3"/>',
  flag: '<path d="M5.2 21V3.6M5.2 4.4h11.4l-1.6 3.6 1.6 3.6H5.2"/>',
  target: '<circle cx="12" cy="12" r="8.4"/><circle cx="12" cy="12" r="4.4"/><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/>',
  shield: '<path d="M12 20.8s6.8-3.2 6.8-8.6V5.9L12 3.2 5.2 5.9v6.3c0 5.4 6.8 8.6 6.8 8.6z"/>',
  star: '<path d="m12 3.6 2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.8-5.2 2.8 1-5.8-4.2-4.1 5.8-.8z" fill="currentColor" stroke="none"/>',
  play: '<path d="M8 5.4 19 12 8 18.6z" fill="currentColor" stroke="none"/>',
  stop: '<rect x="6.6" y="6.6" width="10.8" height="10.8" rx="2.2" fill="currentColor" stroke="none"/>',
  volume: '<path d="M11 5 6.6 9H3v6h3.6L11 19z"/><path d="M15.4 9.4a4 4 0 0 1 0 5.2M18.4 6.6a8 8 0 0 1 0 10.8"/>',

  /* ---------- 业务 ---------- */
  'file-text': '<path d="M14 3.6H7a2 2 0 0 0-2 2v12.8a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8.6z"/><path d="M14 3.6V8.6h5"/><path d="M8.8 13h6.4M8.8 16.6h4.4"/>',
  'file-plus': '<path d="M14 3.6H7a2 2 0 0 0-2 2v12.8a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8.6z"/><path d="M14 3.6V8.6h5"/><path d="M12 12.4v5M9.5 14.9h5"/>',
  'calendar-plus': '<rect x="3.6" y="5" width="16.8" height="16" rx="3"/><path d="M8 3v4M16 3v4M3.6 10.2h16.8M12 13.2v4.6M9.7 15.5h4.6"/>',
  'user-plus': '<circle cx="9.6" cy="8" r="4"/><path d="M3.2 20.5v-1.4a4.2 4.2 0 0 1 4.2-4.2h4.6"/><path d="M18.6 8.6v6M15.6 11.6h6"/>',
  mic: '<rect x="9.2" y="2.8" width="5.6" height="10.6" rx="2.8"/><path d="M18.8 10.6v1a6.8 6.8 0 0 1-13.6 0v-1M12 17.4v3.2M8.8 20.6h6.4"/>',
  'map-pin': '<path d="M18.8 10.4c0 4.8-5.4 9.6-6.8 11-1.4-1.4-6.8-6.2-6.8-11a6.8 6.8 0 0 1 13.6 0z"/><circle cx="12" cy="10.2" r="2.5"/>',
  pen: '<path d="M15.6 4.6 19.4 8.4 8.2 19.6H4.4v-3.8z"/><path d="m13.4 6.8 3.8 3.8"/>',
  camera: '<path d="M3.6 8.8A2.6 2.6 0 0 1 6.2 6.2h1.7l1.3-2.1h5.6l1.3 2.1h1.7a2.6 2.6 0 0 1 2.6 2.6v7.8a2.6 2.6 0 0 1-2.6 2.6H6.2a2.6 2.6 0 0 1-2.6-2.6z"/><circle cx="12" cy="12.4" r="3.3"/>',
  image: '<rect x="3.6" y="4.6" width="16.8" height="14.8" rx="2.6"/><circle cx="8.8" cy="10" r="1.7"/><path d="m4.2 17.4 4.4-4.4 3.9 3.4 3-2.4 4.3 3.6"/>',
  scan: '<path d="M3.6 8.2V5.6a2 2 0 0 1 2-2h2.6M15.8 3.6h2.6a2 2 0 0 1 2 2v2.6M20.4 15.8v2.6a2 2 0 0 1-2 2h-2.6M8.2 20.4H5.6a2 2 0 0 1-2-2v-2.6"/><path d="M3.6 12h16.8"/>',
  list: '<path d="M8.6 6.6h11M8.6 12h11M8.6 17.4h11M4.4 6.6h.01M4.4 12h.01M4.4 17.4h.01"/>',
  wallet: '<rect x="3.6" y="5.6" width="16.8" height="12.8" rx="3"/><path d="M3.6 9.8h16.8M16 14.2h2"/>',
  percent: '<path d="M18.8 5.2 5.2 18.8"/><circle cx="8.2" cy="8.2" r="2.2"/><circle cx="15.8" cy="15.8" r="2.2"/>',
  bank: '<path d="M3.6 9.6 12 4.2l8.4 5.4M5.4 10.2v9M10 10.2v9M14 10.2v9M18.6 10.2v9M3.2 21h17.6"/>',
  chart: '<path d="M4.2 4.2v15.6h15.6"/><path d="M8.2 16.2v-4.2M12.4 16.2V8.6M16.6 16.2v-6.4"/>',
  briefcase: '<rect x="3.2" y="7.6" width="17.6" height="12.2" rx="2.6"/><path d="M8.6 7.6V6a2 2 0 0 1 2-2h2.8a2 2 0 0 1 2 2v1.6M3.2 12.6h17.6"/>',
  phone: '<path d="M6.6 3.6h2.2l1.6 4-2 1.4a11.4 11.4 0 0 0 5.8 5.8l1.4-2 4 1.6v2.2a2 2 0 0 1-2.2 2A15.4 15.4 0 0 1 4.4 5.8a2 2 0 0 1 2.2-2.2z"/>',
  lock: '<rect x="4.6" y="10.6" width="14.8" height="9.8" rx="2.6"/><path d="M8.2 10.6V7.6a3.8 3.8 0 0 1 7.6 0v3"/>',
  key: '<circle cx="8" cy="15" r="4.4"/><path d="m11.2 11.8 8.2-8.2M16.8 3.6l3.4 3.4M19.8 2.2l2 2"/>',
  message: '<path d="M20.4 14.4a2.4 2.4 0 0 1-2.4 2.4H8l-4.4 4V5.6A2.4 2.4 0 0 1 6 3.2h12a2.4 2.4 0 0 1 2.4 2.4z"/>',
  sparkles: '<path d="m12 3.4 1.7 4.3 4.3 1.7-4.3 1.7L12 15.4l-1.7-4.3L6 9.4l4.3-1.7z" fill="currentColor" stroke="none"/><path d="m17.8 15.2.9 2.2 2.2.9-2.2.9-.9 2.2-.9-2.2-2.2-.9 2.2-.9z" fill="currentColor" stroke="none"/>',
  sliders: '<path d="M4 21v-6M4 11V3M12 21v-8M12 9V3M20 21v-4M20 13V3M1.6 15h4.8M9.6 11h4.8M17.6 17h4.8"/>',
  logout: '<path d="M9.6 20.4H5.6a2 2 0 0 1-2-2V5.6a2 2 0 0 1 2-2h4"/><path d="M16 7.4 20.4 12 16 16.6M9.6 12h10.4"/>',
  tag: '<path d="M3.8 11.4V5a1.2 1.2 0 0 1 1.2-1.2h6.4l8.8 8.8-7.6 7.6z"/><circle cx="7.8" cy="7.8" r="1.3"/>',
}

export default ICONS
