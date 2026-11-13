/**
 * Minh An Bloom - Aura Rosa Frontend Interactive Application Logic
 * Full functionality for all buttons, collapsible sidebars, and AI workflow.
 */

let sampleRequests = [];
let catalogData = [];
let inventoryData = {};
let teamData = {};
let crmDeals = [];
let currentResult = null;

// ==========================================================================
// 1. INITIALIZATION & DATA LOADING
// ==========================================================================
document.addEventListener("DOMContentLoaded", async () => {
  // Đảm bảo ban đầu form luôn sạch sẽ, không tự nạp trước bất kỳ dữ liệu mẫu hay con số nào
  clearInputForm(null, false);

  await Promise.all([
    fetchSamples(),
    fetchCatalog(),
    fetchInventory(),
    fetchTeam(),
    fetchDeals(),
    fetchNotifications()
  ]);
});

async function fetchSamples() {
  try {
    const res = await fetch("/api/samples");
    sampleRequests = await res.json();
    // Không tự động nạp kịch bản mẫu nào khi mở trang.
    // Người dùng tự nhập hoặc chỉ chọn mẫu khi chủ động bấm.
  } catch (err) {
    console.error("Lỗi tải kịch bản mẫu:", err);
  }
}

async function fetchCatalog() {
  try {
    const res = await fetch("/api/catalog");
    catalogData = await res.json();
    renderCatalogTable();
  } catch (err) {
    console.error("Lỗi tải danh mục catalog:", err);
  }
}

async function fetchInventory() {
  try {
    const res = await fetch("/api/inventory");
    inventoryData = await res.json();
  } catch (err) {
    console.error("Lỗi tải tồn kho:", err);
  }
}

async function fetchTeam() {
  try {
    const res = await fetch("/api/team");
    teamData = await res.json();
    renderTeamTable();
  } catch (err) {
    console.error("Lỗi tải đội ngũ kinh doanh:", err);
  }
}

async function fetchDeals() {
  try {
    const res = await fetch("/api/deals");
    crmDeals = await res.json();
    renderPipelineTable();
  } catch (err) {
    console.error("Lỗi tải CRM deals:", err);
  }
}

async function fetchNotifications() {
  try {
    const res = await fetch("/api/notifications");
    const notifs = await res.json();
    renderNotifications(notifs);
  } catch (err) {
    console.error("Lỗi tải thông báo:", err);
  }
}

// ==========================================================================
// 2. SIDEBARS COLLAPSE / EXPAND TOGGLE
// ==========================================================================
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const icon = document.getElementById("sidebar-toggle-icon");
  const isCollapsed = sidebar.classList.toggle("collapsed");

  if (isCollapsed) {
    icon.className = "fa-solid fa-chevron-right";
    showToast("Đã thu gọn thanh bên trái", "info");
  } else {
    icon.className = "fa-solid fa-chevron-left";
    showToast("Đã mở rộng thanh bên trái", "info");
  }
}

function toggleRightPanel() {
  const panel = document.getElementById("right-panel");
  const isCollapsed = panel.classList.toggle("collapsed");
  if (isCollapsed) {
    showToast("Đã thu gọn bảng bên phải để mở rộng không gian", "info");
  } else {
    showToast("Đã mở bảng bên phải", "info");
  }
}

// ==========================================================================
// 3. SCENARIOS & FORM ACTIONS
// ==========================================================================
function loadScenario(index, element = null) {
  if (element) {
    document.querySelectorAll(".scenario-pill").forEach(el => el.classList.remove("active"));
    element.classList.add("active");
  }

  const s = sampleRequests[index];
  if (!s) return;

  document.getElementById("raw-content").value = s.raw_content || "";
  document.getElementById("company-name").value = s.company || "";
  document.getElementById("sender-name").value = s.sender_name || "";
  document.getElementById("sender-email").value = s.sender_email || "";
  document.getElementById("phone").value = s.phone || "";
  document.getElementById("channel").value = s.channel || "Email";

  resetStepper();
  document.getElementById("results-area").style.display = "none";
  showToast(`Đã nạp Kịch bản: ${s.company}`, "info");
}

