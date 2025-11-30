// socket.js - FULL FILE REPLACEMENT
import { state } from "./state.js";
import { showToast } from "./utils.js";
import {
  renderConversations,
  renderMessages,
  updateTicketSidebar,
  renderTicketsList,
} from "./ui.js";

export function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${protocol}//${window.location.host}/api/ws`);

  ws.onopen = () => {
    document.getElementById("wsStatus").innerHTML =
      '<span class="flex items-center gap-1 text-green-200 text-xs">● Connected</span>';
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleWebSocketMessage(data);
  };

  ws.onclose = () => {
    document.getElementById("wsStatus").innerHTML =
      '<span class="flex items-center gap-1 text-red-300 text-xs">○ Disconnected</span>';
    setTimeout(connectWebSocket, 3000);
  };
}

function handleWebSocketMessage(payload) {
  console.log("WS:", payload);
  const { type, data } = payload;

  if (type === "message_received" || type === "message_sent") {
    const convId = data.conversation_id || data.id;
    window.app.refreshData();

    if (
      state.currentConversation &&
      state.currentConversation.telegram_account_id === data.account_id &&
      state.currentConversation.chat_id === data.chat_id
    ) {
      if (!state.messages[state.currentConversation.id])
        state.messages[state.currentConversation.id] = [];

      const exists = state.messages[state.currentConversation.id].find(
        (m) => m.message_id === data.message_id
      );
      if (!exists) {
        state.messages[state.currentConversation.id].push({
          text: data.text,
          direction: type === "message_received" ? "incoming" : "outgoing",
          timestamp: data.timestamp,
          status: data.status,
        });
        renderMessages(state.currentConversation.id);
      }
    }
  } else if (
    type === "ticket_created" ||
    type === "ticket_updated" ||
    type === "ticket_deleted"
  ) {
    const ticket = data;

    // Update state first
    if (type !== "ticket_deleted") {
      const key = `${ticket.account_id}_${ticket.chat_id}`;
      if (["open", "in_progress"].includes(ticket.status)) {
        state.activeTickets[key] = ticket;
      } else {
        delete state.activeTickets[key];
      }
    }

    // Refresh data (this will update state.allTickets)
    window.app.refreshData().then(() => {
      // Only update sidebar if currently viewing the affected chat
      if (state.currentConversation) {
        if (
          ticket.account_id === state.currentConversation.telegram_account_id &&
          ticket.chat_id === state.currentConversation.chat_id
        ) {
          updateTicketSidebar();
        }
      }
    });

    // Refresh kanban if visible
    const boardView = document.getElementById("boardView");
    if (boardView && boardView.style.display !== "none" && window.kanban) {
      window.kanban.loadBoard();
      window.kanban.loadSummary();
    }

    // Toast notifications
    if (type === "ticket_created") {
      showToast("info", "New Ticket", "Ticket created successfully");
    } else if (type === "ticket_updated") {
      showToast("success", "Ticket Updated", "Status changed");
    }
  }
}
