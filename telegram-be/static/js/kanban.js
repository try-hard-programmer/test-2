// telegram-be/static/js/kanban.js
const kanban = {
  sortables: {},
  currentTicket: null,
  currentTicketInSidebar: null,
  filters: {
    agent: null,
    status: null,
  },

  async init() {
    await this.loadAgents();
    await this.loadSummary();
    await this.loadBoard();
    this.initDragDrop();
  },

  async loadAgents() {
    try {
      const res = await fetch("/api/accounts").then((r) => r.json());
      const select = document.getElementById("filterAgent");
      if (!select) return;

      res.accounts.forEach((agent) => {
        const option = document.createElement("option");
        option.value = agent.id;
        option.textContent = agent.account_label;
        select.appendChild(option);
      });
    } catch (e) {
      console.error("Error loading agents:", e);
    }
  },

  applyFilters() {
    this.filters.agent = document.getElementById("filterAgent").value || null;
    this.filters.status = document.getElementById("filterStatus").value || null;
    this.loadBoard();
    this.loadSummary();
  },

  resetFilters() {
    this.filters.agent = null;
    this.filters.status = null;
    document.getElementById("filterAgent").value = "";
    document.getElementById("filterStatus").value = "";
    this.loadBoard();
    this.loadSummary();
  },

  async loadSummary() {
    try {
      let url = "/api/tickets/summary";
      if (this.filters.agent) url += `?agent_id=${this.filters.agent}`;

      const res = await fetch(url).then((r) => r.json());
      const summary = res.summary;

      const setCount = (id, val) => {
        let elem = document.querySelector(`#boardView #${id}`);
        if (!elem) elem = document.getElementById(id);
        if (elem) elem.textContent = val;
      };

      setCount("summaryTotal", summary.total);
      setCount("summaryOpen", summary.by_status.open);
      setCount("summaryInProgress", summary.by_status.in_progress);
      setCount("summaryResolved", summary.by_status.resolved);
      setCount("summaryClosed", summary.by_status.closed);
    } catch (e) {
      console.error("Error loading summary:", e);
    }
  },

  async loadBoard() {
    // If status filter active, only load that status
    if (this.filters.status) {
      try {
        let url = `/api/tickets/by-status/${this.filters.status}`;
        if (this.filters.agent) url += `?agent_id=${this.filters.agent}`;

        const res = await fetch(url).then((r) => r.json());

        // Clear all columns
        ["open", "in_progress", "resolved", "closed"].forEach((s) =>
          this.renderColumn(s, [])
        );
        // Render only filtered status
        this.renderColumn(this.filters.status, res.tickets);
      } catch (e) {
        console.error("Error loading filtered tickets:", e);
      }
    } else {
      // Load all statuses
      const statuses = ["open", "in_progress", "resolved", "closed"];
      for (const status of statuses) {
        try {
          let url = `/api/tickets/by-status/${status}`;
          if (this.filters.agent) url += `?agent_id=${this.filters.agent}`;

          const res = await fetch(url).then((r) => r.json());
          this.renderColumn(status, res.tickets);
        } catch (e) {
          console.error(`Error loading ${status}:`, e);
        }
      }
    }
  },

  renderColumn(status, tickets) {
    const columnMap = {
      open: "Open",
      in_progress: "InProgress",
      resolved: "Resolved",
      closed: "Closed",
    };

    const columnId = `column${columnMap[status]}`;
    const countId = `count${columnMap[status]}`;

    // USE COLUMNS FROM MAIN BOARD ONLY
    const column = document.querySelector(`#boardView #${columnId}`);
    const count = document.querySelector(`#boardView #${countId}`);

    if (!column) return;
    count.textContent = tickets.length;
    column.innerHTML = tickets
      .map((ticket) => this.createCard(ticket))
      .join("");
  },

  createCard(ticket) {
    const shortId = ticket.id.split("-")[0];
    const priorityClass = `priority-${ticket.priority}`;
    const accountLabel = ticket.telegram_accounts?.account_label || "Unknown";
    return `<div class="kanban-card" data-ticket-id="${
      ticket.id
    }" onclick="kanban.openDetail('${ticket.id}')">
      <div class="ticket-id">#${shortId}</div>
      <div class="ticket-subject">${this.escapeHtml(
        ticket.subject || "No Subject"
      )}</div>
      <div class="flex items-center justify-between mt-2">
        <span class="priority-badge ${priorityClass}">${ticket.priority}</span>
        <span class="text-xs text-gray-500">${accountLabel}</span>
      </div>
      <div class="ticket-customer mt-2">Chat: ${ticket.chat_id}</div>
    </div>`;
  },

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  },

  initDragDrop() {
    const columns = document.querySelectorAll(".kanban-cards");
    columns.forEach((column) => {
      if (this.sortables[column.id]) this.sortables[column.id].destroy();
      this.sortables[column.id] = new Sortable(column, {
        group: "kanban",
        animation: 150,
        ghostClass: "sortable-ghost",
        dragClass: "sortable-drag",
        onEnd: async (evt) => {
          const ticketId = evt.item.dataset.ticketId;
          const newStatus = evt.to.dataset.status;
          if (ticketId && newStatus)
            await this.updateTicketStatus(ticketId, newStatus);
        },
      });
    });
  },

  async updateTicketStatus(ticketId, newStatus) {
    try {
      await fetch(`/api/tickets/${ticketId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (window.showToast)
        window.showToast("success", "Updated", `Ticket moved to ${newStatus}`);
      await this.loadSummary();
    } catch (e) {
      console.error("Error updating ticket:", e);
      if (window.showToast)
        window.showToast("error", "Error", "Failed to update ticket");
      await this.loadBoard();
    }
  },

  async openDetail(ticketId) {
    try {
      const res = await fetch("/api/tickets").then((r) => r.json());
      const ticket = res.tickets.find((t) => t.id === ticketId);
      if (!ticket) {
        if (window.showToast)
          window.showToast("error", "Error", "Ticket not found");
        return;
      }
      this.currentTicket = ticket;
      this.showDetailModal(ticket);
    } catch (e) {
      console.error("Error opening ticket detail:", e);
      if (window.showToast)
        window.showToast("error", "Error", "Failed to load ticket details");
    }
  },

  async showDetailModal(ticket) {
    const shortId = ticket.id.split("-")[0];
    const accountLabel = ticket.telegram_accounts?.account_label || "Unknown";

    const set = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val;
    };

    set("detailTicketId", `#${shortId}`);
    setVal("detailStatus", ticket.status);
    setVal("detailPriority", ticket.priority);
    set("detailSubject", ticket.subject || "No Subject");
    set("detailDescription", ticket.description || "No description");
    set("detailCustomer", `${accountLabel} - Chat: ${ticket.chat_id}`);
    set("detailCreated", new Date(ticket.created_at).toLocaleString());
    set(
      "detailUpdated",
      ticket.updated_at ? new Date(ticket.updated_at).toLocaleString() : "N/A"
    );

    // ✅ LOAD HISTORY
    try {
      const historyRes = await fetch(`/api/tickets/${ticket.id}/history`);
      const historyData = await historyRes.json();

      const historyContainer = document.getElementById("detailHistory");
      if (historyContainer) {
        if (historyData.history && historyData.history.length > 0) {
          historyContainer.innerHTML = historyData.history
            .map((h) => {
              const icon =
                h.field_changed === "status"
                  ? "📊"
                  : h.field_changed === "priority"
                  ? "🎯"
                  : h.field_changed === "created"
                  ? "✨"
                  : "📝";

              const oldVal = h.old_value
                ? `<span class="text-red-500 line-through">${h.old_value}</span> → `
                : "";

              return `
            <div class="flex gap-3 py-2.5 border-b border-gray-100 last:border-0">
              <div class="text-gray-400 text-xs whitespace-nowrap pt-0.5">
                ${new Date(h.changed_at).toLocaleString("en-US", {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
              <div class="flex-1 text-sm">
                <div>
                  <span class="mr-1">${icon}</span>
                  <span class="font-medium capitalize">${h.field_changed.replace(
                    "_",
                    " "
                  )}</span>: 
                  ${oldVal}
                  <span class="text-green-600 font-medium">${h.new_value}</span>
                </div>
                <div class="text-xs text-gray-400 mt-1">by ${h.changed_by}</div>
              </div>
            </div>
          `;
            })
            .join("");
        } else {
          historyContainer.innerHTML =
            '<div class="text-gray-400 text-sm text-center py-4">No changes yet</div>';
        }
      }
    } catch (e) {
      console.error("Error loading history:", e);
      const historyContainer = document.getElementById("detailHistory");
      if (historyContainer) {
        historyContainer.innerHTML =
          '<div class="text-red-400 text-sm text-center py-3">Failed to load history</div>';
      }
    }

    const modal = document.getElementById("ticketDetailModal");
    if (modal) modal.classList.remove("hidden");
  },

  closeDetail() {
    const modal = document.getElementById("ticketDetailModal");
    if (modal) modal.classList.add("hidden");
    this.currentTicket = null;
  },

  async saveDetail() {
    if (!this.currentTicket) return;
    const newStatus = document.getElementById("detailStatus").value;
    const newPriority = document.getElementById("detailPriority").value;
    try {
      await fetch(`/api/tickets/${this.currentTicket.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus, priority: newPriority }),
      });
      if (window.showToast)
        window.showToast("success", "Saved", "Ticket updated successfully");
      this.closeDetail();
      await this.loadBoard();
      await this.loadSummary();
    } catch (e) {
      console.error("Error saving ticket:", e);
      if (window.showToast)
        window.showToast("error", "Error", "Failed to save changes");
    }
  },

  jumpToChat() {
    if (!this.currentTicket) return;
    const accountId = this.currentTicket.account_id;
    const chatId = this.currentTicket.chat_id;
    if (window.state && window.state.conversations) {
      const conv = window.state.conversations.find(
        (c) => c.telegram_account_id === accountId && c.chat_id === chatId
      );
      if (conv && window.app) {
        this.closeDetail();
        const chatTab = document.querySelector(
          "button[onclick=\"switchTab('chats')\"]"
        );
        if (chatTab) chatTab.click();
        window.app.selectConversation(conv.id);
      } else {
        if (window.showToast)
          window.showToast("error", "Error", "Chat not found");
      }
    }
  },
};

window.kanban = kanban;
