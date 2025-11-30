// static/js/state.js
export const state = {
  conversations: [],
  agents: [],
  activeTickets: {}, // Map: account_id_chat_id -> ticket object
  allTickets: [],
  currentConversation: null,
  messages: {}, // Map: conversation_id -> [messages]
  currentTab: "chats",
};

export function setState(key, value) {
  state[key] = value;
}
