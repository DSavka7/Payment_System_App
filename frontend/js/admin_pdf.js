/**
 * admin_pdf.js — Admin Panel PDF Report Generator for Vault Banking.
 * Generates a full system report: stats, all users, accounts, suspicious
 * transactions, requests. Uses jsPDF (auto-loaded from CDN).
 * All labels in English to avoid Cyrillic rendering issues in jsPDF helvetica.
 */

const AdminPDF = (() => {

  // ── Colors ─────────────────────────────────────────────────
  const C = {
    ink:    [13,  13,  18],
    card:   [22,  22,  30],
    card2:  [28,  28,  40],
    card3:  [18,  18,  26],
    border: [40,  40,  55],
    gold:   [212, 175, 55],
    silver: [130, 130, 155],
    white:  [240, 240, 248],
    mist:   [180, 180, 200],
    green:  [34,  197, 94],
    red:    [239, 68,  68],
    amber:  [245, 158, 11],
    blue:   [99,  102, 241],
  };

  // ── String helpers ──────────────────────────────────────────

  const _CYR = {
    'а':'a','б':'b','в':'v','г':'h','д':'d','е':'e','є':'ie','ж':'zh','з':'z',
    'и':'y','і':'i','ї':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o',
    'п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch',
    'ш':'sh','щ':'shch','ь':'','ю':'iu','я':'ia',
    'А':'A','Б':'B','В':'V','Г':'H','Д':'D','Е':'E','Є':'Ie','Ж':'Zh','З':'Z',
    'И':'Y','І':'I','Ї':'I','Й':'Y','К':'K','Л':'L','М':'M','Н':'N','О':'O',
    'П':'P','Р':'R','С':'S','Т':'T','У':'U','Ф':'F','Х':'Kh','Ц':'Ts','Ч':'Ch',
    'Ш':'Sh','Щ':'Shch','Ь':'','Ю':'Iu','Я':'Ia',
  };

  function _t(str) {
    if (!str) return '';
    return String(str).split('').map(c => _CYR[c] !== undefined ? _CYR[c] : c)
      .join('').replace(/[^\x20-\x7E]/g, '').trim();
  }

  function _safe(str, maxLen = 999) {
    return _t(str).slice(0, maxLen);
  }

  function _fmt(amount, currency) {
    return `${currency} ${Number(amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  }

  function _fmtDate(d) {
    if (!d) return '-';
    const dt = new Date(d);
    return `${String(dt.getDate()).padStart(2,'0')}.${String(dt.getMonth()+1).padStart(2,'0')}.${dt.getFullYear()} `
         + `${String(dt.getHours()).padStart(2,'0')}:${String(dt.getMinutes()).padStart(2,'0')}`;
  }

  function _fmtShort(d) {
    if (!d) return '-';
    const dt = new Date(d);
    return `${String(dt.getDate()).padStart(2,'0')}.${String(dt.getMonth()+1).padStart(2,'0')}.${dt.getFullYear()}`;
  }

  // ── Drawing primitives ──────────────────────────────────────

  function _rect(doc, x, y, w, h, col, r = 0) {
    doc.setFillColor(...col);
    r > 0 ? doc.roundedRect(x, y, w, h, r, r, 'F') : doc.rect(x, y, w, h, 'F');
  }

  function _text(doc, str, x, y, col, size, bold = false, align = 'left') {
    doc.setTextColor(...col);
    doc.setFontSize(size);
    doc.setFont('helvetica', bold ? 'bold' : 'normal');
    doc.text(String(str), x, y, align !== 'left' ? { align } : undefined);
  }

  function _line(doc, x1, y1, x2, y2, col, w = 0.3) {
    doc.setDrawColor(...col);
    doc.setLineWidth(w);
    doc.line(x1, y1, x2, y2);
  }

  function _trunc(doc, str, maxW) {
    let s = String(str || '');
    while (s.length > 1 && doc.getTextWidth(s) > maxW) s = s.slice(0, -1);
    return s;
  }

  // ── Status chip ─────────────────────────────────────────────

  function _chip(doc, status, x, y, w = 22) {
    const MAP = {
      active:         [C.green,  'ACTIVE'],
      blocked:        [C.red,    'BLOCKED'],
      success:        [C.green,  'SUCCESS'],
      approved:       [C.green,  'APPROVED'],
      rejected:       [C.red,    'REJECTED'],
      pending:        [C.amber,  'PENDING'],
      pending_review: [C.amber,  'IN REVIEW'],
      USER:           [C.silver, 'USER'],
      ADMIN:          [C.red,    'ADMIN'],
    };
    const [col, label] = MAP[status] || [C.silver, String(status).toUpperCase()];
    const H = 4.5;
    doc.setFillColor(col[0], col[1], col[2]);
    doc.setGState(new doc.GState({ opacity: 0.15 }));
    doc.roundedRect(x, y - 3.5, w, H, 1.2, 1.2, 'F');
    doc.setGState(new doc.GState({ opacity: 1 }));
    doc.setTextColor(...col);
    doc.setFontSize(5.5);
    doc.setFont('helvetica', 'bold');
    const tw = doc.getTextWidth(label);
    doc.text(label, x + w / 2 - tw / 2, y);
  }

  // ── Page chrome ─────────────────────────────────────────────

  function _bg(doc) { _rect(doc, 0, 0, 210, 297, C.ink); }

  function _header(doc, title, sub, pageNum, total) {
    _rect(doc, 0, 0, 210, 20, C.card);
    _line(doc, 0, 20, 210, 20, C.border, 0.4);
    // Logo
    _rect(doc, 8, 4, 11, 11, C.gold, 1.5);
    _text(doc, 'V', 11.2, 11.5, C.ink, 9, true);
    _text(doc, 'VAULT', 23, 9,   C.gold,   7.5, true);
    _text(doc, 'Admin Report', 23, 14.5, C.silver, 5.5);
    // Title
    _text(doc, title, 105, 8.5, C.white,  8, true, 'center');
    _text(doc, sub,   105, 14,  C.silver, 5.5, false, 'center');
    // Page
    _text(doc, `${pageNum} / ${total}`, 202, 8.5, C.silver, 6.5, false, 'right');
    _text(doc, _fmtShort(new Date()), 202, 14, C.silver, 5.5, false, 'right');
  }

  function _footer(doc, adminEmail) {
    _rect(doc, 0, 285, 210, 12, C.card);
    _line(doc, 0, 285, 210, 285, C.border, 0.3);
    _text(doc, `Vault Banking Platform  |  Admin Report  |  Generated by: ${_safe(adminEmail)}`, 10, 291, C.silver, 5.5);
    _text(doc, 'Confidential — for authorized administrators only', 10, 295.5, C.border, 5);
  }

  function _section(doc, label, y) {
    _text(doc, label, 10, y, C.gold, 6.5, true);
    _line(doc, 10, y + 1.5, 200, y + 1.5, C.border, 0.25);
    return y + 8;
  }

  // Guard new page
  function _pageCheck(doc, y, needed, bg, headerFn, footerFn) {
    if (y + needed > 280) {
      doc.addPage();
      bg(doc);
      headerFn(doc);
      footerFn(doc);
      return 28;
    }
    return y;
  }

  // ── Table header helper ─────────────────────────────────────

  function _tableHeader(doc, y, cols) {
    _rect(doc, 10, y, 190, 7.5, [30, 30, 44], 2);
    cols.forEach(([x, label]) => _text(doc, label, x, y + 5, C.silver, 5.5, true));
    return y + 9;
  }

  function _tableRow(doc, y, cells, isEven) {
    _rect(doc, 10, y - 1.5, 190, 8.5, isEven ? C.card : C.card3);
    cells.forEach(([x, str, col, bold, maxW]) => {
      const s = maxW ? _trunc(doc, str, maxW) : String(str || '-');
      _text(doc, s, x, y + 4.5, col || C.white, 6, bold || false);
    });
    return y + 8.5;
  }

  // ═══════════════════════════════════════════════════════════════════
  // MAIN GENERATOR
  // ═══════════════════════════════════════════════════════════════════

  async function _generate({ adminUser, stats, users, suspicious, requests }) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ unit: 'mm', format: 'a4' });

    const adminEmail = _safe(adminUser.email);
    const today      = _fmtShort(new Date());
    const now        = _fmtDate(new Date());

    // Count pages: cover + stats + users list + suspicious + requests
    // (users details are inline, so we estimate)
    let TOTAL = '?';

    const hdr  = (d, title, sub, n) => _header(d, title, sub, n, TOTAL);
    const ftr  = (d) => _footer(d, adminEmail);
    const chk  = (d, y, n) => _pageCheck(d, y, n, _bg, (d2) => hdr(d2, '...', '', '?'), ftr);

    // ── PAGE 1: COVER ──────────────────────────────────────────
    _bg(doc);

    // Watermark
    doc.setTextColor(20, 20, 30);
    doc.setFontSize(180);
    doc.setFont('helvetica', 'bold');
    doc.text('V', 18, 210);

    // Cover card
    _rect(doc, 18, 30, 174, 120, C.card, 5);
    _rect(doc, 18, 30, 174, 2,   C.red);

    _text(doc, 'VAULT',          30, 52, C.gold,   22, true);
    _text(doc, 'Banking Platform', 30, 62, C.silver,  9);
    _line(doc, 30, 68, 182, 68, C.border, 0.4);

    _text(doc, 'ADMIN SYSTEM REPORT', 30, 80, C.white, 14, true);
    _text(doc, 'Full platform overview: users, accounts, transactions, requests', 30, 89, C.silver, 7.5);
    _line(doc, 30, 95, 182, 95, C.border, 0.3);

    // Admin info
    _text(doc, 'Generated by:',  30, 105, C.silver, 7);
    _text(doc, adminEmail,       30, 113, C.gold,   9, true);
    _text(doc, `Date: ${now}`,   30, 121, C.silver, 7);
    _text(doc, 'Classification: CONFIDENTIAL', 30, 129, C.red, 7, true);

    // Stats preview
    _rect(doc, 18, 158, 174, 62, C.card2, 3);
    _line(doc, 18, 158, 192, 158, C.gold, 0.5);
    _text(doc, 'SYSTEM OVERVIEW', 30, 167, C.silver, 6, true);

    const statBoxes = [
      { label: 'Total Users',    val: stats.total_users,              col: C.gold  },
      { label: 'Active',         val: stats.active_users,             col: C.green },
      { label: 'Blocked',        val: stats.blocked_users,            col: C.red   },
      { label: 'Accounts',       val: stats.total_accounts,           col: C.white },
      { label: 'Transactions',   val: stats.total_transactions,       col: C.white },
      { label: 'In Review',      val: stats.pending_review_transactions, col: C.amber },
      { label: 'Pending Req.',   val: stats.pending_requests,         col: C.amber },
      { label: 'Suspicious',     val: stats.suspicious_transactions,  col: C.red   },
    ];
    statBoxes.forEach((s, i) => {
      const col = i % 4, row = Math.floor(i / 4);
      const bx = 25 + col * 44, by = 175 + row * 22;
      _rect(doc, bx - 4, by - 12, 40, 20, C.card3, 2);
      _text(doc, String(s.val), bx + 16, by - 2, s.col, 13, true, 'center');
      _text(doc, s.label, bx + 16, by + 5, C.silver, 5.5, false, 'center');
    });

    // Cover footer
    _rect(doc, 0, 274, 210, 23, [8, 8, 14]);
    _line(doc, 0, 274, 210, 274, C.gold, 0.5);
    _text(doc, 'This report is confidential and intended for authorized administrators only.', 10, 283, C.silver, 6.5);
    _text(doc, 'Unauthorized distribution is prohibited.', 10, 289.5, C.silver, 6.5);
    _text(doc, today, 200, 283, C.gold, 7, true, 'right');

    let pageNum = 1;

    // ── PAGE 2: SYSTEM STATISTICS ──────────────────────────────
    doc.addPage(); pageNum++;
    _bg(doc);
    _header(doc, 'System Statistics', `Full platform overview  |  ${now}`, pageNum, TOTAL);
    _footer(doc, adminEmail);

    let y = 28;
    y = _section(doc, 'KEY METRICS', y);

    // 4-column stat grid
    const METRIC_COLS = [
      [
        { label: 'Total Users',       val: stats.total_users,                col: C.gold  },
        { label: 'Active Users',      val: stats.active_users,               col: C.green },
        { label: 'Blocked Users',     val: stats.blocked_users,              col: C.red   },
        { label: 'Total Accounts',    val: stats.total_accounts,             col: C.white },
      ],
      [
        { label: 'Total Transactions',val: stats.total_transactions,         col: C.white },
        { label: 'Suspicious Tx',     val: stats.suspicious_transactions,    col: C.amber },
        { label: 'In Review',         val: stats.pending_review_transactions,col: C.amber },
        { label: 'Pending Requests',  val: stats.pending_requests,           col: C.amber },
      ],
    ];

    METRIC_COLS.forEach((row, ri) => {
      row.forEach((m, ci) => {
        const bx = 10 + ci * 47.5, by = y + ri * 28;
        _rect(doc, bx, by, 45, 24, C.card, 3);
        _line(doc, bx, by, bx + 45, by, m.col, 1.5);
        _text(doc, String(m.val), bx + 22.5, by + 14, m.col, 14, true, 'center');
        _text(doc, m.label,       bx + 22.5, by + 21, C.silver, 5.5, false, 'center');
      });
    });
    y += 62;

    // Ratios
    y = _section(doc, 'ANALYSIS', y);
    const activeRate   = stats.total_users   > 0 ? ((stats.active_users / stats.total_users) * 100).toFixed(1)   : '0.0';
    const blockedRate  = stats.total_users   > 0 ? ((stats.blocked_users / stats.total_users) * 100).toFixed(1)  : '0.0';
    const suspRate     = stats.total_transactions > 0 ? ((stats.suspicious_transactions / stats.total_transactions) * 100).toFixed(1) : '0.0';
    const reviewRate   = stats.suspicious_transactions > 0 ? ((stats.pending_review_transactions / stats.suspicious_transactions) * 100).toFixed(1) : '0.0';

    const ratios = [
      ['Active user rate:',       `${activeRate}%`,   C.green],
      ['Blocked user rate:',      `${blockedRate}%`,  C.red  ],
      ['Suspicious tx rate:',     `${suspRate}%`,     C.amber],
      ['Awaiting review:',        `${reviewRate}%`,   C.amber],
    ];
    ratios.forEach((r, i) => {
      const rx = i < 2 ? 10 : 108, ry = y + (i % 2) * 10;
      _rect(doc, rx, ry - 1, 95, 8, C.card, 2);
      _text(doc, r[0], rx + 3, ry + 5, C.silver, 6.5);
      _text(doc, r[1], rx + 88, ry + 5, r[2], 7, true, 'right');
    });
    y += 24;

    // Users by status bar chart (visual)
    y += 6;
    y = _section(doc, 'USER STATUS DISTRIBUTION', y);
    const totalU = stats.total_users || 1;
    const bars = [
      { label: 'Active',  count: stats.active_users,  col: C.green },
      { label: 'Blocked', count: stats.blocked_users, col: C.red   },
    ];
    bars.forEach((b, i) => {
      const barW = Math.max(2, (b.count / totalU) * 150);
      const bx = 10, by2 = y + i * 14;
      _text(doc, b.label, bx, by2 + 6, C.silver, 6);
      _rect(doc, bx + 28, by2, barW, 8, b.col, 2);
      _text(doc, String(b.count), bx + 28 + barW + 4, by2 + 6, b.col, 6, true);
    });
    y += 34;

    // ── PAGE 3+: USERS LIST ────────────────────────────────────
    doc.addPage(); pageNum++;
    _bg(doc);
    _header(doc, 'Users Directory', `Total: ${users.length} users`, pageNum, TOTAL);
    _footer(doc, adminEmail);
    y = 28;
    y = _section(doc, `ALL USERS (${users.length})`, y);

    const USER_COLS = [
      [13,  'NAME & EMAIL'],
      [72,  'PHONE'],
      [103, 'ROLE'],
      [120, 'STATUS'],
      [144, 'ACCOUNTS'],
      [160, 'REGISTERED'],
    ];
    y = _tableHeader(doc, y, USER_COLS);

    for (let i = 0; i < users.length; i++) {
      const u = users[i];
      y = chk(doc, y, 10, _bg, (d) => {
        pageNum++;
        _header(d, 'Users Directory', `continued (${i + 1} / ${users.length})`, pageNum, TOTAL);
        _footer(d, adminEmail);
      }, () => {});
      if (y === 28) { y = _section(doc, `USERS (continued)`, y); y = _tableHeader(doc, y, USER_COLS); }

      const name  = _safe(`${u.first_name} ${u.last_name}`, 22);
      const email = _safe(u.email, 26);
      const phone = _safe(u.phone || '-', 18);

      // Row bg
      _rect(doc, 10, y - 1.5, 190, 14, i % 2 === 0 ? C.card : C.card3);
      // Status stripe
      _rect(doc, 10, y - 1.5, 2, 14, u.status === 'active' ? C.green : C.red);

      _text(doc, name,  15, y + 4.5, C.white,  6,   true);
      _text(doc, email, 15, y + 10,  C.silver, 5.5, false);
      _text(doc, phone, 72, y + 4.5, C.silver, 6);
      _chip(doc, u.role,   101, y + 4.5, 18);
      _chip(doc, u.status, 118, y + 4.5, 22);
      _text(doc, String(u.accounts_count || 0), 148, y + 4.5, C.white, 6, true, 'center');
      _text(doc, _fmtShort(u.created_at), 160, y + 4.5, C.silver, 6);

      if (u.block_reason) {
        _text(doc, `Block reason: ${_safe(u.block_reason, 60)}`, 15, y + 10, C.red, 5);
      }

      y += 14;
    }

    // ── SUSPICIOUS TRANSACTIONS ────────────────────────────────
    doc.addPage(); pageNum++;
    _bg(doc);
    _header(doc, 'Suspicious Transactions', `Total: ${suspicious.length}`, pageNum, TOTAL);
    _footer(doc, adminEmail);
    y = 28;
    y = _section(doc, `SUSPICIOUS TRANSACTIONS (${suspicious.length})`, y);

    if (!suspicious.length) {
      _rect(doc, 10, y, 190, 14, C.card, 3);
      _text(doc, 'No suspicious transactions found', 14, y + 9, C.silver, 8);
      y += 18;
    } else {
      // Summary by status
      const pendingCount  = suspicious.filter(t => t.status === 'pending_review').length;
      const approvedCount = suspicious.filter(t => t.status === 'approved').length;
      const rejectedCount = suspicious.filter(t => t.status === 'rejected').length;

      const summCards = [
        { label: 'In Review', val: pendingCount,  col: C.amber },
        { label: 'Approved',  val: approvedCount, col: C.green },
        { label: 'Rejected',  val: rejectedCount, col: C.red   },
      ];
      summCards.forEach((s, i) => {
        const bx = 10 + i * 63;
        _rect(doc, bx, y, 60, 18, C.card2, 3);
        _line(doc, bx, y, bx + 60, y, s.col, 1.5);
        _text(doc, String(s.val), bx + 30, y + 11, s.col, 12, true, 'center');
        _text(doc, s.label,       bx + 30, y + 17, C.silver, 5.5, false, 'center');
      });
      y += 24;

      // Table
      const SUSP_COLS = [
        [13,  'DATE'],
        [45,  'FROM ACCOUNT'],
        [88,  'TO ACCOUNT'],
        [124, 'AMOUNT'],
        [158, 'STATUS'],
        [181, 'REVIEWED'],
      ];
      y = _tableHeader(doc, y, SUSP_COLS);

      for (let i = 0; i < suspicious.length; i++) {
        const tx = suspicious[i];
        y = chk(doc, y, 10, _bg, (d) => {
          pageNum++;
          _header(d, 'Suspicious Transactions', 'continued', pageNum, TOTAL);
          _footer(d, adminEmail);
        }, () => {});
        if (y === 28) { y = _section(doc, 'SUSPICIOUS (continued)', y); y = _tableHeader(doc, y, SUSP_COLS); }

        _rect(doc, 10, y - 1.5, 190, 8.5, i % 2 === 0 ? C.card : C.card3);
        // Left stripe by status
        const sCol = tx.status === 'approved' ? C.green : tx.status === 'rejected' ? C.red : C.amber;
        _rect(doc, 10, y - 1.5, 2, 8.5, sCol);

        _text(doc, _fmtShort(tx.created_at),                         13,  y + 4.5, C.silver, 5.5);
        _text(doc, `...${(tx.from_account_id || '').slice(-8)}`,       45,  y + 4.5, C.mist,   5.5);
        _text(doc, `...${(tx.to_account_id || '?').slice(-8)}`,        88,  y + 4.5, C.mist,   5.5);
        _text(doc, _fmt(tx.amount, tx.currency),                      124, y + 4.5, C.amber,  6,   true);
        _chip(doc, tx.status, 156, y + 4.5, 22);
        _text(doc, tx.reviewed_at ? _fmtShort(tx.reviewed_at) : '-',  181, y + 4.5, C.silver, 5.5);

        if (tx.review_comment) {
          y += 8.5;
          _text(doc, `Comment: ${_safe(tx.review_comment, 60)}`, 15, y + 4.5, C.silver, 5);
        }
        y += 8.5;
      }
    }

    // ── REQUESTS ───────────────────────────────────────────────
    doc.addPage(); pageNum++;
    _bg(doc);
    _header(doc, 'User Requests', `Total: ${requests.length}`, pageNum, TOTAL);
    _footer(doc, adminEmail);
    y = 28;
    y = _section(doc, `ALL REQUESTS (${requests.length})`, y);

    if (!requests.length) {
      _rect(doc, 10, y, 190, 14, C.card, 3);
      _text(doc, 'No requests found', 14, y + 9, C.silver, 8);
    } else {
      // Summary
      const pendReq  = requests.filter(r => r.status === 'pending').length;
      const apprReq  = requests.filter(r => r.status === 'approved').length;
      const rejReq   = requests.filter(r => r.status === 'rejected').length;

      const reqSumm = [
        { label: 'Pending',   val: pendReq, col: C.amber },
        { label: 'Approved',  val: apprReq, col: C.green },
        { label: 'Rejected',  val: rejReq,  col: C.red   },
      ];
      reqSumm.forEach((s, i) => {
        const bx = 10 + i * 63;
        _rect(doc, bx, y, 60, 18, C.card2, 3);
        _line(doc, bx, y, bx + 60, y, s.col, 1.5);
        _text(doc, String(s.val), bx + 30, y + 11, s.col, 12, true, 'center');
        _text(doc, s.label,       bx + 30, y + 17, C.silver, 5.5, false, 'center');
      });
      y += 24;

      // Request type breakdown
      const typeBreak = {};
      requests.forEach(r => { typeBreak[r.type] = (typeBreak[r.type] || 0) + 1; });
      let tbx = 10;
      Object.entries(typeBreak).forEach(([type, count]) => {
        _rect(doc, tbx, y, 58, 10, C.card3, 2);
        _text(doc, type, tbx + 4, y + 7, C.silver, 6);
        _text(doc, String(count), tbx + 52, y + 7, C.white, 6, true, 'right');
        tbx += 62;
      });
      y += 14;

      // Table
      const REQ_COLS = [
        [13,  'DATE'],
        [43,  'USER'],
        [88,  'TYPE'],
        [112, 'ACCOUNT'],
        [150, 'STATUS'],
        [170, 'MESSAGE'],
      ];
      y = _tableHeader(doc, y, REQ_COLS);

      for (let i = 0; i < requests.length; i++) {
        const req = requests[i];
        y = chk(doc, y, 10, _bg, (d) => {
          pageNum++;
          _header(d, 'User Requests', 'continued', pageNum, TOTAL);
          _footer(d, adminEmail);
        }, () => {});
        if (y === 28) { y = _section(doc, 'REQUESTS (continued)', y); y = _tableHeader(doc, y, REQ_COLS); }

        _rect(doc, 10, y - 1.5, 190, 8.5, i % 2 === 0 ? C.card : C.card3);
        const rCol = req.status === 'approved' ? C.green : req.status === 'rejected' ? C.red : C.amber;
        _rect(doc, 10, y - 1.5, 2, 8.5, rCol);

        _text(doc, _fmtShort(req.created_at),                             13,  y + 4.5, C.silver, 5.5);
        _text(doc, _trunc(doc, _safe(req.user_email || '-'), 40),          43,  y + 4.5, C.mist,   5.5);
        _text(doc, req.type || '-',                                        88,  y + 4.5, C.white,  5.5, true);
        _text(doc, `...${(req.account_id || '').slice(-8)}`,              112,  y + 4.5, C.silver, 5.5);
        _chip(doc, req.status, 148, y + 4.5, 20);
        _text(doc, _trunc(doc, _safe(req.message), 35),                   170,  y + 4.5, C.silver, 5);

        y += 8.5;
      }
    }

    // ── Patch total page count ─────────────────────────────────
    TOTAL = pageNum;
    const totalPages = doc.getNumberOfPages();
    for (let i = 2; i <= totalPages; i++) {
      doc.setPage(i);
      _rect(doc, 165, 5, 40, 10, C.card);
      _text(doc, `${i} / ${totalPages}`, 202, 8.5, C.silver, 6.5, false, 'right');
    }

    return doc;
  }

  // ── Load jsPDF ──────────────────────────────────────────────

  async function _ensureJsPDF() {
    if (window.jspdf?.jsPDF) return;
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
      s.onload  = resolve;
      s.onerror = () => reject(new Error('Failed to load jsPDF'));
      document.head.appendChild(s);
    });
  }

  // ── Public API ──────────────────────────────────────────────

  async function generateReport() {
    const btn = document.getElementById('admin-pdf-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Generating PDF...'; }

    AdminUI.toast('Collecting data...', 'info', 3000);

    try {
      await _ensureJsPDF();

      const adminUser = Store.getUser();

      // Fetch all pages of a paginated endpoint (max limit=100 per request)
      async function _fetchAll(path, pageSize = 100) {
        const items = [];
        let offset = 0;
        while (true) {
          const data = await adminGet(`${path}?limit=${pageSize}&offset=${offset}`);
          const page = data.items || [];
          items.push(...page);
          if (page.length < pageSize) break; // last page
          offset += pageSize;
        }
        return { items };
      }

      // Fetch all data (stats in parallel with first pages, rest paginated)
      const [statsData, usersData, suspData, reqData] = await Promise.all([
        adminGet('/admin/stats'),
        _fetchAll('/admin/users',      100),
        _fetchAll('/admin/suspicious', 100),
        _fetchAll('/admin/requests',   100),
      ]);

      const doc = await _generate({
        adminUser,
        stats:      statsData,
        users:      usersData.items || [],
        suspicious: suspData.items  || [],
        requests:   reqData.items   || [],
      });

      const dateStr = new Date().toISOString().slice(0, 10);
      doc.save(`Vault_Admin_Report_${dateStr}.pdf`);

      AdminUI.toast('Admin report saved successfully ✓', 'success', 4000);
    } catch (err) {
      console.error('Admin PDF error:', err);
      AdminUI.toast('PDF error: ' + err.message, 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="13" height="13"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg> Download Admin Report PDF`;
      }
    }
  }

  return { generateReport };
})();