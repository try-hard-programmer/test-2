# Quick Start Guide

## 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. Get Telegram API Credentials

1. Visit https://my.telegram.org
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create an application
5. Save your `api_id` and `api_hash`

## 3. Setup Supabase

1. Create account at https://supabase.com
2. Create a new project
3. Go to SQL Editor
4. Run the SQL from `supabase_migration.sql`
5. Get your project URL and anon key from Settings > API

## 4. Configure Environment

```bash
cp .env.example .env
```

Generate encryption key:
```bash
uv run python generate_key.py
```

Edit `.env` and fill in:
- SUPABASE_URL
- SUPABASE_KEY
- ENCRYPTION_KEY (from generate_key.py output)

## 5. Install Dependencies

```bash
uv sync
```

## 6. Start the Application

```bash
./start.sh
```

Or manually:
```bash
uv run python main.py
```

## 7. Open Dashboard

Visit http://localhost:8000 in your browser

## 8. Add Your First Account

1. Click "Add Telegram Account"
2. Enter your account details:
   - Label: "My Account"
   - API ID: (from step 2)
   - API Hash: (from step 2)
   - Phone: +1234567890 (with country code)
3. Click "Add Account"
4. Enter the verification code from Telegram
5. Click "Verify"

## Done!

You should now see your conversations appear as messages arrive.

## Troubleshooting

**"Missing required environment variables"**
- Make sure you've filled in all values in `.env`

**"Failed to connect to Telegram"**
- Check your API credentials
- Verify phone number format includes country code

**"Connection refused to Supabase"**
- Verify your Supabase URL and key
- Make sure you ran the migration SQL

**Need help?**
- Check the full README.md
- Review application logs in the console
- Verify all configuration in .env
