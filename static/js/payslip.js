/* ═══════════════════════════════════════════════════════════════
   SmartHR — Payslip PDF Generator (jsPDF client-side)
   Generates a polished A4 payslip PDF with dark-themed header,
   salary breakdown table, and company watermark.
═══════════════════════════════════════════════════════════════ */

window.PayslipGenerator = (function () {
  'use strict';

  function hexToRgb(hex) {
    var r = parseInt(hex.slice(1,3),16);
    var g = parseInt(hex.slice(3,5),16);
    var b = parseInt(hex.slice(5,7),16);
    return [r, g, b];
  }

  /**
   * generatePayslip — builds and auto-downloads a PDF payslip.
   * @param {Object} data  — employee + salary breakdown
   */
  function generatePayslip(data) {
    if (typeof window.jspdf === 'undefined') {
      alert('PDF library not loaded. Please refresh the page.');
      return;
    }

    var jsPDF = window.jspdf.jsPDF;
    var doc   = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
    var W     = doc.internal.pageSize.getWidth();   // 210
    var H     = doc.internal.pageSize.getHeight();  // 297

    /* ── Page background ── */
    doc.setFillColor(10, 15, 30);
    doc.rect(0, 0, W, H, 'F');

    /* ── Header band ── */
    doc.setFillColor(13, 31, 60);
    doc.roundedRect(0, 0, W, 52, 0, 0, 'F');

    /* ── Header accent line ── */
    doc.setFillColor(0, 212, 255);
    doc.rect(0, 50, W, 2, 'F');

    /* ── Logo block ── */
    doc.setFillColor(0, 212, 255);
    doc.roundedRect(14, 10, 28, 28, 4, 4, 'F');
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(10, 15, 30);
    doc.text('HR', 28, 26, { align: 'center' });

    /* ── Company name ── */
    doc.setFontSize(22);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(255, 255, 255);
    doc.text('SmartHR', 48, 22);

    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(148, 163, 184);
    doc.text('AI-Powered Human Resource Management', 48, 29);
    doc.text('payroll@smarthr.com  ·  www.smarthr.com', 48, 35);

    /* ── Payslip label (top-right) ── */
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 212, 255);
    doc.text('SALARY SLIP', W - 14, 20, { align: 'right' });
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(148, 163, 184);
    doc.text('Pay Period: ' + data.payPeriod, W - 14, 28, { align: 'right' });
    doc.text('Issue Date: ' + data.issueDate,  W - 14, 34, { align: 'right' });

    /* ── Employee info section ── */
    var ey = 64;
    doc.setFillColor(17, 24, 39);
    doc.roundedRect(10, ey, W - 20, 42, 6, 6, 'F');
    doc.setDrawColor(255, 255, 255, 0.06);
    doc.setLineWidth(0.3);
    doc.roundedRect(10, ey, W - 20, 42, 6, 6, 'S');

    doc.setFontSize(9);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(148, 163, 184);
    doc.text('EMPLOYEE DETAILS', 18, ey + 10);

    doc.setFontSize(11);
    doc.setTextColor(226, 232, 240);
    doc.text(data.employeeName, 18, ey + 20);

    doc.setFontSize(8.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(148, 163, 184);
    doc.text(data.designation + '  ·  ' + data.department, 18, ey + 28);
    doc.text('Employee ID: ' + data.employeeId + '   ·   Joining Date: ' + data.joiningDate, 18, ey + 35);

    /* Right column */
    doc.setFontSize(8.5);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 212, 255);
    doc.text('Net Pay', W - 18, ey + 14, { align: 'right' });
    doc.setFontSize(16);
    doc.text('₹ ' + formatINR(data.netSalary), W - 18, ey + 26, { align: 'right' });
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(16, 185, 129);
    doc.text('✓ Credited', W - 18, ey + 34, { align: 'right' });

    /* ── Earnings / Deductions table ── */
    var ty = ey + 52;

    /* Earnings column header */
    doc.setFillColor(0, 212, 255, 0.1);
    doc.setFillColor(26, 34, 53);
    doc.roundedRect(10, ty, (W - 24) / 2, 8, 3, 3, 'F');
    doc.setFontSize(8.5);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 212, 255);
    doc.text('EARNINGS', 18, ty + 5.5);
    doc.text('AMOUNT', (W / 2) - 2, ty + 5.5, { align: 'right' });

    /* Deductions column header */
    doc.setFillColor(26, 34, 53);
    doc.roundedRect(W / 2 + 2, ty, (W - 24) / 2, 8, 3, 3, 'F');
    doc.setTextColor(239, 68, 68);
    doc.text('DEDUCTIONS', W / 2 + 10, ty + 5.5);
    doc.text('AMOUNT', W - 14, ty + 5.5, { align: 'right' });

    /* Earnings rows */
    var earnings = [
      { label: 'Basic Salary',     value: data.basic },
      { label: 'HRA (40%)',         value: data.hra },
      { label: 'DA (12%)',          value: data.da },
      { label: 'Bonus',             value: data.bonus || 0 }
    ];

    var deductions = [
      { label: 'PF (12% Basic)',    value: data.pf },
      { label: 'Professional Tax',  value: data.professionalTax || 200 },
      { label: 'TDS',               value: data.tds || 0 }
    ];

    var rowH = 9;
    var rowY = ty + 12;

    doc.setFontSize(8.5);
    doc.setFont('helvetica', 'normal');

    earnings.forEach(function (row, i) {
      if (i % 2 === 0) {
        doc.setFillColor(17, 24, 39);
        doc.rect(10, rowY + i * rowH - 2, (W - 24) / 2, rowH, 'F');
      }
      doc.setTextColor(226, 232, 240);
      doc.text(row.label, 18, rowY + i * rowH + 4);
      doc.setTextColor(16, 185, 129);
      doc.text('₹ ' + formatINR(row.value), (W / 2) - 2, rowY + i * rowH + 4, { align: 'right' });
    });

    deductions.forEach(function (row, i) {
      if (i % 2 === 0) {
        doc.setFillColor(17, 24, 39);
        doc.rect(W / 2 + 2, rowY + i * rowH - 2, (W - 24) / 2, rowH, 'F');
      }
      doc.setTextColor(226, 232, 240);
      doc.text(row.label, W / 2 + 10, rowY + i * rowH + 4);
      doc.setTextColor(239, 68, 68);
      doc.text('₹ ' + formatINR(row.value), W - 14, rowY + i * rowH + 4, { align: 'right' });
    });

    /* Totals row */
    var totY = rowY + Math.max(earnings.length, deductions.length) * rowH + 4;
    doc.setDrawColor(255, 255, 255, 0.06);
    doc.setLineWidth(0.3);
    doc.line(10, totY - 2, W / 2 - 2, totY - 2);
    doc.line(W / 2 + 2, totY - 2, W - 10, totY - 2);

    var totalEarnings   = earnings.reduce(function(s, r){ return s + r.value; }, 0);
    var totalDeductions = deductions.reduce(function(s, r){ return s + r.value; }, 0);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.setTextColor(226, 232, 240);
    doc.text('Total Earnings',   18,        totY + 5);
    doc.setTextColor(16, 185, 129);
    doc.text('₹ ' + formatINR(totalEarnings), (W / 2) - 2, totY + 5, { align: 'right' });

    doc.setTextColor(226, 232, 240);
    doc.text('Total Deductions', W / 2 + 10, totY + 5);
    doc.setTextColor(239, 68, 68);
    doc.text('₹ ' + formatINR(totalDeductions), W - 14, totY + 5, { align: 'right' });

    /* ── Net Pay banner ── */
    var netY = totY + 14;
    doc.setFillColor(0, 212, 255);
    doc.roundedRect(10, netY, W - 20, 18, 6, 6, 'F');
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(10, 15, 30);
    doc.text('NET SALARY PAYABLE', 22, netY + 11);
    doc.setFontSize(13);
    doc.text('₹ ' + formatINR(data.netSalary), W - 18, netY + 11.5, { align: 'right' });

    /* ── Watermark ── */
    doc.setFontSize(52);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(255, 255, 255);
    doc.saveGraphicsState();
    doc.setGState(new doc.GState({ opacity: 0.025 }));
    doc.text('SmartHR', W / 2, H / 2 + 10, { align: 'center', angle: 45 });
    doc.restoreGraphicsState();

    /* ── Footer ── */
    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(71, 85, 105);
    doc.text('This is a computer-generated payslip and does not require a physical signature.', W / 2, H - 12, { align: 'center' });
    doc.text('SmartHR AI-Powered HR Platform  ·  Confidential Document', W / 2, H - 8, { align: 'center' });

    /* ── Download ── */
    var fileName = 'Payslip_' + data.employeeName.replace(/\s+/g, '_') + '_' + data.payPeriod.replace(/\s+/g, '_') + '.pdf';
    doc.save(fileName);
  }

  function formatINR(val) {
    if (!val && val !== 0) return '0';
    return Math.round(val).toLocaleString('en-IN');
  }

  return { generatePayslip: generatePayslip };
})();