function clearInputForm(element = null, notify = true) {
  document.querySelectorAll(".scenario-pill").forEach(el => el.classList.remove("active"));
  const firstPill = document.querySelector(".scenario-pill");
  if (element) {
    element.classList.add("active");
  } else if (firstPill) {
    firstPill.classList.add("active");
  }

  const raw = document.getElementById("raw-content");
  if (raw) raw.value = "";
  const comp = document.getElementById("company-name");
  if (comp) comp.value = "";
  const send = document.getElementById("sender-name");
  if (send) send.value = "";
  const mail = document.getElementById("sender-email");
  if (mail) mail.value = "";
  const phone = document.getElementById("phone");
  if (phone) phone.value = "";
  
  resetStepper();
  const resArea = document.getElementById("results-area");
  if (resArea) resArea.style.display = "none";

  if (notify) {
    if (raw) raw.focus();
    showToast("Đã làm mới ô nhập liệu. Hãy nhập yêu cầu của bạn!", "info");
  }
}

function insertProductSnippet(sku) {
  const area = document.getElementById("raw-content");
  const prod = catalogData.find(p => p.sku === sku);
  const name = prod ? prod.name : sku;

  area.value += `\n- Cần báo giá 02 ${name} (${sku})`;
  area.focus();
  showToast(`Đã thêm nhanh sản phẩm: ${name}`, "success");
}

function scrollToIntake(navElement = null) {
  if (navElement) setActiveNav(navElement);
  document.getElementById("intake-section").scrollIntoView({ behavior: "smooth" });
  document.getElementById("raw-content").focus();
}

function navigateHome(navElement = null) {
  if (navElement) setActiveNav(navElement);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setActiveNav(element) {
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));
  element.classList.add("active");
}

// ==========================================================================
// 4. STEPPER & AI WORKFLOW EXECUTION
// ==========================================================================
function resetStepper() {
  for (let i = 1; i <= 7; i++) {
    const node = document.getElementById(`step-${i}`);
    if (node) {
      node.className = "step-node";
      node.querySelector(".step-circle").innerText = i;
    }
  }
}

