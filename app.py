import json
import os
import sqlite3
import sys
import time
import urllib.request

# =====================================================================
# LILY AI ASSISTANT - PERMANENT FACTS VERSION
# =====================================================================
GROQ_API_KEY = "Paste You AI Api key Create from Groq Cloud"  # <-- Paste your Groq API key here
MODEL_ID = "Paste the Name of Your AI Model which you found from Groq Cloud"
DB_FILE = "lily_core_memory.db"

# Resolve API Key
api_key = (
    GROQ_API_KEY
    if GROQ_API_KEY != "YOUR_GROQ_API_KEY_HERE"
    else os.environ.get("GROQ_API_KEY")
)

if not api_key or api_key == "YOUR_GROQ_API_KEY_HERE":
  print(
      "❌ Error: Please paste your Groq API key into the GROQ_API_KEY variable"
      " at the top of the script!"
  )
  sys.exit(1)


def init_database():
  """Initializes the lightweight SQLite core memory database."""
  with sqlite3.connect(DB_FILE) as conn:
    conn.execute(
        """
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                core_summary TEXT
            )
        """
    )
    conn.execute(
        """
            INSERT OR IGNORE INTO memory (id, core_summary) 
            VALUES (1, ?)
        """,
        (
            (
                "Just starting our journey together, getting to know each"
                " other."
            ),
        ),
    )


def load_memory():
  """Loads the dynamic conversation summary from disk."""
  with sqlite3.connect(DB_FILE) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT core_summary FROM memory WHERE id = 1")
    return cursor.fetchone()[0]


def save_memory(new_summary):
  """Permanently updates the dynamic conversation summary."""
  with sqlite3.connect(DB_FILE) as conn:
    conn.execute(
        "UPDATE memory SET core_summary = ? WHERE id = 1", (new_summary,)
    )


def call_groq_api(prompt_text):
  """Sends request to Groq using built-in urllib with headers and retry logic."""
  url = "https://api.groq.com/openai/v1/chat/completions"
  headers = {
      "Authorization": f"Bearer {api_key}",
      "Content-Type": "application/json",
      "User-Agent": "Mozilla/5.0 (Compatible; LilyAI/1.0)",
  }
  payload = {
      "model": MODEL_ID,
      "messages": [{"role": "user", "content": prompt_text}],
      "temperature": 0.7,
  }

  data = json.dumps(payload).encode("utf-8")
  max_retries = 3

  for attempt in range(max_retries):
    try:
      req = urllib.request.Request(url, data=data, headers=headers, method="POST")
      with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
      error_body = e.read().decode("utf-8")
      print(f"\n⚠️ API HTTP Error {e.code}: {error_body}")
      if attempt < max_retries - 1:
        wait_time = (attempt + 1) * 3
        print(f"⏳ Retrying in {wait_time}s...")
        time.sleep(wait_time)
      else:
        raise e
    except Exception as e:
      if attempt < max_retries - 1:
        wait_time = (attempt + 1) * 3
        print(f"\n⏳ Connection hiccup. Retrying in {wait_time}s...")
        time.sleep(wait_time)
      else:
        raise e


def main():
  init_database()
  print("==================================================")
  print("🌸 Lily AI Assistant Initialized (Fact-Lock Mode) 🌸")
  print("Type 'exit' or 'quit' to end the session.")
  print("==================================================\n")

  while True:
    try:
      user_input = input("You: ").strip()
      if not user_input:
        continue
      if user_input.lower() in ["exit", "quit"]:
        print("\nLily: Goodbye! Take care of yourself! 🌸")
        break

      current_memory = load_memory()

      # ===================================================================
      # 🛡️ PERMANENT FACTS ARE HARDCODED RIGHT HERE SO SHE NEVER FORGETS
      # ===================================================================
      prompt = f"""
[ABSOLUTE PERMANENT FACTS - NEVER FORGET OR IGNORE THESE]
- You are a Girl

[CURRENT DYNAMIC CONVERSATION CONTEXT]
{current_memory}

[INSTRUCTIONS]
1. Speak directly like a human partner—no separate chat logs, just natural conversation.
2. If the user asks about their name, profession, or projects, always use the "ABSOLUTE PERMANENT FACTS" section above to answer instantly and accurately.
3. Respond to the user's latest message below. 

User's latest message: "{user_input}"

Format your response strictly using this structure:
REPLY: [Your direct human-like reply to the user]
UPDATED_MEMORY: [A concise paragraph capturing recent conversational details, keeping it compact]
"""

      raw_text = call_groq_api(prompt)

      if "REPLY:" in raw_text and "UPDATED_MEMORY:" in raw_text:
        parts = raw_text.split("UPDATED_MEMORY:")
        reply = parts[0].replace("REPLY:", "").strip()
        new_memory = parts[1].strip()
        save_memory(new_memory)
      else:
        reply = raw_text

      print(f"\nLily: {reply}\n")

    except KeyboardInterrupt:
      print("\n\nLily: Goodbye! 🌸")
      break
    except Exception as e:
      print(f"\n❌ Error encountered: {e}\n")


if __name__ == "__main__":
  main()
