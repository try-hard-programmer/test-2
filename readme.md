📌 **PRD — Telegram Chat Integration (Phase 1 Only)**

✅ **Objective**

Build a system where admins can receive and reply to Telegram messages inside a local web dashboard, supporting multiple **real Telegram accounts (MTProto)** with encrypted sessions stored in Supabase and messages stored locally in SQLite.

---

🧑‍💼 **User Story**

As an admin,  
I want to receive chat messages from Telegram in one dashboard  
so that I can manage and reply to users without using the Telegram app.

---

✅ **Acceptance Criteria**

### Message Handling

- Incoming Telegram messages appear in the dashboard **in real-time**
- Each message is labeled by:
  - Telegram account (session owner)
  - Sender (chat user)
- Messages are stored in **SQLite**
- Message metadata tracked:
  - received
  - sent
  - failed
- No duplicates (based on Telegram message ID)

### Reply Handling

- Admin can reply directly from dashboard
- Reply is sent using the **correct Telegram account**
- Outgoing messages appear instantly
- Delivery status updated on success/failure

### Multi-Account Support

- Admin can add multiple **Telegram accounts**
- Supabase stores:
  - api_id
  - api_hash
  - encrypted session string
- Backend auto-reconnects all accounts at startup
- Messages routed based on account ID

### Security

- Local dashboard only (no public access)
- No authentication required (Phase 1)
- Supabase stores **encrypted** session strings
- No plaintext OTP stored anywhere

---

🏗️ **System Architecture (Telegram Only)**

### Flow

Telegram User  
→ Telethon MTProto Client  
→ FastAPI backend  
→ Save to SQLite  
→ WebSocket push to dashboard  
→ Admin reply  
→ Backend → Telethon → Telegram User

### Components

| Component       | Responsibility                                                 |
| --------------- | -------------------------------------------------------------- |
| FastAPI Backend | Manages Telethon clients, messaging, WebSockets                |
| Supabase        | Stores Telegram account credentials + session strings          |
| SQLite          | Stores conversations and messages                              |
| Web Dashboard   | Display chats, send replies, manage multiple Telegram accounts |
| Telethon        | Real account messaging transport                               |

---

🗄️ **Supabase Data Model (Phase 1)**

**telegram_accounts**

| field          | type             | notes                 |
| -------------- | ---------------- | --------------------- |
| id             | uuid             | PK                    |
| account_label  | text             | display name          |
| api_id         | integer          | required              |
| api_hash       | text             | required              |
| session_string | text (encrypted) | generated after login |
| is_active      | boolean          | toggle on/off         |
| created_at     | timestamp        | —                     |

(No messages stored in Supabase)

---

🗄️ **SQLite Local Data Model**

**conversations**

| field               | type       | notes                  |
| ------------------- | ---------- | ---------------------- |
| id                  | integer PK | —                      |
| telegram_account_id | uuid       | FK → telegram_accounts |
| chat_id             | text       | Telegram peer ID       |
| last_message_at     | timestamp  | updated on new message |

**messages**

| field               | type                 | notes               |
| ------------------- | -------------------- | ------------------- |
| id                  | integer PK           | —                   |
| telegram_account_id | uuid                 | FK                  |
| chat_id             | text                 | conversation link   |
| message_id          | text                 | Telegram message ID |
| direction           | incoming/outgoing    | —                   |
| text                | text                 | message body        |
| timestamp           | timestamp            | —                   |
| status              | received/sent/failed | —                   |

---

🔌 **Backend Requirements**

### WebSocket Events

- message_received
- message_sent
- account_status

### REST Endpoints

- POST /accounts/add  
   body: api_id, api_hash, label  
   → generates session via Telethon login
- GET /conversations
- GET /conversations/:id/messages
- POST /conversations/:id/reply  
   body: text → routed to correct account

### Runtime Behavior

- One Telethon client **per active account**
- Auto-reconnect if disconnected
- Load sessions from Supabase on startup
- Write messages to SQLite immediately

---

📍 **Frontend Requirements (Dashboard)**

Features:

- Real-time message stream via WebSocket
- Conversation list grouped by Telegram account
- Reply input per conversation
- Shows:
  - incoming/outgoing
  - timestamps
  - delivery status

Constraints:

- Plain HTML + vanilla JS
- No routing
- Served from [http://localhost](http://localhost):<port>
- No authentication

---

🚀 **Non-Functional Requirements**

- Real-time latency < 1s
- System runs entirely offline after sessions synced
- Survives backend restart without losing session
- Supports at least 3 accounts simultaneously
- Safe write handling if SQLite locked

---

⛔ **Out of Scope (Phase 1)**

- WhatsApp
- Email integration
- Bot accounts
- AI auto-reply
- Media (images, voice, files)
- Cloud hosting
- Admin roles/auth
- Push notifications

---

✅ **Phase 1 Completion Definition**

Phase 1 is complete when:

- Multiple Telegram accounts can be added
- Session strings stored safely in Supabase
- Messages stored in SQLite
- Dashboard displays chats in real-time
- Admin can reply using correct account
- Backend restarts without losing sessions
- Entire system runs on localhost only

---

**FINISH PRD PHASE 1**
