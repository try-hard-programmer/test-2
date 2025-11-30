// ui.js - FULL REPLACEMENT
import { state } from "./state.js";
import { formatTime, escapeHtml, showToast } from "./utils.js";
import { api } from "./api.js";

export function renderConversations() {
  const container = document.getElementById("chatsTab");
  if (state.conversations.length === 0) {
    container.innerHTML =
      '<div class="p-8 text-center text-gray-400">No conversations yet</div>';
    return;
  }

  container.innerHTML = state.conversations
    .map((conv) => {
      const key = `${conv.telegram_account_id}_${conv.chat_id}`;
      const hasTicket = state.activeTickets[key];
      const isActive =
        state.currentConversation && state.currentConversation.id === conv.id;

      return `
        <div class="p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors ${
          isActive ? "bg-blue-50 border-l-4 border-l-blue-500" : ""
        } group relative" data-id="${conv.id}">
            <div class="flex justify-between items-start mb-1">
                <div class="flex flex-col min-w-0 flex-1" onclick="window.app.selectConversation(${
                  conv.id
                })">
                    <div class="text-xs font-semibold text-blue-600 mb-0.5 flex items-center gap-1">
                       ${
                         hasTicket
                           ? '<span class="w-2 h-2 rounded-full bg-red-500 inline-block"></span>'
                           : ""
                       }
                       Account: ${conv.telegram_account_id.substring(0, 8)}...
                    </div>
                    <div class="text-sm font-medium text-gray-900 truncate">
                        ${escapeHtml(conv.chat_name) || "Chat: " + conv.chat_id}
                    </div>
                </div>
                <button 
                  class="delete-conv-btn opacity-0 group-hover:opacity-100 p-1.5 text-red-500 hover:bg-red-50 rounded transition-all z-10"
                  data-id="${conv.id}"
                  title="Delete"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                  </svg>
                </button>
            </div>
            <div class="text-xs text-gray-400 text-right">${formatTime(
              conv.last_message_at
            )}</div>
        </div>
    `;
    })
    .join("");

  // Add delete event listener
  container.querySelectorAll(".delete-conv-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      window.app.deleteConversation(parseInt(btn.dataset.id));
    });
  });
}

export function renderMessages(convId) {
  const container = document.getElementById("messagesContainer");
  const msgs = state.messages[convId] || [];

  container.innerHTML = msgs
    .map(
      (msg) => `
        <div class="flex mb-4 gap-2 ${
          msg.direction === "outgoing" ? "justify-end" : "justify-start"
        }">
            <div class="max-w-[70%] px-4 py-3 rounded-2xl text-sm shadow-sm ${
              msg.direction === "outgoing"
                ? "bg-blue-600 text-white rounded-br-none"
                : "bg-white border border-gray-200 rounded-bl-none"
            }">
                <div class="leading-relaxed break-words">${escapeHtml(
                  msg.text
                )}</div>
                <div class="text-[10px] mt-1 opacity-70 flex items-center gap-1 ${
                  msg.direction === "outgoing"
                    ? "justify-end text-blue-100"
                    : "text-gray-400"
                }">
                    ${formatTime(msg.timestamp)}
                    ${
                      msg.direction === "outgoing"
                        ? `<span>${msg.status === "sent" ? "✓" : "•"}</span>`
                        : ""
                    }
                </div>
            </div>
        </div>
    `
    )
    .join("");

  container.scrollTop = container.scrollHeight;
}

export function renderTicketsList() {
  const container = document.getElementById("ticketsTab");
  const visibleTickets = state.allTickets.filter((t) =>
    ["open", "in_progress"].includes(t.status)
  );

  if (visibleTickets.length === 0) {
    container.innerHTML =
      '<div class="p-8 text-center text-gray-400">No open tickets</div>';
    return;
  }

  container.innerHTML = visibleTickets
    .map((ticket) => {
      const pColor =
        ticket.priority === "high" || ticket.priority === "urgent"
          ? "bg-red-500"
          : "bg-green-500";
      return `
        <div class="p-4 border-b border-gray-100 cursor-pointer bg-white hover:bg-gray-50 transition-colors ticket-item" data-account="${
          ticket.account_id
        }" data-chat="${ticket.chat_id}">
            <div class="flex justify-between items-center mb-1">
                <span class="text-xs font-bold text-gray-400">#${
                  ticket.id.split("-")[0]
                }</span>
                <span class="text-[10px] px-2 py-0.5 rounded bg-blue-50 text-blue-600 font-bold uppercase">${
                  ticket.status
                }</span>
            </div>
            <div class="text-sm font-semibold text-gray-800 mb-1 truncate">${escapeHtml(
              ticket.subject || "No Subject"
            )}</div>
            <div class="flex justify-between items-center text-xs text-gray-500">
                <div class="flex items-center gap-1">
                    <span class="w-1.5 h-1.5 rounded-full ${pColor}"></span>
                    ${ticket.priority}
                </div>
                <span>${formatTime(ticket.created_at)}</span>
            </div>
        </div>
    `;
    })
    .join("");

  container.querySelectorAll(".ticket-item").forEach((el) => {
    el.addEventListener("click", () =>
      window.app.selectTicketFromList(el.dataset.account, el.dataset.chat)
    );
  });
}

