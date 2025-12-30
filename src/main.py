from .data_loader import KnowledgeBase
from .bot import AuenBot

def run():
    kb = KnowledgeBase.load()
    bot = AuenBot(kb)

    print("Auen_Bot (MVP) – tippe 'exit' zum Beenden.\n")
    while True:
        user = input("Du: ").strip()
        if user.lower() in ("exit", "quit", "q"):
            break
        reply = bot.answer(user)
        print(f"\nBot: {reply}\n")

if __name__ == "__main__":
    run()
