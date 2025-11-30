# 📚 API Documentation

This document details the REST API endpoints and WebSocket events for the Telegram Support Dashboard.

## Base URL

`http://127.0.0.1:8000/api`

## 🔐 Accounts

### Add Telegram Account

Initiate login or verify code.

- **Endpoint:** `POST /accounts/add`
- **Description:** Starts the login process. If a code is required, it returns `status: "code_sent"`. If the session is already authorized, it saves the account.

**Request Body:**

```
{
  "label": "Support Agent 1",
  "api_id": 123456,
  "api_hash": "abcdef123456...",
  "phone": "+1234567890"
}
```

**Response (Code Sent):**

```
{
  "status": "code_sent",
  "message": "Verification code sent to your phone",
  "phone": "+1234567890",
  "phone_code_hash": "..."
}
```

**Response (Success):**

```
{
  "status": "success",
  "account": {
    "id": "uuid...",
    "account_label": "Support Agent 1",
    "is_active": true
  }
}
```

### Verify Account

Complete the login with the code received on Telegram.

- **Endpoint:** `POST /accounts/verify`

**Request Body:**

```
{
  "label": "Support Agent 1",
  "api_id": 123456,
  "api_hash": "abcdef...",
  "phone": "+1234567890",
  "code": "12345"
}
```

### Get All Accounts

List all connected Telegram accounts.

- **Endpoint:** `GET /accounts`

## 💬 Conversations & Messages

### Get Conversations

List all active chats sorted by the latest message.

- **Endpoint:** `GET /conversations`

### Get Messages

Retrieve chat history for a specific conversation.

- **Endpoint:** `GET /conversations/{id}/messages`
- **Query Params:** `limit` (default: 100)

### Send Reply

Send a message to a Telegram user.

- **Endpoint:** `POST /conversations/{id}/reply`

**Request Body:**

```
{
  "text": "Hello! How can I help you?"
}
```

## 🎫 Tickets (Phase 2)

### List Tickets

Get all support tickets stored in Supabase.

- **Endpoint:** `GET /tickets`
- **Query Params:** `status` (optional: `open`, `closed`, `resolved`)

### Create Manual Ticket

Manually open a ticket for a conversation.

- **Endpoint:** `POST /tickets/create`

**Request Body:**

```
{
  "account_id": "uuid-of-account",
  "chat_id": "123456789",
  "priority": "high",
  "subject": "Manual Ticket",
  "description": "User called via phone."
}
```

### Update Ticket

Change status or priority.

- **Endpoint:** `PATCH /tickets/{id}`

**Request Body:**

```
{
  "status": "resolved",
  "priority": "low"
}
```

### Delete Ticket

Permanently remove a ticket.

- **Endpoint:** `DELETE /tickets/{id}`

## 🔌 WebSocket Events

Connect to: `ws://127.0.0.1:8000/api/ws`

### Incoming Events (Server -> Client)

**1. Message Received** Sent when a new message arrives from Telegram.

```
{
  "type": "message_received",
  "data": {
    "account_id": "...",
    "chat_id": "...",
    "text": "Hello",
    "timestamp": "2024-01-01T12:00:00"
  }
}
```

**2. Ticket Created** Sent when a ticket is created (manually or via `/ticket`).

```
{
  "type": "ticket_created",
  "data": {
    "id": "uuid...",
    "status": "open",
    "subject": "Internet Down"
  }
}
```

**3. Ticket Updated** Sent when a ticket status changes (e.g., closed via `/close`).

```
{
  "type": "ticket_updated",
  "data": {
    "id": "uuid...",
    "status": "closed"
  }
}
```
