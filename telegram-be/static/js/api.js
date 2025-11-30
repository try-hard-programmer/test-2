// static/js/api.js
const API_BASE = "/api";

async function request(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Request failed");
    return data;
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
}

export const api = {
  // Conversations
  getConversations: () => request("/conversations"),
  getMessages: (convId) => request(`/conversations/${convId}/messages`),
  sendReply: (convId, text) =>
    request(`/conversations/${convId}/reply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }),

  // Tickets
  getTickets: () => request("/tickets"),
  createTicket: (payload) =>
    request("/tickets/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  updateTicket: (ticketId, updates) =>
    request(`/tickets/${ticketId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    }),
  deleteTicket: (ticketId) =>
    request(`/tickets/${ticketId}`, {
      method: "DELETE",
    }),

  // Kanban Board (NEW)
  getTicketsByStatus: (status) => request(`/tickets/by-status/${status}`),
  getTicketSummary: (startDate, endDate, agentId) => {
    let url = "/tickets/summary";
    const params = new URLSearchParams();
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (agentId) params.append("agent_id", agentId);
    const query = params.toString();
    return request(query ? `${url}?${query}` : url);
  },

  // Accounts
  getAccounts: () => request("/accounts"),
  addAccount: (payload) =>
    request("/accounts/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  verifyAccount: (payload) =>
    request("/accounts/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  deleteAccount: (accountId) =>
    request(`/accounts/${accountId}`, {
      method: "DELETE",
    }),
  toggleAccount: (accountId, isActive) =>
    request(`/accounts/${accountId}/toggle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_active: isActive }),
    }),
};