export function renderAgents() {
  const container = document.getElementById("agentsTab");

  if (!state.agents || state.agents.length === 0) {
    container.innerHTML = `<div class="flex flex-col items-center justify-center h-64 text-gray-400">
                <svg class="w-12 h-12 mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
                <p>No accounts connected</p>
            </div>`;
    return;
  }

  container.innerHTML = state.agents
    .map(
      (agent) => `
        <div class="bg-white border border-gray-200 rounded-lg p-4 mb-4 shadow-sm hover:shadow-md transition-all">
            <div class="flex justify-between items-start mb-3">
                <div>
                    <h3 class="font-bold text-gray-800 text-sm flex items-center gap-2">
                        ${escapeHtml(agent.account_label)}
                        ${
                          agent.connected
                            ? '<span class="w-2 h-2 bg-green-500 rounded-full"></span>'
                            : '<span class="w-2 h-2 bg-red-500 rounded-full"></span>'
                        }
                    </h3>
                    <p class="text-xs text-gray-500 mt-1">
                        ${agent.connected ? "Connected" : "Disconnected"}
                        ${agent.is_active ? "" : " • Paused"}
                    </p>
                </div>
                
                <!-- Settings Button -->
                <button 
                    onclick="window.app.openAgentAttributesModal('${agent.id}')"
                    class="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Agent Settings"
                >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                </button>
            </div>
            
            <div class="flex gap-2 mt-3">
                <button onclick="toggleAgent('${agent.id}', ${
        agent.is_active
      })" class="flex-1 py-1.5 rounded text-xs font-medium border ${
        agent.is_active
          ? "border-yellow-200 text-yellow-700 hover:bg-yellow-50"
          : "border-green-200 text-green-700 hover:bg-green-50"
      }">
                    ${agent.is_active ? "Pause" : "Activate"}
                </button>
                <button onclick="deleteAgent('${agent.id}', '${escapeHtml(
        agent.account_label
      )}')" class="flex-1 py-1.5 rounded text-xs font-medium border border-red-200 text-red-600 hover:bg-red-50 transition-colors text-center">
                    Delete
                </button>
            </div>
        </div>
    `
    )
    .join("");
}

// ui.js - FIX updateTicketSidebar - GANTI FUNCTION INI AJA
export function updateTicketSidebar() {
  console.log("=== updateTicketSidebar called ===");

  const noTicket = document.getElementById("noTicketState");
  const activeTicket = document.getElementById("activeTicketState");

  if (!noTicket || !activeTicket) {
    console.error("Ticket sidebar elements not found");
    return;
  }

  if (!state.currentConversation) {
    console.log("No current conversation");
    noTicket.classList.remove("hidden");
    activeTicket.classList.add("hidden");
    return;
  }

  const key = `${state.currentConversation.telegram_account_id}_${state.currentConversation.chat_id}`;
  const ticket = state.activeTickets[key];

  console.log("Looking for ticket with key:", key);
  console.log("Found ticket:", ticket);

  if (ticket) {
    noTicket.classList.add("hidden");
    activeTicket.classList.remove("hidden");

    const shortId = ticket.id.split("-")[0];

    const displayId = document.getElementById("ticketDisplayId");
    const subject = document.getElementById("ticketSubject");
    const priority = document.getElementById("ticketPriority");
    const source = document.getElementById("ticketSource");
    const description = document.getElementById("ticketDescription");
    const statusBadge = document.getElementById("ticketStatusBadge");
    const statusSelect = document.getElementById("ticketStatusSelect");

    if (displayId) displayId.textContent = `#${shortId}`;
    if (subject) subject.textContent = ticket.subject || "No Subject";
    if (priority) priority.textContent = ticket.priority || "medium";
    if (source) source.textContent = ticket.source || "manual";
    if (description) description.textContent = ticket.description || "";
    if (statusBadge) statusBadge.textContent = ticket.status.toUpperCase();
    if (statusSelect) {
      statusSelect.value = ticket.status;
      console.log("Setting statusSelect to:", ticket.status);

      // SET TICKET TO KANBAN
      if (window.kanban) {
        window.kanban.currentTicketInSidebar = ticket;
        console.log(
          "✅ Ticket set to kanban.currentTicketInSidebar:",
          ticket.id
        );
      } else {
        console.error("❌ window.kanban not found!");
      }
    }
  } else {
    console.log("No ticket found for this chat");
    noTicket.classList.remove("hidden");
    activeTicket.classList.add("hidden");
    if (window.kanban) window.kanban.currentTicketInSidebar = null;
  }
}