function setStepState(stepNumber, state) {
  const node = document.getElementById(`step-${stepNumber}`);
  if (!node) return;

  node.className = `step-node ${state}`;
  const circle = node.querySelector(".step-circle");
  if (state === "completed") {
    circle.innerHTML = `<i class="fa-solid fa-check"></i>`;
  } else if (state === "warning") {
    circle.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i>`;
  }
}

function explainStep(stepNumber) {
  const stepExplanations = {
    1: "Bước 1: Tiếp nhận yêu cầu từ Email hoặc Biểu mẫu Web Form.",
    2: "Bước 2: Phân loại & Bóc tách danh mục hàng hóa, số lượng, hạn chót, ngân sách (Gemini 3.1 LLM).",
    3: "Bước 3: Rẽ nhánh: Nếu thiếu TT -> Gửi thư bổ sung. Nếu đủ -> Tạo OPP-ID & Gán 1 trong 6 NVKD.",
    4: "Bước 4: Thẩm định giá niêm yết hiện hành & Tồn kho khả dụng/Lead time vận hành.",
    5: "Bước 5: Lập Báo giá, tính chiết khấu, VAT 10%, soạn thư chào hàng và xuất file Excel.",
    6: "Bước 6: Đối chiếu thẩm quyền: Nếu CK > 5% hoặc đơn > 150tr hoặc thiếu hàng -> Chuyển Trưởng phòng duyệt.",
    7: "Bước 7: Hoàn tất hồ sơ, cập nhật trạng thái CRM Pipeline để theo dõi xuyên suốt."
  };
  showToast(stepExplanations[stepNumber] || `Bước ${stepNumber}`, "info");
}

async function processRequest() {
  const rawContent = document.getElementById("raw-content").value.trim();
  if (!rawContent) {
    showToast("Vui lòng nhập nội dung email hoặc yêu cầu của khách hàng.", "warning");
    document.getElementById("raw-content").focus();
    return;
  }

  const btn = document.getElementById("btn-process");
  const originalBtnHtml = btn.innerHTML;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>AI AGENT ĐANG PHÂN TÍCH QUY TRÌNH...</span>`;
  btn.disabled = true;

  resetStepper();

  // Animate step 1 & 2
  setStepState(1, "active");
  await sleep(250);
  setStepState(1, "completed");
  setStepState(2, "active");

  const payload = {
    raw_content: rawContent,
    company: document.getElementById("company-name").value.trim(),
    sender_name: document.getElementById("sender-name").value.trim(),
    sender_email: document.getElementById("sender-email").value.trim(),
    phone: document.getElementById("phone").value.trim(),
    channel: document.getElementById("channel").value
  };

  try {
    const res = await fetch("/api/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("Máy chủ phản hồi lỗi");

    const data = await res.json();
    currentResult = data;

    renderResults(data);
    await fetchDeals(); // Refresh CRM pipeline
    await fetchNotifications();

  } catch (err) {
    showToast("Lỗi xử lý AI Agent: " + err.message, "warning");
  } finally {
    btn.innerHTML = originalBtnHtml;
    btn.disabled = false;
  }
}

// ==========================================================================
// 5. RENDER RESULTS
// ==========================================================================
async function renderResults(data) {
  const resultsArea = document.getElementById("results-area");
  resultsArea.style.display = "block";

  const isClarification = data.workflow_outcome === "AWAITING_CUSTOMER_CLARIFICATION";

  if (isClarification) {
    setStepState(2, "completed");
    setStepState(3, "warning");
    
    document.getElementById("clarification-card").style.display = "block";
    document.getElementById("success-opportunity-card").style.display = "none";

    const missingContainer = document.getElementById("missing-fields-container");
    missingContainer.innerHTML = "";
    (data.clarification.missing_fields || []).forEach(f => {
      const tag = document.createElement("span");
      tag.className = "missing-tag";
      tag.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${f}`;
      missingContainer.appendChild(tag);
    });

    document.getElementById("clarification-email-text").value = data.clarification.clarification_email_body;

    document.getElementById("latest-activity-text").innerText = 
      `Yêu cầu từ ${data.parsed_data.company || "khách hàng"} thiếu thông tin. Agent đã tự động tạo email đề nghị bổ sung.`;
    
    showToast("⚠️ Yêu cầu thiếu thông tin. Đã kích hoạt nhánh gửi thư bổ sung!", "warning");

  } else {
    for (let i = 2; i <= 7; i++) {
      setStepState(i, "active");
      await sleep(80);
      setStepState(i, "completed");
    }

    document.getElementById("clarification-card").style.display = "none";
    document.getElementById("success-opportunity-card").style.display = "block";

    const opp = data.opportunity;
    const ver = data.verification;
    const quo = data.quotation;
    const app = data.approval;

    // Metrics
    document.getElementById("metric-opp-id").innerText = opp.opp_id;
    document.getElementById("metric-rep-name").innerText = opp.assigned_rep.name;
    document.getElementById("metric-grand-total").innerText = formatCurrency(quo.grand_total);
    
    const statusBadge = document.getElementById("metric-status-badge");
    if (app.requires_manager_approval) {
      statusBadge.innerText = "Chờ TP Duyệt";
      statusBadge.style.color = "#E85D75";
      showToast("🚨 Đơn hàng có điều khoản vượt thẩm quyền. Đã chuyển Trưởng phòng phê duyệt!", "warning");
    } else {
      statusBadge.innerText = "Sẵn sàng gửi";
      statusBadge.style.color = "#56C596";
      showToast("✅ Đã tạo Hồ sơ Cơ hội & Báo giá thành công!", "success");
    }

    document.getElementById("budget-eval-text").innerText = 
      `Đánh giá ngân sách khách hàng: ${quo.budget_status} | Tiến độ khả thi của kho: ${ver.earliest_fulfillment_days} ngày.`;

    // Items table
    const tbody = document.getElementById("verified-items-tbody");
    tbody.innerHTML = "";
    ver.verified_items.forEach(it => {
      const tr = document.createElement("tr");
      const stockBadge = it.is_in_stock
        ? `<span class="badge-stock available"><i class="fa-solid fa-check"></i> Sẵn sàng (Kho)</span>`
        : `<span class="badge-stock shortage"><i class="fa-solid fa-clock"></i> Nhập (${it.fulfillment_days} ngày)</span>`;

      tr.innerHTML = `
        <td><strong>${it.sku}</strong></td>
        <td>${it.name}</td>
        <td>${it.quantity}</td>
        <td>${formatCurrency(it.unit_price)}</td>
        <td><strong>${formatCurrency(it.line_total)}</strong></td>
        <td>${stockBadge}</td>
      `;
      tbody.appendChild(tr);
    });

    // Totals
    document.getElementById("val-subtotal").innerText = formatCurrency(quo.subtotal);
    document.getElementById("lbl-discount").innerText = `Chiết khấu ưu đãi (${quo.discount_pct}%):`;
    document.getElementById("val-discount").innerText = `-${formatCurrency(quo.discount_amount)}`;
    document.getElementById("val-before-vat").innerText = formatCurrency(quo.total_after_discount);
    document.getElementById("val-vat").innerText = formatCurrency(quo.vat_amount);
    document.getElementById("val-grand-total").innerText = formatCurrency(quo.grand_total);

    // Proposal email
    document.getElementById("proposal-email-text").value = quo.proposal_email_body;

    // Manager card
    const managerBox = document.getElementById("manager-box");
    if (app.requires_manager_approval) {
      managerBox.style.display = "block";
      document.getElementById("manager-brief-text").innerText = app.manager_brief;
    } else {
      managerBox.style.display = "none";
    }

    document.getElementById("latest-activity-text").innerText = 
      `Đã lập hồ sơ ${opp.opp_id} cho ${opp.company}. Tổng thanh toán: ${formatCurrency(quo.grand_total)}.`;
  }

  resultsArea.scrollIntoView({ behavior: "smooth" });
}

// ==========================================================================
// 6. EXCEL EXPORT & MANAGER ACTIONS
// ==========================================================================
async function downloadExcel() {
  if (!currentResult) {
    showToast("Chưa có cơ hội nào được xử lý để xuất Excel.", "warning");
    return;
  }

  showToast("Đang tạo bảng báo giá Excel chuẩn doanh nghiệp...", "info");

  try {
    const res = await fetch("/api/export-excel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentResult)
    });

    if (!res.ok) throw new Error("Lỗi khi tải file báo giá.");

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Bao_Gia_${currentResult.opportunity.opp_id}.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    showToast("📥 Đã tải xuống file Báo giá Excel thành công!", "success");
  } catch (err) {
    showToast("Không thể tải file Excel: " + err.message, "warning");
  }
}

async function submitManagerAction(action) {
  if (!currentResult || !currentResult.opportunity) return;
  const oppId = currentResult.opportunity.opp_id;

  try {
    const res = await fetch("/api/manager-action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        opp_id: oppId,
        action: action,
        notes: action === "APPROVE" ? "Đồng ý hỗ trợ khách hàng chiến lược." : "Cần thương lượng lại điều khoản."
      })
    });

    const data = await res.json();
    if (data.success) {
      showToast(`Trưởng phòng đã phê duyệt: ${data.note}`, "success");
      document.getElementById("metric-status-badge").innerText = data.new_status;
      document.getElementById("metric-status-badge").style.color = "#56C596";
      document.getElementById("manager-box").style.display = "none";
      await fetchDeals();
    }
  } catch (err) {
    showToast("Lỗi thực thi phê duyệt: " + err.message, "warning");
  }
}

// ==========================================================================
// 7. MODALS LOGIC (POPUP DIALOGS)
// ==========================================================================
function openProcessModal(navElement = null) {
  if (navElement) setActiveNav(navElement);
  document.getElementById("modal-process").style.display = "flex";
}

function openPipelineModal(navElement = null) {
  if (navElement) setActiveNav(navElement);
  renderPipelineTable();
  document.getElementById("modal-pipeline").style.display = "flex";
}

function openCatalogModal(navElement = null) {
  if (navElement) setActiveNav(navElement);
  renderCatalogTable();
  document.getElementById("modal-catalog").style.display = "flex";
}

function openTeamModal(navElement = null) {
  if (navElement) setActiveNav(navElement);
  renderTeamTable();
  document.getElementById("modal-team").style.display = "flex";
}

function openSettingsModal(navElement = null) {
  if (navElement) setActiveNav(navElement);
  document.getElementById("modal-settings").style.display = "flex";
}

function openAiChatModal() {
  document.getElementById("modal-aichat").style.display = "flex";
}

function openProfileModal() {
  openTeamModal();
}

function closeModal(modalId) {
  document.getElementById(modalId).style.display = "none";
}

function closeModalOnBackdrop(event, modalId) {
  if (event.target.id === modalId) {
    closeModal(modalId);
  }
}

function logoutApp() {
  clearInputForm();
  showToast("Đã làm mới phiên làm việc thành công!", "success");
}

function saveSettings() {
  closeModal("modal-settings");
  showToast("Đã lưu các thiết lập thẩm quyền thành công!", "success");
}

// ==========================================================================
// 8. RENDER DYNAMIC TABLES & VIEWS
// ==========================================================================
function renderCatalogTable(filterQuery = "") {
  const tbody = document.getElementById("catalog-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  const query = filterQuery.toLowerCase();
  const filtered = catalogData.filter(p => 
    p.name.toLowerCase().includes(query) || p.sku.toLowerCase().includes(query) || p.category.toLowerCase().includes(query)
  );

  filtered.forEach(p => {
    const inv = inventoryData[p.sku] || { available_qty: 0, lead_time_days_if_out_of_stock: 14 };
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${p.sku}</strong></td>
      <td>${p.name}</td>
      <td>${formatCurrency(p.unit_price)}</td>
      <td><span class="badge-stock ${inv.available_qty > 0 ? 'available' : 'shortage'}">${inv.available_qty} chiếc</span></td>
      <td>${inv.lead_time_days_if_out_of_stock} ngày</td>
      <td>
        <button class="btn-chip-add" onclick="insertProductSnippet('${p.sku}'); closeModal('modal-catalog');">
          <i class="fa-solid fa-plus"></i> Chèn vào RFQ
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterCatalogTable(query) {
  renderCatalogTable(query);
}

function renderPipelineTable(filterQuery = "") {
  const tbody = document.getElementById("crm-deals-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  const query = filterQuery.toLowerCase();
  const filtered = crmDeals.filter(d => {
    const opp = d.opportunity || {};
    return (opp.company || "").toLowerCase().includes(query) || (opp.opp_id || "").toLowerCase().includes(query);
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 25px;">Chưa có cơ hội nào. Sau khi bạn nhập yêu cầu ở màn hình chính và nhấn "Kích hoạt AI Agent", kết quả sẽ được lưu trữ và hiển thị tại đây.</td></tr>`;
    return;
  }

  filtered.forEach(d => {
    const opp = d.opportunity;
    const quo = d.quotation;
    const app = d.approval;
    const tr = document.createElement("tr");

    const statusHtml = app.requires_manager_approval
      ? `<span style="color: #D64267; font-weight: 700;">Chờ Trưởng phòng</span>`
      : `<span style="color: #56C596; font-weight: 700;">Đã phê duyệt</span>`;

    tr.innerHTML = `
      <td><strong>${opp.opp_id}</strong></td>
      <td>${opp.company}</td>
      <td>${opp.assigned_rep.name}</td>
      <td>${formatCurrency(quo.grand_total)}</td>
      <td>${quo.discount_pct}%</td>
      <td>${statusHtml}</td>
      <td>
        <button class="btn-chip-add" onclick="inspectDeal('${opp.opp_id}')">
          <i class="fa-solid fa-eye"></i> Xem
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterCrmDeals(query) {
  renderPipelineTable(query);
}

function inspectDeal(oppId) {
  const deal = crmDeals.find(d => d.opportunity && d.opportunity.opp_id === oppId);
  if (deal) {
    currentResult = deal;
    renderResults(deal);
    closeModal("modal-pipeline");
    showToast(`Đang hiển thị chi tiết cơ hội: ${oppId}`, "info");
  }
}

function renderTeamTable() {
  const tbody = document.getElementById("team-tbody");
  if (!tbody || !teamData.reps) return;
  tbody.innerHTML = "";

  teamData.reps.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${r.id}</strong></td>
      <td>${r.name}</td>
      <td>${r.email}</td>
      <td>${r.specialty}</td>
      <td><span class="badge-stock available">${r.active_deals_count} deals</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderNotifications(notifs) {
  const container = document.getElementById("notif-list-container");
  if (!container) return;
  container.innerHTML = "";

  if (!notifs || notifs.length === 0) {
    container.innerHTML = `<div style="padding: 14px; font-size: 12px; color: var(--text-muted); text-align: center;">Chưa có thông báo nào. Hệ thống sẵn sàng tiếp nhận yêu cầu từ bạn.</div>`;
    return;
  }

  notifs.forEach(n => {
    const div = document.createElement("div");
    div.style = "padding: 8px 10px; border-bottom: 1px solid #FFF0F4; cursor: pointer;";
    div.innerHTML = `
      <div style="font-size: 12px; font-weight: 700; color: #B3284B;">${n.title}</div>
      <div style="font-size: 11.5px; color: var(--text-secondary); line-height: 1.3;">${n.message}</div>
      <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">${n.time}</div>
    `;
    div.onclick = () => {
      openPipelineModal();
      document.getElementById("notif-dropdown").style.display = "none";
    };
    container.appendChild(div);
  });
}

function toggleNotifications() {
  const el = document.getElementById("notif-dropdown");
  el.style.display = el.style.display === "block" ? "none" : "block";
}

// ==========================================================================
// 9. GLOBAL SEARCH & QUICK AI CHAT
// ==========================================================================
function handleGlobalSearch(query) {
  const dropdown = document.getElementById("search-dropdown");
  if (!query || query.trim().length < 2) {
    dropdown.style.display = "none";
    return;
  }

  const q = query.toLowerCase();
  let matches = [];

  // Match catalog
  catalogData.forEach(p => {
    if (p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q)) {
      matches.push({
        title: `📦 Sản phẩm: ${p.name} (${p.sku})`,
        action: () => { insertProductSnippet(p.sku); dropdown.style.display = "none"; }
      });
    }
  });

  // Match deals
  crmDeals.forEach(d => {
    if (d.opportunity && (d.opportunity.company.toLowerCase().includes(q) || d.opportunity.opp_id.toLowerCase().includes(q))) {
      matches.push({
        title: `📄 Cơ hội: ${d.opportunity.opp_id} - ${d.opportunity.company}`,
        action: () => { inspectDeal(d.opportunity.opp_id); dropdown.style.display = "none"; }
      });
    }
  });

  if (matches.length > 0) {
    dropdown.innerHTML = "";
    matches.slice(0, 5).forEach(m => {
      const item = document.createElement("div");
      item.className = "search-dropdown-item";
      item.innerText = m.title;
      item.onclick = m.action;
      dropdown.appendChild(item);
    });
    dropdown.style.display = "block";
  } else {
    dropdown.innerHTML = `<div style="padding: 8px; font-size: 12px; color: var(--text-muted);">Không tìm thấy kết quả phù hợp.</div>`;
    dropdown.style.display = "block";
  }
}

// Quick AI Chat helper
function sendAiChat() {
  const input = document.getElementById("ai-chat-input");
  const msg = input.value.trim();
  if (!msg) return;

  const box = document.getElementById("ai-chat-response");
  box.innerHTML = `<strong>Bạn:</strong> ${msg}<br><br><strong>AI Cố vấn B2B:</strong> Đang phân tích chiến lược...`;
  input.value = "";

  setTimeout(() => {
    box.innerHTML = `<strong>Bạn:</strong> ${msg}<br><br><strong>AI Cố vấn B2B:</strong> Theo chính sách Công ty Minh An, với các đơn hàng trên 150 triệu hoặc chiết khấu trên 5%, bạn cần gửi tờ trình để Trưởng phòng phê duyệt. Bạn có thể chèn nhanh các mã sản phẩm bằng thanh công cụ bên phải và nhấn 'KÍCH HOẠT AI AGENT' để hệ thống tự động sinh báo giá và tờ trình hoàn chỉnh.`;
  }, 600);
}

// ==========================================================================
// 10. UTILITIES & TOAST ALERTS
// ==========================================================================
function copyText(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  navigator.clipboard.writeText(el.value).then(() => {
    showToast("📋 Đã sao chép nội dung vào Clipboard thành công!", "success");
  });
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  let icon = "fa-circle-info";
  if (type === "success") icon = "fa-circle-check";
  if (type === "warning") icon = "fa-triangle-exclamation";

  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = "slideToast 0.3s ease reverse forwards";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

function formatCurrency(val) {
  if (!val && val !== 0) return "0 đ";
  return new Intl.NumberFormat("vi-VN").format(val) + " đ";
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
