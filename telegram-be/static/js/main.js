// static/js/main.js - FULL FILE
import { state, setState } from "./state.js";
import { api } from "./api.js";
import * as ui from "./ui.js";
import { connectWebSocket } from "./socket.js";
import { showToast } from "./utils.js";

const app = {
  pendingVerification: null,

  async init() {
    connectWebSocket();
    await this.refreshData();
    this.setupTabs();

    window.addAccount = this.submitAddAccount.bind(this);
    window.hideAddAccountModal = this.hideAddAccountModal.bind(this);
    window.showAddAccountModal = this.showAddAccountModal.bind(this);
  },

  async refreshData() {
    try {
      const [convData, ticketData, accountData] = await Promise.all([
        api.getConversations(),
        api.getTickets(),
        api.getAccounts(),
      ]);

      state.conversations = convData.conversations;
      state.allTickets = ticketData.tickets;
      state.agents = accountData.accounts;

      state.activeTickets = {};
      state.allTickets.forEach((t) => {
        if (["open", "in_progress"].includes(t.status)) {
          state.activeTickets[`${t.account_id}_${t.chat_id}`] = t;
        }
      });

      ui.renderConversations();
      if (state.currentTab === "tickets") ui.renderTicketsList();
      if (state.currentTab === "agents") ui.renderAgents();
    } catch (e) {
      console.error("Init failed", e);
    }
  },

  setupTabs() {
    window.switchTab = (tab) => {
      state.currentTab = tab;
      document
        .querySelectorAll(".sidebar-tab")
        .forEach((b) =>
          b.classList.remove(
            "active",
            "text-blue-600",
            "border-b-2",
            "border-blue-600"
          )
        );
      event.target.classList.add(
        "active",
        "text-blue-600",
        "border-b-2",
        "border-blue-600"
      );

      ["chatsTab", "ticketsTab", "boardTab", "agentsTab"].forEach(
        (id) => (document.getElementById(id).style.display = "none")
      );

      const chatView = document.getElementById("chatView");
      const boardView = document.getElementById("boardView");

      if (tab === "chats") {
        document.getElementById("chatsTab").style.display = "block";
        if (chatView) chatView.style.display = "flex";
        if (boardView) boardView.style.display = "none";
        ui.renderConversations();
      } else if (tab === "tickets") {
        document.getElementById("ticketsTab").style.display = "block";
        if (chatView) chatView.style.display = "flex";
        if (boardView) boardView.style.display = "none";
        ui.renderTicketsList();
      } else if (tab === "board") {
        document.getElementById("boardTab").style.display = "block";
        if (chatView) chatView.style.display = "none";
        if (boardView) boardView.style.display = "flex";
        if (window.kanban) window.kanban.init();
      } else if (tab === "agents") {
        document.getElementById("agentsTab").style.display = "block";
        if (chatView) chatView.style.display = "flex";
        if (boardView) boardView.style.display = "none";
        ui.renderAgents();
      }
    };
  },

  async selectConversation(id) {
    const conv = state.conversations.find((c) => c.id === id);
    if (!conv) return;

    state.currentConversation = conv;
    ui.renderConversations();

    try {
      const data = await api.getMessages(id);
      state.messages[id] = data.messages;

      document.getElementById("emptyChat").style.display = "none";
      document.getElementById("activeChat").style.display = "flex";
      document.getElementById("activeChat").classList.remove("hidden");

      document.getElementById("chatTitle").textContent =
        conv.chat_name || `Chat: ${conv.chat_id}`;
      document.getElementById(
        "chatSubtitle"
      ).textContent = `${conv.telegram_account_id.substring(0, 8)}...`;

      ui.renderMessages(id);
      ui.updateTicketSidebar();
    } catch (e) {
      console.error(e);
    }
  },

  async selectTicketFromList(accountId, chatId) {
    const conv = state.conversations.find(
      (c) => c.telegram_account_id === accountId && c.chat_id === chatId
    );
    if (conv) {
      document.querySelector("button[onclick=\"switchTab('chats')\"]").click();
      this.selectConversation(conv.id);
    } else {
      showToast("error", "Error", "Conversation log not found locally");
    }
  },

  async sendReply(event) {
    event.preventDefault();
    const input = document.getElementById("replyInput");
    const text = input.value.trim();
    if (!text || !state.currentConversation) return;

    try {
      await api.sendReply(state.currentConversation.id, text);
      input.value = "";
    } catch (e) {
      showToast("error", "Failed", e.message);
    }
  },

  showCreateTicketModal() {
    document.getElementById("createTicketModal").classList.remove("hidden");
    document.getElementById("createTicketModal").classList.add("flex");
  },

  async deleteConversation(convId) {
    if (!confirm("Delete this conversation? All messages will be removed."))
      return;

    try {
      const response = await fetch(`/api/conversations/${convId}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Failed to delete");

      // Clear UI if this was the active conversation
      if (
        state.currentConversation &&
        state.currentConversation.id === convId
      ) {
        state.currentConversation = null;
        document.getElementById("emptyChat").style.display = "flex";
        document.getElementById("activeChat").style.display = "none";
        document.getElementById("activeChat").classList.add("hidden");
      }

      await this.refreshData();
      showToast("info", "Deleted", "Conversation removed");
    } catch (e) {
      console.error(e);
      showToast("error", "Error", "Failed to delete conversation");
    }
  },

  async submitCreateTicket(event) {
    event.preventDefault();
    if (!state.currentConversation) return;

    const payload = {
      account_id: state.currentConversation.telegram_account_id,
      chat_id: state.currentConversation.chat_id,
      subject: document.getElementById("newTicketSubject").value,
      priority: document.getElementById("newTicketPriority").value,
      description: document.getElementById("newTicketDescription").value,
    };

    try {
      const res = await api.createTicket(payload);
      document.getElementById("createTicketModal").classList.add("hidden");
      document.getElementById("createTicketModal").classList.remove("flex");

      state.activeTickets[`${payload.account_id}_${payload.chat_id}`] =
        res.ticket;
      ui.updateTicketSidebar();
      ui.renderConversations();
      showToast("success", "Ticket Created", "Ticket created successfully");
    } catch (e) {
      alert(e.message);
    }
  },

  async updateCurrentTicketStatus() {
    if (!state.currentConversation) return;

    const key = `${state.currentConversation.telegram_account_id}_${state.currentConversation.chat_id}`;
    const ticket = state.activeTickets[key];

    if (!ticket) return;

    const newStatus = document.getElementById("ticketStatusSelect").value;

    try {
      await api.updateTicket(ticket.id, { status: newStatus });

      ticket.status = newStatus;
      if (["open", "in_progress"].includes(newStatus)) {
        state.activeTickets[key] = ticket;
      } else {
        delete state.activeTickets[key];
      }

      ui.updateTicketSidebar();
      ui.renderConversations();
      showToast("success", "Updated", `Status changed to ${newStatus}`);
    } catch (e) {
      console.error(e);
      showToast("error", "Error", "Failed to update status");
    }
  },

  async closeCurrentTicket() {
    if (!confirm("Resolve this ticket?")) return;
    if (!state.currentConversation) return;
    const key = `${state.currentConversation.telegram_account_id}_${state.currentConversation.chat_id}`;
    const ticket = state.activeTickets[key];

    try {
      await api.updateTicket(ticket.id, { status: "resolved" });
      delete state.activeTickets[key];
      ui.updateTicketSidebar();
      ui.renderConversations();
      showToast("success", "Resolved", "Ticket resolved");
    } catch (e) {
      console.error(e);
    }
  },

  async deleteCurrentTicket() {
    if (!confirm("Delete ticket?")) return;
    if (!state.currentConversation) return;
    const key = `${state.currentConversation.telegram_account_id}_${state.currentConversation.chat_id}`;
    const ticket = state.activeTickets[key];

    try {
      await api.deleteTicket(ticket.id);
      delete state.activeTickets[key];
      ui.updateTicketSidebar();
      ui.renderConversations();
      showToast("info", "Deleted", "Ticket deleted");
    } catch (e) {
      console.error(e);
    }
  },

  showAddAccountModal() {
    document.getElementById("addAccountModal").classList.remove("hidden");
    document.getElementById("addAccountModal").classList.add("flex");
    document.getElementById("addAccountError").classList.add("hidden");

    this.pendingVerification = null;
    document.getElementById("initialFields").classList.remove("hidden");
    document.getElementById("verificationField").classList.add("hidden");
    document.getElementById("addAccountSubmitBtn").innerHTML =
      "<span>Request Code</span>";
  },

  hideAddAccountModal() {
    document.getElementById("addAccountModal").classList.add("hidden");
    document.getElementById("addAccountModal").classList.remove("flex");
  },

  async submitAddAccount(event) {
    event.preventDefault();
    const errorBanner = document.getElementById("addAccountError");
    const btn = document.getElementById("addAccountSubmitBtn");
    errorBanner.classList.add("hidden");

    const label = document.getElementById("accountLabel").value;
    const apiId = parseInt(document.getElementById("apiId").value);
    const apiHash = document.getElementById("apiHash").value;
    const phone = document.getElementById("phone").value;

    if (!phone.startsWith("+")) {
      errorBanner.textContent = "Phone must start with + (e.g. +62...)";
      errorBanner.classList.remove("hidden");
      return;
    }

    try {
      btn.disabled = true;
      btn.innerHTML =
        '<span class="animate-spin h-4 w-4 border-2 border-white rounded-full border-t-transparent mr-2"></span> Processing...';

      if (this.pendingVerification) {
        const code = document.getElementById("verificationCode").value;
        if (!code) throw new Error("Please enter the code");

        await api.verifyAccount({
          phone,
          code,
          api_id: apiId,
          api_hash: apiHash,
          label,
        });

        showToast("success", "Success", "Account connected successfully");
        this.hideAddAccountModal();
        this.refreshData();
      } else {
        const res = await api.addAccount({
          label,
          api_id: apiId,
          api_hash: apiHash,
          phone,
        });

        if (res.status === "code_sent") {
          this.pendingVerification = true;
          document.getElementById("initialFields").classList.add("hidden");
          document
            .getElementById("verificationField")
            .classList.remove("hidden");
          btn.innerHTML = "<span>Verify Code</span>";
          btn.disabled = false;
          return;
        } else if (res.status === "success") {
          showToast("success", "Success", "Account connected (No code needed)");
          this.hideAddAccountModal();
          this.refreshData();
        }
      }
    } catch (e) {
      errorBanner.textContent = e.message || "Operation failed";
      errorBanner.classList.remove("hidden");
      btn.disabled = false;
      btn.innerHTML = this.pendingVerification
        ? "<span>Verify Code</span>"
        : "<span>Request Code</span>";
    }
  },

  async toggleAgent(id, isActive) {
    // ✅ FIX: Flip the logic - isActive is CURRENT state, we want OPPOSITE
    const newState = !isActive;

    if (!confirm(newState ? "Activate this account?" : "Pause this account?"))
      return;

    try {
      await api.toggleAccount(id, newState); // ✅ Send the NEW state
      showToast(
        "success",
        "Updated",
        `Account ${newState ? "activated" : "paused"}`
      );
      this.refreshData();
    } catch (e) {
      showToast("error", "Error", e.message);
    }
  },

  async deleteAgent(id, label) {
    if (!confirm(`Delete account "${label}"? This cannot be undone.`)) return;
    try {
      await api.deleteAccount(id);
      showToast("info", "Deleted", "Account removed");
      this.refreshData();
    } catch (e) {
      showToast("error", "Error", e.message);
    }
  },

  async openAgentAttributesModal(accountId) {
    try {
      // Fetch current attributes
      const res = await fetch(`/api/accounts/${accountId}/attributes`);
      const data = await res.json();

      if (data.status === "success") {
        const attr = data.attributes;

        // Set account ID
        document.getElementById("attrAccountId").value = accountId;

        // Set persona
        document.getElementById("attrPersona").value = attr.persona || "";

        // Set knowledge
        document.getElementById("attrKnowledge").value = attr.knowledge || "";

        // Set schedule
        if (attr.schedule) {
          document.getElementById("attrTimezone").value =
            attr.schedule.timezone || "Asia/Jakarta";
          document.getElementById("attrWorkHours").value =
            attr.schedule.work_hours || "";

          // Set work days
          document.querySelectorAll(".attr-day").forEach((checkbox) => {
            checkbox.checked =
              attr.schedule.days?.includes(checkbox.value) || false;
          });
        }

        // Set integration
        if (attr.integration) {
          document.getElementById("attrTelegram").checked =
            attr.integration.telegram || false;
          document.getElementById("attrWhatsapp").checked =
            attr.integration.whatsapp || false;
          document.getElementById("attrEmail").checked =
            attr.integration.email || false;
        }

        // Set ticketing settings
        if (attr.ticketing_settings) {
          document.getElementById("attrAutoAssign").checked =
            attr.ticketing_settings.auto_assign || false;
          document.getElementById("attrMaxTickets").value =
            attr.ticketing_settings.max_tickets || "";
          document.getElementById("attrPriorityRules").value =
            attr.ticketing_settings.priority_rules || "auto";
        }

        // Show modal
        document
          .getElementById("agentAttributesModal")
          .classList.remove("hidden");
        document.getElementById("agentAttributesModal").classList.add("flex");
      }
    } catch (e) {
      console.error("Error loading agent attributes:", e);
      showToast("error", "Error", "Failed to load agent attributes");
    }
  },

  closeAgentAttributesModal() {
    document.getElementById("agentAttributesModal").classList.add("hidden");
    document.getElementById("agentAttributesModal").classList.remove("flex");
    document.getElementById("agentAttributesForm").reset();
  },

  async submitAgentAttributes(event) {
    event.preventDefault();

    const accountId = document.getElementById("attrAccountId").value;

    // Collect work days
    const workDays = Array.from(
      document.querySelectorAll(".attr-day:checked")
    ).map((cb) => cb.value);

    const payload = {
      persona: document.getElementById("attrPersona").value.trim() || null,
      knowledge: document.getElementById("attrKnowledge").value.trim() || null,
      schedule: {
        timezone: document.getElementById("attrTimezone").value,
        work_hours: document.getElementById("attrWorkHours").value,
        days: workDays,
      },
      integration: {
        telegram: document.getElementById("attrTelegram").checked,
        whatsapp: document.getElementById("attrWhatsapp").checked,
        email: document.getElementById("attrEmail").checked,
      },
      ticketing_settings: {
        auto_assign: document.getElementById("attrAutoAssign").checked,
        max_tickets:
          parseInt(document.getElementById("attrMaxTickets").value) || null,
        priority_rules: document.getElementById("attrPriorityRules").value,
      },
    };

    try {
      const res = await fetch(`/api/accounts/${accountId}/attributes`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Failed to update attributes");
      }

      this.closeAgentAttributesModal();
      showToast("success", "Saved", "Agent attributes updated successfully");
    } catch (e) {
      console.error("Error saving agent attributes:", e);
      showToast("error", "Error", e.message);
    }
  },
};

window.app = app;
window.state = state;
window.sendReply = app.sendReply.bind(app);
window.showCreateTicketModal = app.showCreateTicketModal.bind(app);
window.submitCreateTicket = app.submitCreateTicket.bind(app);
window.updateTicketStatus = app.updateCurrentTicketStatus.bind(app);
window.closeCurrentTicket = app.closeCurrentTicket.bind(app);
window.deleteCurrentTicket = app.deleteCurrentTicket.bind(app);
window.showAddAccountModal = app.showAddAccountModal.bind(app);
window.hideAddAccountModal = app.hideAddAccountModal.bind(app);
window.addAccount = app.submitAddAccount.bind(app);
window.toggleAgent = app.toggleAgent.bind(app);
window.deleteAgent = app.deleteAgent.bind(app);
window.deleteConversation = app.deleteConversation.bind(app);
document
  .getElementById("agentAttributesForm")
  .addEventListener("submit", (e) => window.app.submitAgentAttributes(e));

app.init();
