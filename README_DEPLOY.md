# Getting AI Writers' Room in front of friends

This folder is a self-contained web version. It reuses `core/` from your desktop app
unchanged -- the .fdx parsing, the AI calls, and the xlsx report writing are exactly the
same code. Only the interface changed, from CustomTkinter windows to a browser page.

Six tools are included, all fully working: **Comedy Analysis**, **Dialogue Craft**,
**Hero's Journey Editor**, **Plot Hole Editor**, **Readability Editor**, and
**Spelling & Grammar**. Each one's prompt, JSON schema and report layout are copied
straight from the matching desktop tab, so results should match what you're used to.
Description Improver and Voice Editor are intentionally left out of this build (see
`PORTING_GUIDE.md` if you want to add either later).

## Step 1 -- Test it locally first

Create an isolated virtual environment for this project first. Your main Python
environment likely has other projects (TTS tools, etc.) with pinned package versions --
installing this app's dependencies straight into it can downgrade packages those other
projects rely on. A venv keeps this app's dependencies completely separate.

```bash
cd ai_writers_room_web
python -m venv venv
```

Activate it -- on Windows:
```bash
venv\Scripts\activate
```
On macOS/Linux:
```bash
source venv/bin/activate
```

Your terminal prompt should now start with `(venv)`. With that showing:

```bash
pip install -r requirements.txt
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Every time you come back to test locally, reactivate the venv first (the activate
command above) before running anything.

Open `.streamlit/secrets.toml` and fill in a real `APP_PASSWORD` and your real
`ANTHROPIC_API_KEY`. Leave the `[gcp_service_account]` section commented out for now --
add it later once the basics work.

```bash
streamlit run streamlit_app.py
```

This opens in your browser at `localhost:8501`. Log in with the password you set, upload
a test .fdx, and confirm both tools work. This step matters -- it's much easier to debug
locally than on a deployed server.

## Step 2 -- Put it on GitHub (private repo)

1. Create a **private** repository on GitHub (Settings on the repo confirm it's private
   -- don't skip this, since the code itself doesn't need to be secret, but there's no
   reason to make it public either).
2. Push this folder to it. `.streamlit/secrets.toml` will NOT be pushed because it's in
   `.gitignore` -- that's intentional, your real API key never goes to GitHub.

```bash
git init
git add .
git commit -m "AI Writers' Room web version"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Step 3 -- Deploy on Streamlit Community Cloud

1. Go to share.streamlit.io and sign in with GitHub.
2. Click "New app", pick your repo, branch `main`, main file path `streamlit_app.py`.
3. Before or after the first deploy, go to the app's Settings -> Secrets, and paste in
   the contents of your local `.streamlit/secrets.toml` (with real values). This is
   where your API key actually lives once deployed -- it's encrypted at rest and never
   visible in your repo.
4. Deploy. You'll get a URL like `https://your-app-name.streamlit.app`.

## Step 4 -- (Optional) Set up run logging to a Google Sheet

Skip this at first if you want to get moving faster -- the app works fine without it,
you just won't have a log of who ran what.

1. In Google Cloud Console, create a project (or use an existing one), enable the
   "Google Sheets API" and "Google Drive API".
2. Create a Service Account, then create a JSON key for it and download it.
3. Create a Google Sheet named "AI Writers Room Logs" (or whatever you set
   `LOG_SHEET_NAME` to), and share it with the service account's email address
   (found in the JSON, field `client_email`) as an Editor.
4. Copy the JSON key's contents into the `[gcp_service_account]` section of your
   Streamlit Cloud secrets, matching the field names shown in
   `.streamlit/secrets.toml.example`.
5. Redeploy (or it'll pick up new secrets automatically). Now every run -- success or
   failure -- gets a row: timestamp, name, filename, tool, status, error message.

When a friend says "it didn't work," open the sheet, find their row, read the actual
error.

## Step 5 -- Share it

Send friends the app URL and the password out of band (text, not the same channel as
anything public). Ask them to enter their real name when logging in -- that's what
makes the log useful.

## A few things worth knowing going in

- **Cold starts**: Streamlit Community Cloud apps "sleep" after inactivity and take
  10-20 seconds to wake up on the first visit of the day. Normal, not a bug.
- **The daily usage cap is per browser session**, not per person -- someone clearing
  cookies resets it. Fine for a friends-only test; revisit if it's ever a real problem.
- **The uploaded script never gets stored** by this app itself beyond the temp file used
  during processing -- only the run metadata gets logged, not the script content. If you
  want to also log a snippet of the output for your own debugging, that's a one-line
  addition to `log_run()`, but tell your friends first since it's their material.
