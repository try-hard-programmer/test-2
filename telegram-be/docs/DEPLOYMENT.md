# Deployment Checklist

## Pre-Deployment

### 1. System Requirements
- [ ] Python 3.11+ installed
- [ ] uv package manager installed
- [ ] Internet connection available
- [ ] Supabase account created
- [ ] Telegram API credentials obtained

### 2. Supabase Setup
- [ ] Created Supabase project
- [ ] Ran migration SQL (`supabase_migration.sql`)
- [ ] Copied Supabase URL
- [ ] Copied Supabase anon key
- [ ] Verified telegram_accounts table exists

### 3. Telegram API Setup
- [ ] Visited https://my.telegram.org
- [ ] Created application
- [ ] Saved api_id
- [ ] Saved api_hash

### 4. Project Configuration
- [ ] Cloned/copied project files
- [ ] Created `.env` from `.env.example`
- [ ] Generated encryption key (`make key` or `uv run python generate_key.py`)
- [ ] Filled in all `.env` variables:
  - [ ] SUPABASE_URL
  - [ ] SUPABASE_KEY
  - [ ] ENCRYPTION_KEY
  - [ ] HOST (default: 127.0.0.1)
  - [ ] PORT (default: 8000)
  - [ ] SQLITE_DB_PATH (default: ./data/messages.db)

### 5. Dependencies
- [ ] Ran `uv sync` or `make install`
- [ ] All packages installed successfully

### 6. Testing
- [ ] Ran `uv run python test_config.py` or `make test`
- [ ] All tests passed

## Deployment

### 7. First Run
- [ ] Started application (`./start.sh` or `make run`)
- [ ] No errors in console
- [ ] Server running on http://127.0.0.1:8000
- [ ] Dashboard accessible in browser

### 8. Add First Account
- [ ] Opened dashboard in browser
- [ ] Clicked "Add Telegram Account"
- [ ] Entered account details
- [ ] Received verification code
- [ ] Verified successfully
- [ ] Account appears as connected

### 9. Test Messaging
- [ ] Sent a test message to the Telegram account (from another account)
- [ ] Message appears in dashboard
- [ ] Conversation listed in sidebar
- [ ] Can open conversation
- [ ] Can send reply
- [ ] Reply delivered successfully

## Post-Deployment

### 10. Verification
- [ ] WebSocket connection stable
- [ ] Real-time updates working
- [ ] Multiple conversations work
- [ ] Message status updates correctly
- [ ] No errors in console

### 11. Backend Restart Test
- [ ] Stopped application (Ctrl+C)
- [ ] Restarted application
- [ ] All accounts reconnected automatically
- [ ] Messages still visible
- [ ] Can send/receive messages

### 12. Optional: Add More Accounts
- [ ] Added second Telegram account
- [ ] Both accounts working simultaneously
- [ ] Messages routed to correct accounts

## Troubleshooting

If any step fails, check:
- [ ] Console logs for error messages
- [ ] `.env` file configuration
- [ ] Supabase connection
- [ ] Network connectivity
- [ ] Python version compatibility

Common issues:
- **"Missing required environment variables"**: Check `.env` file
- **"Failed to connect to Telegram"**: Verify API credentials
- **"Connection refused to Supabase"**: Check URL and key
- **"Module not found"**: Run `uv sync` again
- **"Database locked"**: Ensure only one instance running

## Success Criteria

Phase 1 is successfully deployed when:
- [ ] Multiple Telegram accounts can be added
- [ ] Session strings stored encrypted in Supabase
- [ ] Messages stored in local SQLite
- [ ] Dashboard displays chats in real-time
- [ ] Admin can reply using correct account
- [ ] Backend survives restarts without losing sessions
- [ ] System runs on localhost only
- [ ] No authentication required (as per Phase 1 spec)

## Notes

- Keep `.env` file secure and never commit it
- Keep encryption key safe - losing it means re-authenticating all accounts
- SQLite database can be backed up by copying `data/messages.db`
- Supabase stores only credentials, not messages
- For production, implement proper authentication and security measures

## Next Steps (Phase 2+)

Future enhancements to consider:
- [ ] Add authentication
- [ ] Support media messages
- [ ] WhatsApp integration
- [ ] Email integration
- [ ] Cloud deployment
- [ ] Multi-user support
