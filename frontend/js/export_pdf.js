/**
 * export_pdf.js — Client-side PDF export for Vault Banking.
 * Uses jsPDF 2.5.1 via CDN (auto-loaded on first use).
 *
 * All UI labels are in English to avoid font/encoding issues
 * with jsPDF's built-in helvetica (no Cyrillic support).
 * User data (names, emails, descriptions) is rendered as-is —
 * non-Latin chars that can't render will be stripped safely.
 */

const VaultPDF = (() => {

  // ── Colors (RGB) ───────────────────────────────────────────
  const C = {
    ink:    [13,  13,  18],
    card:   [22,  22,  30],
    card2:  [28,  28,  40],
    border: [40,  40,  55],
    gold:   [212, 175, 55],
    silver: [130, 130, 155],
    white:  [240, 240, 248],
    green:  [34,  197, 94],
    red:    [239, 68,  68],
    amber:  [245, 158, 11],
    mist:   [180, 180, 200],
  };

  // Strip non-latin/non-printable chars that jsPDF can't render
  function _safe(str) {
    if (!str) return '';
    return String(str)
      .replace(/[^\x20-\x7E\u00C0-\u024F]/g, '')  // keep Latin extended
      .trim() || String(str).replace(/\s+/g, ' ').trim().slice(0, 40);
  }

  // Transliterate Ukrainian/Russian to Latin for safe rendering
  function _translit(str) {
    if (!str) return '';
    const map = {
      'а':'a','б':'b','в':'v','г':'h','д':'d','е':'e','є':'ie','ж':'zh',
      'з':'z','и':'y','і':'i','ї':'i','й':'y','к':'k','л':'l','м':'m',
      'н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f',
      'х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ь':'','ю':'iu','я':'ia',
      'А':'A','Б':'B','В':'V','Г':'H','Д':'D','Е':'E','Є':'Ie','Ж':'Zh',
      'З':'Z','И':'Y','І':'I','Ї':'I','Й':'Y','К':'K','Л':'L','М':'M',
      'Н':'N','О':'O','П':'P','Р':'R','С':'S','Т':'T','У':'U','Ф':'F',
      'Х':'Kh','Ц':'Ts','Ч':'Ch','Ш':'Sh','Щ':'Shch','Ь':'','Ю':'Iu','Я':'Ia',
    };
    return str.split('').map(c => map[c] !== undefined ? map[c] : _safe(c)).join('');
  }

  function _fmt(amount, currency) {
    const num = Number(amount).toLocaleString('en-US', {
      minimumFractionDigits: 2, maximumFractionDigits: 2,
    });
    return `${currency} ${num}`;
  }

  function _fmtDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return `${String(d.getDate()).padStart(2,'0')}.${String(d.getMonth()+1).padStart(2,'0')}.${d.getFullYear()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
  }

  function _fmtDateShort(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return `${String(d.getDate()).padStart(2,'0')}.${String(d.getMonth()+1).padStart(2,'0')}.${d.getFullYear()}`;
  }

  // ── Drawing primitives ─────────────────────────────────────

  function _rect(doc, x, y, w, h, color, radius = 0) {
    doc.setFillColor(...color);
    if (radius > 0) doc.roundedRect(x, y, w, h, radius, radius, 'F');
    else            doc.rect(x, y, w, h, 'F');
  }

  function _text(doc, str, x, y, color, size, bold = false, align = 'left') {
    doc.setTextColor(...color);
    doc.setFontSize(size);
    doc.setFont('helvetica', bold ? 'bold' : 'normal');
    doc.text(String(str), x, y, align !== 'left' ? { align } : undefined);
  }

  function _line(doc, x1, y1, x2, y2, color, w = 0.3) {
    doc.setDrawColor(...color);
    doc.setLineWidth(w);
    doc.line(x1, y1, x2, y2);
  }

  function _truncate(doc, str, maxW) {
    if (!str) return '';
    let s = String(str);
    while (s.length > 0 && doc.getTextWidth(s) > maxW) s = s.slice(0, -1);
    return s;
  }

  // ── Status chip ────────────────────────────────────────────

  function _chip(doc, status, x, y) {
    const map = {
      active:         { c: C.green,  l: 'ACTIVE'      },
      blocked:        { c: C.red,    l: 'BLOCKED'      },
      success:        { c: C.green,  l: 'SUCCESS'      },
      approved:       { c: C.green,  l: 'APPROVED'     },
      rejected:       { c: C.red,    l: 'REJECTED'     },
      pending:        { c: C.amber,  l: 'PENDING'      },
      pending_review: { c: C.amber,  l: 'IN REVIEW'    },
    };
    const cfg = map[status] || { c: C.silver, l: String(status).toUpperCase() };
    const W = 20, H = 4.5;
    doc.setFillColor(cfg.c[0], cfg.c[1], cfg.c[2]);
    doc.setGState(new doc.GState({ opacity: 0.18 }));
    doc.roundedRect(x, y - 3.5, W, H, 1.2, 1.2, 'F');
    doc.setGState(new doc.GState({ opacity: 1 }));
    doc.setTextColor(...cfg.c);
    doc.setFontSize(5.5);
    doc.setFont('helvetica', 'bold');
    const tw = doc.getTextWidth(cfg.l);
    doc.text(cfg.l, x + W/2 - tw/2, y);
  }

  // ── Page chrome ────────────────────────────────────────────

  function _bg(doc) {
    _rect(doc, 0, 0, 210, 297, C.ink);
  }

  function _header(doc, title, sub, pageNum, total) {
    _rect(doc, 0, 0, 210, 20, C.card);
    _line(doc, 0, 20, 210, 20, C.border, 0.4);

    // Logo
    _rect(doc, 8, 4, 11, 11, C.gold, 1.5);
    _text(doc, 'V', 11.2, 11.5, C.ink, 9, true);
    _text(doc, 'VAULT', 23, 9, C.gold, 7.5, true);
    _text(doc, 'Banking Platform', 23, 14.5, C.silver, 5.5);

    // Center title
    _text(doc, title, 105, 8.5, C.white, 8, true, 'center');
    _text(doc, sub,   105, 14, C.silver, 5.5, false, 'center');

    // Page number
    _text(doc, `${pageNum} / ${total}`, 202, 8.5, C.silver, 6.5, false, 'right');
    _text(doc, _fmtDateShort(new Date().toISOString()), 202, 14, C.silver, 5.5, false, 'right');
  }

  function _footer(doc) {
    _rect(doc, 0, 285, 210, 12, C.card);
    _line(doc, 0, 285, 210, 285, C.border, 0.3);
    _text(doc, 'Vault Banking Platform  |  Official Account Statement  |  Auto-generated', 10, 291, C.silver, 5.5);
    _text(doc, 'This document is a bank statement and does not require a signature', 10, 295.5, C.border, 5);
  }

  function _sectionLabel(doc, label, y) {
    _text(doc, label, 10, y, C.gold, 6, true);
    _line(doc, 10, y + 1.5, 200, y + 1.5, C.border, 0.25);
    return y + 7;
  }

  // ── Main generator ─────────────────────────────────────────

  async function _generate({ user, accounts, txByAccount }) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ unit: 'mm', format: 'a4' });

    const fullName  = _translit(`${user.first_name || ''} ${user.last_name || ''}`.trim()) || _safe(user.email);
    const email     = _safe(user.email);
    const phone     = _safe(user.phone || '-');
    const role      = user.role === 'ADMIN' ? 'Administrator' : 'Client';
    const today     = _fmtDateShort(new Date().toISOString());
    const totalTx   = Object.values(txByAccount).reduce((s, d) => s + (d.total || 0), 0);
    const activeAcc = accounts.filter(a => a.status === 'active').length;

    // We'll patch page numbers at the end
    const TOTAL_PAGES = 1 + 1 + accounts.length; // cover + profile + one per account

    // ──────────────────────────────────────────────────────────
    // PAGE 1 — COVER
    // ──────────────────────────────────────────────────────────
    _bg(doc);

    // Big watermark "V"
    doc.setTextColor(22, 22, 32);
    doc.setFontSize(200);
    doc.setFont('helvetica', 'bold');
    doc.text('V', 18, 210);

    // Cover card
    _rect(doc, 18, 32, 174, 105, C.card, 5);
    _rect(doc, 18, 32, 174, 2.5, C.gold, 0); // top accent bar

    _text(doc, 'VAULT',              30, 52, C.gold,   22, true);
    _text(doc, 'Banking Platform',   30, 62, C.silver,  9);
    _line(doc, 30, 68, 182, 68, C.border, 0.4);

    _text(doc, 'ACCOUNT STATEMENT',  30, 80, C.white,  13, true);
    _text(doc, 'Official Bank Statement', 30, 88, C.silver, 8);
    _line(doc, 30, 93, 182, 93, C.border, 0.3);

    _text(doc, fullName, 30, 103, C.white,  10, true);
    _text(doc, email,    30, 111, C.silver,  8);
    _text(doc, phone,    30, 118, C.silver,  8);
    _text(doc, `Generated: ${today}`, 30, 127, C.silver, 7.5);

    // Stats row
    _rect(doc, 18, 148, 174, 26, C.card2, 3);
    _line(doc, 18, 148, 192, 148, C.gold, 0.5);

    const stats = [
      { val: String(accounts.length), lbl: 'Accounts',    col: C.gold  },
      { val: String(activeAcc),       lbl: 'Active',      col: C.green },
      { val: String(totalTx),         lbl: 'Transactions',col: C.white },
    ];
    stats.forEach((s, i) => {
      const cx = 40 + i * 58;
      _text(doc, s.val, cx, 162, s.col, 14, true, 'center');
      _text(doc, s.lbl, cx, 169, C.silver, 6.5, false, 'center');
    });

    // Cover footer
    _rect(doc, 0, 274, 210, 23, [8, 8, 14]);
    _line(doc, 0, 274, 210, 274, C.gold, 0.5);
    _text(doc, 'This document is an official bank account statement', 10, 283, C.silver, 6.5);
    _text(doc, 'generated automatically by Vault Banking Platform.', 10, 289.5, C.silver, 6.5);
    _text(doc, today, 200, 283, C.gold, 7, true, 'right');
    _text(doc, `1 / ${TOTAL_PAGES}`, 200, 289.5, C.silver, 6, false, 'right');

    // ──────────────────────────────────────────────────────────
    // PAGE 2 — CLIENT PROFILE
    // ──────────────────────────────────────────────────────────
    doc.addPage();
    _bg(doc);
    _header(doc, 'Client Profile', `${fullName}  |  ${email}`, 2, TOTAL_PAGES);
    _footer(doc);

    let y = 28;
    y = _sectionLabel(doc, 'CLIENT INFORMATION', y);

    // Profile hero card
    _rect(doc, 10, y, 190, 50, C.card, 3);
    _line(doc, 10, y, 200, y, C.gold, 0.6);

    // Avatar
    doc.setFillColor(...C.gold);
    doc.circle(26, y + 17, 10, 'F');
    const initials = (
      ((user.first_name || '?')[0]) +
      ((user.last_name  || '?')[0])
    ).toUpperCase();
    _text(doc, initials, 26, y + 20.5, C.ink, 10, true, 'center');

    // Name block
    _text(doc, fullName, 42, y + 11, C.white,  10, true);
    _text(doc, email,    42, y + 18, C.silver,  7.5);
    _text(doc, phone,    42, y + 25, C.silver,  7.5);
    _chip(doc, user.status, 42, y + 34);
    _text(doc, role, 67, y + 34, C.silver, 6.5);

    // Right column
    const rx = 118;
    const rows = [
      ['First name:',    _translit(user.first_name || '-')],
      ['Last name:',     _translit(user.last_name  || '-')],
      ['Phone:',         phone],
      ['Registered:',    _fmtDateShort(user.created_at)],
      ['Status:',        user.status],
      ['Role:',          role],
    ];
    rows.forEach((r, i) => {
      const ry = y + 10 + i * 7;
      _text(doc, r[0], rx,      ry, C.silver, 6.5);
      _text(doc, r[1], rx + 24, ry, C.white,  6.5);
    });

    // Block reason
    if (user.block_reason) {
      y += 53;
      _rect(doc, 10, y, 190, 11, [55, 18, 18], 2);
      _text(doc, 'BLOCK REASON:', 14, y + 7.5, C.red, 6.5, true);
      _text(doc, _truncate(doc, _translit(user.block_reason), 130), 50, y + 7.5, C.white, 6.5);
      y += 14;
    } else {
      y += 53;
    }

    y += 5;
    y = _sectionLabel(doc, 'ACCOUNTS SUMMARY', y);

    // Table header
    _rect(doc, 10, y, 190, 8, [30, 30, 44], 2);
    const TH = [
      [14,  'ACCOUNT NUMBER'],
      [72,  'CURRENCY'],
      [98,  'BALANCE'],
      [142, 'STATUS'],
      [174, 'TX COUNT'],
    ];
    TH.forEach(([tx, lbl]) => _text(doc, lbl, tx, y + 5.5, C.silver, 5.5, true));
    y += 10;

    accounts.forEach((acc, i) => {
      _rect(doc, 10, y - 1.5, 190, 9, i % 2 === 0 ? C.card : C.card2);
      _text(doc, acc.card_number || '-',          14,  y + 5, C.white,  6.5);
      _text(doc, acc.currency,                    72,  y + 5, C.silver, 6.5);
      _text(doc, _fmt(acc.balance, acc.currency), 98,  y + 5,
            acc.status === 'active' ? C.green : C.mist, 6.5, true);
      _chip(doc, acc.status, 140, y + 5);
      _text(doc, String(txByAccount[acc.id]?.total || 0), 174, y + 5, C.white, 6.5);
      y += 9;
    });

    // Currency totals row
    y += 2;
    _rect(doc, 10, y, 190, 8, C.gold, 2);
    _text(doc, 'TOTAL BALANCE', 14, y + 5.5, C.ink, 6.5, true);
    const currencies = [...new Set(accounts.map(a => a.currency))];
    let cx = 80;
    currencies.forEach(cur => {
      const tot = accounts.filter(a => a.currency === cur).reduce((s, a) => s + a.balance, 0);
      _text(doc, _fmt(tot, cur), cx, y + 5.5, C.ink, 6.5, true);
      cx += 45;
    });

    // ──────────────────────────────────────────────────────────
    // PAGES 3+ — ONE PER ACCOUNT
    // ──────────────────────────────────────────────────────────
    for (let ai = 0; ai < accounts.length; ai++) {
      const acc = accounts[ai];
      const pageNum = 3 + ai;
      const accTypeMap = { UAH: 'UAH Account', USD: 'USD Account', EUR: 'EUR Account' };
      const accType = accTypeMap[acc.currency] || `${acc.currency} Account`;

      doc.addPage();
      _bg(doc);
      _header(doc, accType, `${acc.card_number}  |  ${acc.currency}`, pageNum, TOTAL_PAGES);
      _footer(doc);

      y = 28;

      // ── Account card visual ──
      const cardBg = acc.status === 'blocked' ? [40, 15, 15] : [18, 28, 55];
      _rect(doc, 10, y, 128, 50, cardBg, 5);
      _rect(doc, 10, y, 128, 1.5, acc.status === 'blocked' ? C.red : C.gold);

      // Chip
      _rect(doc, 18, y + 10, 8, 6, C.gold, 1);
      _rect(doc, 19.5, y + 11, 5, 4, [170, 130, 20], 0.5);

      _text(doc, acc.card_number || '-', 18, y + 26, C.white, 8.5, true);
      _text(doc, _fmt(acc.balance, acc.currency), 18, y + 37,
            acc.status === 'blocked' ? C.red : C.gold, 12, true);
      _text(doc, acc.status === 'active' ? '  ACTIVE' : '  BLOCKED',
            18, y + 45, acc.status === 'active' ? C.green : C.red, 6, true);

      // Details panel
      _rect(doc, 144, y, 56, 50, C.card, 3);
      _text(doc, 'ACCOUNT DETAILS', 147, y + 8, C.silver, 5.5, true);
      _line(doc, 147, y + 10, 196, y + 10, C.border, 0.25);
      const dRows = [
        ['Type:',     accType],
        ['Currency:', acc.currency],
        ['Status:',   acc.status.toUpperCase()],
        ['Opened:',   _fmtDateShort(acc.created_at)],
        ['ID:',       acc.id ? `...${acc.id.slice(-8)}` : '-'],
      ];
      dRows.forEach((r, i) => {
        const ry = y + 17 + i * 7;
        _text(doc, r[0], 147, ry, C.silver, 6);
        _text(doc, r[1], 170, ry, C.white,  6);
      });

      y += 55;

      // Block reason
      if (acc.block_reason) {
        _rect(doc, 10, y, 190, 10, [52, 16, 16], 2);
        _text(doc, 'BLOCK REASON:', 14, y + 7, C.red, 6.5, true);
        _text(doc, _truncate(doc, _translit(acc.block_reason), 130), 50, y + 7, C.white, 6.5);
        y += 14;
      }

      y += 3;

      // ── Transactions table ──
      const txData  = txByAccount[acc.id];
      const txItems = txData?.items || [];
      const txTotal = txData?.total || 0;

      y = _sectionLabel(doc, `TRANSACTIONS (${txItems.length} of ${txTotal})`, y);

      if (txItems.length === 0) {
        _rect(doc, 10, y, 190, 14, C.card, 3);
        _text(doc, 'No transactions found', 14, y + 9, C.silver, 8);
        y += 18;
      } else {
        // Table header
        _rect(doc, 10, y, 190, 7.5, [28, 28, 42], 2);
        const cols = [
          [13, 'DATE'],
          [47, 'TX ID'],
          [77, 'TYPE'],
          [107,'DESCRIPTION'],
          [151,'STATUS'],
          [175,'AMOUNT'],
        ];
        cols.forEach(([cx2, lbl]) => _text(doc, lbl, cx2, y + 5, C.silver, 5.5, true));
        y += 9;

        let incomeSum = 0, outcomeSum = 0;

        for (let ti = 0; ti < txItems.length; ti++) {
          const tx = txItems[ti];

          // New page if needed
          if (y > 270) {
            doc.addPage();
            _bg(doc);
            _header(doc, accType + ' (cont.)', `${acc.card_number}  |  continued`, pageNum, TOTAL_PAGES);
            _footer(doc);
            y = 28;
            _rect(doc, 10, y, 190, 7.5, [28, 28, 42], 2);
            cols.forEach(([cx2, lbl]) => _text(doc, lbl, cx2, y + 5, C.silver, 5.5, true));
            y += 9;
          }

          const isIncome = tx.to_account_id === acc.id;
          if (isIncome) incomeSum += tx.amount;
          else          outcomeSum += tx.amount;

          const rowBg = ti % 2 === 0 ? C.card : C.card2;
          _rect(doc, 10, y - 1.5, 190, 8.5, rowBg);
          // Side stripe
          _rect(doc, 10, y - 1.5, 2, 8.5, isIncome ? C.green : C.red);

          const typeLabel = tx.type === 'transfer'
            ? (isIncome ? 'Incoming' : 'Outgoing')
            : tx.type === 'income' ? 'Income' : (tx.type || '-');

          const desc = _truncate(doc,
            _safe(tx.description || tx.category || typeLabel), 40);
          const shortId = tx.id ? `#${tx.id.slice(-7)}` : '-';
          const amtStr  = `${isIncome ? '+' : '-'} ${_fmt(tx.amount, tx.currency)}`;

          _text(doc, _fmtDateShort(tx.created_at), 13,  y + 5, C.silver, 5.5);
          _text(doc, shortId,   47,  y + 5, C.silver, 5.5);
          _text(doc, typeLabel, 77,  y + 5, C.white,  5.5);
          _text(doc, desc,      107, y + 5, C.mist,   5.5);
          _chip(doc, tx.status, 149, y + 5);
          _text(doc, amtStr, 195, y + 5, isIncome ? C.green : C.red, 5.5, true, 'right');

          y += 8.5;
        }

        // Account totals bar
        y += 3;
        if (y > 275) {
          doc.addPage();
          _bg(doc);
          _header(doc, accType, acc.card_number, pageNum, TOTAL_PAGES);
          _footer(doc);
          y = 30;
        }

        _rect(doc, 10, y, 190, 16, [16, 28, 20], 3);
        _line(doc, 10, y, 200, y, C.green, 0.4);

        _text(doc, 'Incoming:', 14, y + 6,  C.silver, 6.5);
        _text(doc, `+ ${_fmt(incomeSum,  acc.currency)}`, 45, y + 6,  C.green, 6.5, true);
        _text(doc, 'Outgoing:', 14, y + 12, C.silver, 6.5);
        _text(doc, `- ${_fmt(outcomeSum, acc.currency)}`, 45, y + 12, C.red,   6.5, true);

        const net = incomeSum - outcomeSum;
        _text(doc, 'Net:',            118, y + 6,  C.silver, 6.5);
        _text(doc, `${net >= 0 ? '+' : '-'} ${_fmt(Math.abs(net), acc.currency)}`,
              148, y + 6, net >= 0 ? C.green : C.red, 7, true);
        _text(doc, 'Current balance:', 118, y + 12, C.silver, 6.5);
        _text(doc, _fmt(acc.balance, acc.currency), 178, y + 12, C.gold, 7, true, 'right');

        y += 20;
      }
    }

    return doc;
  }

  // ── Load jsPDF from CDN ────────────────────────────────────

  async function _ensureJsPDF() {
    if (window.jspdf?.jsPDF) return;
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
      s.onload  = resolve;
      s.onerror = () => reject(new Error('Failed to load jsPDF library'));
      document.head.appendChild(s);
    });
  }

  // ── Public API ─────────────────────────────────────────────

  async function exportAccountStatement(user, accounts) {
    const btn = document.getElementById('profile-export-pdf-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Generating PDF...'; }

    try {
      await _ensureJsPDF();

      // Fetch up to 200 transactions per account
      const txByAccount = {};
      await Promise.all(accounts.map(async acc => {
        try {
          txByAccount[acc.id] = await Api.getAccountTx(acc.id, 200, 0);
        } catch {
          txByAccount[acc.id] = { items: [], total: 0 };
        }
      }));

      const doc = await _generate({ user, accounts, txByAccount });

      const namePart = _translit(`${user.first_name || ''}_${user.last_name || ''}`)
        .replace(/\s+/g, '_').replace(/[^A-Za-z0-9_-]/g, '') || 'client';
      const datePart = new Date().toISOString().slice(0, 10);
      doc.save(`Vault_Statement_${namePart}_${datePart}.pdf`);

      UI.toast('PDF statement saved successfully', 'success', 4000);
    } catch (err) {
      console.error('PDF export error:', err);
      UI.toast('PDF generation error: ' + err.message, 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="13" height="13"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg> &darr; Download Statement PDF`;
      }
    }
  }

  return { exportAccountStatement };
})();