"""
Interactive Dashboard CLI
Manage your Q&A answers, view jobs, track applications.
Run: python dashboard/cli.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from data.database import (
    init_db, get_jobs, get_stats, get_all_qa,
    save_answer, find_answer, get_today_apply_count
)
from ai_engine.matcher import answer_question


def clear():
    print("\033[2J\033[H", end="")


def print_header(title: str):
    print(f"\n{'═'*54}")
    print(f"  {title}")
    print(f"{'═'*54}")


def menu_main():
    while True:
        clear()
        print("""
╔══════════════════════════════════════════════════╗
║   🎯 JOB HUNTER DASHBOARD                       ║
║   Data Engineer · Sri Krishna Sai Kota          ║
╚══════════════════════════════════════════════════╝

  1. 📋  View recent jobs
  2. ✅  View applications sent
  3. 🧠  Manage Q&A memory
  4. ➕  Add a new Q&A answer
  5. 🔍  Test answer for a question
  6. 📊  View stats
  7. 🚪  Exit
        """)

        choice = input("  Choose option: ").strip()

        if choice == "1":
            menu_view_jobs()
        elif choice == "2":
            menu_view_applications()
        elif choice == "3":
            menu_view_qa()
        elif choice == "4":
            menu_add_qa()
        elif choice == "5":
            menu_test_answer()
        elif choice == "6":
            menu_stats()
        elif choice == "7":
            print("\n👋 Goodbye!\n")
            break
        else:
            input("  ❌ Invalid choice. Press Enter to continue...")


def menu_view_jobs():
    print_header("📋 Recent Jobs Found")
    jobs = get_jobs(limit=20)
    if not jobs:
        input("\n  No jobs in database yet. Press Enter to go back...")
        return

    for i, job in enumerate(jobs, 1):
        score = job.get("match_score", 0)
        emoji = "🟢" if score >= 80 else "🟡" if score >= 65 else "🔴"
        status = job.get("status", "new")
        status_icon = "✅" if status == "applied" else "🆕" if status == "new" else "⏭️"
        print(f"\n  {i:02d}. {emoji} [{score}%] {status_icon} {job['title']}")
        print(f"       🏢 {job['company']}  📍 {job['location']}")
        print(f"       🔗 {job['url'][:60]}...")
        print(f"       💬 {job.get('match_reason','')[:70]}")

    input("\n  Press Enter to go back...")


def menu_view_applications():
    print_header("✅ Applications Sent")
    jobs = get_jobs(status="applied", limit=30)
    if not jobs:
        input("\n  No applications sent yet. Press Enter to go back...")
        return

    print(f"\n  {'#':<4} {'Title':<35} {'Company':<20} {'Score'}")
    print(f"  {'-'*75}")
    for i, job in enumerate(jobs, 1):
        title = job["title"][:33]
        company = job["company"][:18]
        score = job.get("match_score", 0)
        print(f"  {i:<4} {title:<35} {company:<20} {score}%")

    input("\n  Press Enter to go back...")


def menu_view_qa():
    print_header("🧠 Q&A Memory")
    qa_list = get_all_qa()
    if not qa_list:
        input("\n  No Q&A saved yet. Press Enter to go back...")
        return

    print(f"\n  Total answers stored: {len(qa_list)}\n")
    for i, qa in enumerate(qa_list, 1):
        print(f"  {i:02d}. ❓ {qa['question_original'][:65]}")
        print(f"       💬 {qa['your_answer'][:80]}")
        print(f"       📊 Used {qa['used_count']} times\n")

    input("  Press Enter to go back...")


def menu_add_qa():
    print_header("➕ Add Q&A Answer")
    print("\n  This lets you teach the bot how to answer specific questions.")
    print("  Your answer will be stored and reused automatically.\n")

    question = input("  Enter the application question:\n  > ").strip()
    if not question:
        return

    existing = find_answer(question)
    if existing:
        print(f"\n  ℹ️  Existing answer: {existing}")
        overwrite = input("\n  Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            return

    print("\n  Enter your answer (press Enter twice when done):")
    lines = []
    while True:
        line = input("  > ")
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    answer = "\n".join(lines).strip()

    if answer:
        save_answer(question, answer)
        print(f"\n  ✅ Saved! This answer will be used for similar questions.")
    input("\n  Press Enter to go back...")


def menu_test_answer():
    print_header("🔍 Test Answer Generation")
    print("\n  Type a question to see what the bot would answer.\n")

    question = input("  Question: ").strip()
    if not question:
        return

    print("\n  🤔 Generating answer...")
    answer = answer_question(question)
    print(f"\n  💬 Answer:\n  {answer}")
    input("\n  Press Enter to go back...")


def menu_stats():
    print_header("📊 System Stats")
    stats = get_stats()
    print(f"""
  📁 Total jobs discovered : {stats['total_jobs']}
  🆕 New (not reviewed)    : {stats['new_jobs']}
  ✅ Applications sent      : {stats['applied']}
  📅 Applied today          : {stats['today_applied']}
  🧠 Q&A answers stored     : {stats['qa_answers']}
    """)
    input("  Press Enter to go back...")


if __name__ == "__main__":
    init_db()
    menu_main()
