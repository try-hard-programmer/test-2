# 📘 User Manual: Telegram Support Dashboard

Welcome to your **Telegram Support Dashboard**. This system allows you to manage multiple Telegram accounts, receive messages in real-time, and manage support tickets—all from one place.

## 🚀 How to Run

### 1. Start the Application

Open your terminal in the project folder and run:

```
./start.sh
```

If successful, you will see:

> Starting server on http://127.0.0.1:8000

### 2. Access the Dashboard

Open your web browser (Chrome recommended) and visit: 👉 **http://localhost:8000**

## ⚙️ Setup: Connecting Accounts

1. Click the **+ Add Account** button in the sidebar.
2. Fill in the form:

   - **Label:** Any name (e.g., "Support Agent 1").
   - **API ID & Hash:** Get these from [my.telegram.org](https://my.telegram.org "null").
   - **Phone:** Your number with country code (e.g., `+628123456789`).

3. Click **Request Code**.
4. Check your Telegram app for a login code from Telegram.
5. Enter the code and click **Verify**.

_Note: The session is encrypted and stored securely in your Supabase cloud database._

## 🎫 Ticket System Features

This dashboard includes a **Hybrid Ticket System**. Tickets are stored in the cloud (Supabase), while chat logs remain local.

### 1. Auto-Ticket (Self-Service for Users)

Your customers can create tickets themselves directly from Telegram!

**How it works:**

1. **User types:** `/ticket`
2. **Bot replies:** "Please reply with format..."
3. **User replies:**

   ```
   Subject: WiFi Error
   Priority: High
   Problem: My internet is red.
   ```

4. **Result:**

   - Bot confirms "✅ Ticket Created".
   - **Your Dashboard:** The sidebar instantly updates to show the new ticket details.

### 2. Manual Ticket Creation

You can create tickets for users who forget to use the command.

1. Open a chat.
2. Look at the **Right Sidebar**.
3. Click **+ Create Ticket**.
4. Fill in the Subject and Priority.
5. The ticket is now active and linked to this chat.

### 3. Closing Tickets

Once an issue is resolved, you can close it in two ways:

- **Via Dashboard:** Click the **Mark Resolved** button in the right sidebar.
- **Via Telegram (User):** The user can simply type `/close` to close their own ticket.

## 🛠️ Troubleshooting

**"WebSocket Disconnected"**

- Check if your terminal running `./start.sh` is still open.
- Refresh the page.

**"Database Locked"**

- This means two processes are trying to write to the local database file at once.
- **Fix:** Restart the backend (`Ctrl+C` then `./start.sh`).

**"Tickets not loading"**

- Check your internet connection. Tickets are fetched from Supabase (Cloud).
