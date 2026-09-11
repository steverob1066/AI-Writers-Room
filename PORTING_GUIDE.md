# Adding tools beyond the current six

The app currently ships six tools, all built on one pattern: load .fdx -> one whole-script
AI call -> parse JSON -> render + xlsx report. That covers everything except two of your
original eight desktop tabs, which use different patterns.

## Voice Editor (not included)

Structurally closest to Description Improver's loop-based approach, but writes one sheet
per character into a report that *accumulates across runs* rather than starting fresh
each time. That accumulation is the tricky part to port: on the desktop it opens the
existing local xlsx file and appends a sheet. On the web, there's no "local file that
persists between visits" in the same way.

Two reasonable approaches if you want to add it later:
- Simplest: generate a fresh report each run (drop the accumulation), and let the writer
  keep their own historical reports downloaded locally, comparing manually
- Truer to the original: store each character's data in `st.session_state` for the
  browser session, and let the user re-run other characters before downloading one
  combined xlsx at the end (accumulation within a session, not across visits)

## Description Improver (removed from this build)

This was in the very first draft of the web app and worked (per-line extract, AI-improve,
replace-in-fdx, download updated .fdx). It's no longer wired into `streamlit_app.py` at
your request, but the pattern is straightforward to bring back if needed: loop over
`fdx_utils.extract_action_description_groups()`, call `ai_client.send_prompt()` once per
line, then either export a comparison xlsx or call `fdx_utils.replace_paragraph_groups()`
to write an updated .fdx. Ask if you want this re-added as a seventh tool.

## A note on prompts

Each tool's prompt is shown in an editable box that starts from the built-in default each
time a user opens it, but nothing gets saved back to disk. That's the right default for a
shared web app -- one friend editing the prompt shouldn't change it for everyone else,
since (unlike the desktop app's local settings file) this is one shared server. If you
want per-user saved prompts later, that needs real per-user accounts, not just a shared
password.
