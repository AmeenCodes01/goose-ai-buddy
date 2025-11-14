# documentation of how I used subagents 
2 parallel subagents for create voice functionality & browser extension limit sending URLs/

Subagent used for creating the Goose (python SDK-ish) class 

Subagent for distraction tracker 

subagent to fix logging_distraction & goose intervening.

create a subagent that will always be listening to user input

created a subagent which is now testing & fixing the whole conversation with goose aspect. all building blocks are in place.


Create two subagents that run in parallel. Keep the implementation minimal and simple.

Subagent 1:
- Every day, check if a Goose session exists for today in a txt file.
- If not, create a new Goose session and save the session ID with today’s date.
- If yes, reuse the existing session.
- Reference: goose_interaction.py

Subagent 2:
- Improve the voice-based accountability loop.
- Only ask the user to repeat if they actually said something.
- Extend the listening timeout so it doesn’t cut off mid-sentence.
- Reference: start_accountability_conversation and voice_interaction.py

I’ll handle testing and feedback. Just write the code.


before executing, tell on how you plan to do this both
    (it executed in main chat,smh)

Create Agent (Wi-Fi Scan): Run locally on the user's laptop. Scan nearby Wi-Fi SSIDs for keywords like 'Train', 'Bus', or 'Station'. If a match is found, call the tool goose with the instruction: 'user heading to train station'." 
    (this was through gemini CLI sorry, I had hit rate limit in goose & gemini CLI wasn't being configured as provider ://)



# lock in MVP 
1- Browser extension with goose intervening 
2- Scheduler 
3- Chat anytime (trigger goose by a word).
3- Train station trigger
4- Vision - look away detection & speak to user. - triggers/signs for extension activation ? 

Assume I have 2 days. 






[] Make goose intervene for browser extension
[] User chat loop

[] Create Scheduler MCP
[] schedules and makes goose speak.
[X] Have "word trigger" always running. 

[] get user location from browser 
[] scan wifi's if "station" in them
[] Call goose to run

#Sessions
[] Create per day session 
[] Summarise at end of day, whole chat into a doc

#Reminders
[] Ask 3 times a day 

#Goose
[] prompt tuning