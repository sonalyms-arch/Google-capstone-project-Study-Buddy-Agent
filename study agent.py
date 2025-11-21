import datetime
from datetime import date, timedelta

# -----------------------------
# Helper functions
# -----------------------------

def parse_date(date_str):
    """
    Parse a date in YYYY-MM-DD format.
    """
    try:
        year, month, day = map(int, date_str.split("-"))
        return date(year, month, day)
    except Exception:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return None


def get_days_until_exam(exam_date):
    """
    Return number of days from today until exam_date.
    """
    today = date.today()
    delta = (exam_date - today).days
    return max(delta, 0)


# -----------------------------
# Collect user input
# -----------------------------

def collect_subject_info():
    print("Welcome to Study Buddy Agent 📚")
    print("Let's set up your subjects and exams.\n")

    subjects = []

    while True:
        subject_name = input("Enter subject name (or press Enter to finish): ").strip()
        if subject_name == "":
            break

        exam_date_str = input(f"Enter exam date for {subject_name} (YYYY-MM-DD): ").strip()
        exam_date = parse_date(exam_date_str)
        if not exam_date:
            print("Skipping this subject due to invalid date.\n")
            continue

        is_weak_str = input(f"Is {subject_name} a weak subject for you? (yes/no): ").strip().lower()
        is_weak = is_weak_str in ["yes", "y"]

        subjects.append({
            "name": subject_name,
            "exam_date": exam_date,
            "weak": is_weak
        })

    if not subjects:
        print("No subjects entered. Exiting.")
        exit(0)

    # Daily study hours
    while True:
        try:
            daily_hours = float(input("\nHow many hours can you study per day? (e.g. 2): ").strip())
            if daily_hours <= 0:
                print("Please enter a positive number.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")

    # Duration of plan (days)
    while True:
        try:
            plan_days = int(input("For how many days do you want to generate a plan? (e.g. 7): ").strip())
            if plan_days <= 0:
                print("Please enter a positive integer.")
                continue
            break
        except ValueError:
            print("Please enter a valid integer.")

    return subjects, daily_hours, plan_days


# -----------------------------
# Scheduling logic
# -----------------------------

def compute_priority(subject):
    """
    Compute a priority score based on how close the exam is and whether it's weak.
    Higher score = more priority.
    """
    days_until = get_days_until_exam(subject["exam_date"])

    # Avoid division by zero
    days_factor = 1 / (days_until + 1)

    weak_bonus = 0.5 if subject["weak"] else 0.0

    return days_factor + weak_bonus


def generate_study_plan(subjects, daily_hours, plan_days):
    """
    Generate a simple day-wise study plan.
    Each day will be split into 1-hour blocks.
    Subjects will be scheduled based on priority.
    """
    print("\nGenerating your study plan...\n")

    # 1-hour blocks per day
    blocks_per_day = int(daily_hours)

    if blocks_per_day == 0:
        print("Daily hours less than 1. Setting blocks_per_day = 1.")
        blocks_per_day = 1

    # Pre-calculate priorities
    for subj in subjects:
        subj["priority"] = compute_priority(subj)

    # Sort subjects by priority (high to low)
    subjects_sorted = sorted(subjects, key=lambda x: x["priority"], reverse=True)

    today = date.today()
    plan = []  # list of days; each day is dict {date, sessions: [subject names]}

    for day_index in range(plan_days):
        day_date = today + timedelta(days=day_index)
        day_sessions = []

        # Simple round-robin by priority
        for i in range(blocks_per_day):
            subject = subjects_sorted[(day_index * blocks_per_day + i) % len(subjects_sorted)]
            day_sessions.append(subject["name"])

        plan.append({
            "date": day_date,
            "sessions": day_sessions,
            "completed": [False] * len(day_sessions)
        })

    return plan


# -----------------------------
# Plan display and update
# -----------------------------

def display_day_plan(day_plan, day_number=None):
    """
    Print the plan for a single day.
    """
    if day_number is not None:
        print(f"\nDay {day_number + 1} - {day_plan['date']}:")
    else:
        print(f"\nDate: {day_plan['date']}")

    for idx, subj in enumerate(day_plan["sessions"]):
        status = "✅" if day_plan["completed"][idx] else "⬜"
        print(f"  [{status}] Block {idx + 1}: {subj}")


def mark_day_progress(day_plan):
    """
    Allow user to mark which sessions were completed.
    """
    print("\nMark completed sessions for this day.")
    print("Enter block numbers separated by commas (e.g. 1,3) or press Enter to skip.")
    completed_str = input("Completed blocks: ").strip()

    if completed_str == "":
        print("No updates made.")
        return day_plan

    try:
        indices = [int(x.strip()) - 1 for x in completed_str.split(",") if x.strip() != ""]
        for idx in indices:
            if 0 <= idx < len(day_plan["sessions"]):
                day_plan["completed"][idx] = True
            else:
                print(f"Ignoring invalid block number: {idx + 1}")
    except ValueError:
        print("Invalid input. No updates made.")

    return day_plan


def reschedule_incomplete_tasks(plan, current_day_index):
    """
    Move incomplete tasks from current day to future days.
    """
    current_day = plan[current_day_index]
    incomplete_subjects = [
        current_day["sessions"][i]
        for i, done in enumerate(current_day["completed"])
        if not done
    ]

    if not incomplete_subjects:
        print("Great! No incomplete tasks to reschedule.")
        return plan

    print(f"\nRescheduling {len(incomplete_subjects)} incomplete task(s) to future days...")

    # Start rescheduling from the next day
    future_days = plan[current_day_index + 1:]
    if not future_days:
        print("No future days in the plan. Tasks cannot be rescheduled.")
        return plan

    idx = 0
    for subj in incomplete_subjects:
        # place each incomplete subject in the earliest future day with free slot
        placed = False
        for day in future_days:
            try:
                # find first not-completed block and replace it
                free_index = day["completed"].index(False)
                day["sessions"][free_index] = subj
                placed = True
                break
            except ValueError:
                continue
        if not placed:
            print(f"Could not reschedule: {subj} (no free slots).")

        idx += 1

    print("Rescheduling done.")
    return plan


# -----------------------------
# Main interaction loop
# -----------------------------

def main():
    subjects, daily_hours, plan_days = collect_subject_info()
    plan = generate_study_plan(subjects, daily_hours, plan_days)

    while True:
        print("\n----- Study Buddy Agent Menu -----")
        print("1. View full plan")
        print("2. View a specific day")
        print("3. Mark progress for a day")
        print("4. Exit")
        choice = input("Enter your choice (1-4): ").strip()

        if choice == "1":
            for i, day_plan in enumerate(plan):
                display_day_plan(day_plan, i)

        elif choice == "2":
            try:
                day_num = int(input(f"Enter day number (1-{len(plan)}): ").strip()) - 1
                if 0 <= day_num < len(plan):
                    display_day_plan(plan[day_num], day_num)
                else:
                    print("Invalid day number.")
            except ValueError:
                print("Please enter a valid integer.")

        elif choice == "3":
            try:
                day_num = int(input(f"Enter day number to update (1-{len(plan)}): ").strip()) - 1
                if 0 <= day_num < len(plan):
                    display_day_plan(plan[day_num], day_num)
                    plan[day_num] = mark_day_progress(plan[day_num])
                    plan = reschedule_incomplete_tasks(plan, day_num)
                else:
                    print("Invalid day number.")
            except ValueError:
                print("Please enter a valid integer.")

        elif choice == "4":
            print("Goodbye! Keep studying consistently 💪")
            break

        else:
            print("Invalid choice. Please select 1–4.")


if __name__ == "__main__":
    main()