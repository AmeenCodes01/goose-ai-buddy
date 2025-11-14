import datetime
import os
import sys

# Add the parent directory of goose_integration.py to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), 'python-service'))

from goose_integration import GooseClient

def get_or_create_daily_session():
    today = datetime.date.today()
    today_session_name = f"daily_session_{today.strftime('%Y-%m-%d')}"
    
    client = GooseClient()
    name=""
    session_id = None
    # we'll go with name fr now.
    try:
        try:
            with open("today_session.txt", "r") as f:
                name = f.readline().strip()
        except FileNotFoundError:
            name = ""
            with open("today_session.txt", "w") as f:
                pass  # Just create the file

        print(name, "name")

        if name != today_session_name:
            result = client.start_session(today_session_name)
            print("created new sesh fr today", result)

            with open("today_session.txt", "w") as f:
                f.write(today_session_name)

        client.today_session_name = today_session_name

    # Optional: session_id logic
    # session_id = None
    # sessions = client.list_sessions(format_type="json")
    # for session_data in sessions:
    #     if session_data.get("name") == today_session_name:
    #         session_id = session_data.get("id") or session_data.get("session_id")
    #         if session_id:
    #             print(f"Reusing existing session for {today_session_name}: {session_id}")
    #             break

    # if not session_id:
    #     print(f"Creating new session for {today_session_name}...")
    #     client.start_session(name=today_session_name, extensions=["developer"])
    #     sessions = client.list_sessions(format_type="json")
    #     for session_data in sessions:
    #         if session_data.get("name") == today_session_name:
    #             session_id = session_data.get("id") or session_data.get("session_id")
    #             if session_id:
    #                 print(f"Created new session for {today_session_name}: {session_id}")
    #                 break
    #     if not session_id:
    #         print(f"Warning: Could not retrieve session ID for new session {today_session_name}.")
    #         session_id = today_session_name

    except Exception as e:
        print(f"Error managing Goose session: {e}")
        session_id = None

    return today_session_name

if __name__ == '__main__':
    current_session_id = get_or_create_daily_session()
    if current_session_id:
        print(f"Active Goose session ID for today: {current_session_id}")
    else:
        print("Failed to establish an active Goose session for today.")
