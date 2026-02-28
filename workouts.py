import csv
import random
from datetime import datetime
import shutil
import os
import json
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog

# -------------------- Config --------------------
CSV_FILE = "workouts.csv"
SESSION_LOG_FILE = "workouts_log.csv"
DEFAULT_TYPE_FILE = "workouts_lasttype.txt"

LAST_DATES_FILE = "workouts_dates.json"
LAST_DATES_BACKUP = "workouts_dates_backup.json"

level_name = ["", "Light", "Medium", "Intense"]
levels = { level_name[1]: 1, level_name[2]: 2, level_name[3]: 3 }
DEFAULT_TIME = 42
DEFAULT_TIME_BUFFER = 5
DEBUG = 0

# -------------------- Date Storage --------------------
def load_last_dates():
    if not os.path.exists(LAST_DATES_FILE):
        return {}

    with open(LAST_DATES_FILE, "r") as f:
        data = json.load(f)

    last_dates = {}
    for name, date_str in data.items():
        if date_str:
            last_dates[name] = datetime.strptime(date_str, "%Y-%m-%d")

    return last_dates


def save_last_dates(workouts):
    # Backup existing file
    if os.path.exists(LAST_DATES_FILE):
        shutil.copyfile(LAST_DATES_FILE, LAST_DATES_BACKUP)

    data = {}
    for w in workouts:
        if w["last_date"]:
            data[w["name"]] = w["last_date"].strftime("%Y-%m-%d")

    with open(LAST_DATES_FILE, "w") as f:
        json.dump(data, f, indent=4)

# -------------------- Data Handling --------------------
def load_workouts():
    workouts = []
    last_dates = load_last_dates()

    with open(CSV_FILE, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith("#"):
                continue

            name = row[2].strip()
            if len(row) > 4:
                music = row[4].strip()
            else:
                music = ""

            workouts.append({
                "type": row[0].strip(),
                "difficulty": int(row[1]),
                "name": name,
                "duration": int(row[3]),
                "music": music,
                "last_date": last_dates.get(name)
            })

    return workouts


def log_session(selected, w_type, total_time, avg_diff, session_level):
    today_str = datetime.today().strftime("%Y-%m-%d")

    if not os.path.exists(SESSION_LOG_FILE):
        with open(SESSION_LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Date", "Workout Type", "Total Duration",
                "Average Difficulty", "Session Level", "Workout Details"
            ])

    details = "; ".join(
        [f"{w['name']}({w['duration']}min,diff{w['difficulty']})" for w in selected]
    )

    with open(SESSION_LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            today_str, w_type, total_time,
            f"{avg_diff:.2f}", session_level, details
        ])


def get_default_type():
    if os.path.exists(DEFAULT_TYPE_FILE):
        with open(DEFAULT_TYPE_FILE, "r") as f:
            last = f.read().strip().lower()
            default = "groove" if last == "combat" else "combat"
    else:
        default = "combat"

    with open(DEFAULT_TYPE_FILE, "w") as f:
        f.write(default)

    return default

# -------------------- Workout Selection --------------------
def select_workouts(workouts, w_type, target_minutes, min_difficulty, max_difficulty):
    today = datetime.today()

    for w in workouts:
        w["days_since"] = (
            (today - w["last_date"]).days if w["last_date"] else 9999
        )

    # Get workouts of specific type and sort
    available = [w for w in workouts if w["type"] == w_type]
    available.sort(key=lambda w: w["days_since"], reverse=True)

    selected = []
    total_time = 0
    max_extra_time = DEFAULT_TIME_BUFFER

    # Ensure 1 of each difficulty if possible
    for difficulty in range(min_difficulty, max_difficulty+1):
        candidates = [
            w for w in available
            if w["difficulty"] == difficulty and w not in selected
        ]
        if DEBUG > 0:
            print("difficulty="+str(difficulty)+", "+str(len(candidates))+" candidates, "+str(len(w))+" workouts")
        if candidates:
            top_n = min(5, len(candidates))
            top_candidates = candidates[:top_n]
            random.shuffle(top_candidates)
            chosen = top_candidates[0]
            if DEBUG > 0:
                print("...adding(a) "+chosen["name"]+" - "+str(chosen["duration"])+" min "+level_name[chosen["difficulty"]])
            selected.append(chosen)
            total_time += chosen["duration"]

    difficulty_pools = {1: [], 2: [], 3: []}
    for w in available:
        if w not in selected:
            if w["difficulty"] >= min_difficulty and w["difficulty"] <= max_difficulty:
                difficulty_pools[w["difficulty"]].append(w)

    for pool in difficulty_pools.values():
        pool.sort(key=lambda w: w["days_since"], reverse=True)

    diff_cycle = range(min_difficulty, max_difficulty+1)
    diff_range = max_difficulty - min_difficulty + 1
    diff_idx = 0

    while total_time < target_minutes:
        diff = diff_cycle[diff_idx % diff_range]
        if difficulty_pools[diff]:
            next_workout = difficulty_pools[diff].pop(0)
            if total_time + next_workout["duration"] - target_minutes <= max_extra_time:
                if DEBUG > 0:
                    print("...adding(b) "+next_workout["name"]+" - "+str(next_workout["duration"]))
                selected.append(next_workout)
                total_time += next_workout["duration"]

        diff_idx += 1

        if all(len(pool) == 0 for pool in difficulty_pools.values()):
            break

    # Allow duplicates if needed
    if total_time < target_minutes:
        duplicates = available.copy()
        duplicates.sort(key=lambda w: w["days_since"], reverse=True)
        idx = 0

        while total_time < target_minutes and idx < len(duplicates):
            next_workout = duplicates[idx]
            if total_time + next_workout["duration"] - target_minutes <= max_extra_time:
                if DEBUG > 0:
                    print("...adding(c) "+next_workout["name"]+" - "+str(next_workout["duration"]))
                selected.append(next_workout)
                total_time += next_workout["duration"]
            idx += 1

    # Ensure at least 2 workouts
    if len(selected) < 2:
        additional = [w for w in available if w not in selected]
        additional.sort(key=lambda w: w["days_since"], reverse=True)

        for w in additional:
            if DEBUG > 0:
                print("...adding(d) "+selected["name"]+" - "+str(selected["duration"]))
            selected.append(w)
            total_time += w["duration"]
            if len(selected) >= 2:
                break

    summary = {1: 0, 2: 0, 3: 0}

    if len(selected) > 0:
        selected.sort(key=lambda w: (w["difficulty"], w["days_since"]))

        avg_diff = sum(w["difficulty"] for w in selected) / len(selected)

        if avg_diff < 1.5:
            session_level = level_name[1]
        elif avg_diff < 2.5:
            session_level = level_name[2]
        else:
            session_level = level_name[3]

        for w in selected:
            summary[w["difficulty"]] += w["duration"]
    else:
        print("NO WORKOUTS FOUND")
        session_level = level_name[1]
        avg_diff = 1

    return selected, total_time, session_level, avg_diff, summary

# -------------------- GUI --------------------
class WorkoutApp:
    def __init__(self, root):
        self.root = root
        root.title("Workout Generator")

        self.workouts = load_workouts()
        self.selected = []
        self.default_type = get_default_type()
        self.level_min_var = level_name[1]
        self.level_max_var = level_name[3]

        tk.Label(root, text="Workout type:", anchor="e").grid(row=0, column=0, sticky="e")
        self.type_var = tk.StringVar(value=self.default_type)
        tk.OptionMenu(root, self.type_var, "combat", "groove", "flow")\
            .grid(row=0, column=1, sticky="w")

        self.options = { level_name[1]: 1, level_name[2]: 2, level_name[3]: 3 }
        tk.Label(root, text="Min level:", anchor="e").grid(row=1, column=0, sticky="e")
        self.min_var = tk.StringVar(value=self.level_min_var)
        #tk.OptionMenu(root, self.min_var, *self.options.keys())\
        tk.OptionMenu(root, self.min_var, level_name[1], level_name[2], level_name[3])\
            .grid(row=1, column=1, sticky="w")
        tk.Label(root, text="Max level:", anchor="e").grid(row=1, column=2, sticky="e")
        self.max_var = tk.StringVar(value=self.level_max_var)
        tk.OptionMenu(root, self.max_var, level_name[1], level_name[2], level_name[3])\
            .grid(row=1, column=3, sticky="w")

        tk.Label(root, text="Target duration (minutes):")\
            .grid(row=2, column=0, sticky="e")
        self.duration_var = tk.StringVar(value=DEFAULT_TIME)
        tk.Entry(root, textvariable=self.duration_var)\
            .grid(row=2, column=1, sticky="w")

        tk.Button(root, text="Generate Workout",
                  command=self.generate)\
            .grid(row=4, column=0, columnspan=2, pady=5)

        #tk.Button(root, text="Generate Weekly Plan",
        #          command=self.weekly_plan)\
        #    .grid(row=6, column=0, columnspan=2, pady=5)

        self.text_area = scrolledtext.ScrolledText(
            root, width=70, height=20
        )
        self.text_area.grid(row=3, column=0, columnspan=5, pady=5)

        tk.Button(root, text="Approve", bg='blue', fg='white', command=self.approve)\
            .grid(row=4, column=2, pady=5)


    # -------------------- Single Day --------------------
    def generate(self):
        try:
            level_min = int(levels[self.min_var.get()])
        except:
            level_min = 1
        try:
            level_max = int(levels[self.max_var.get()])
        except:
            level_max = 3
        try:
            target = int(self.duration_var.get())
        except:
            target = DEFAULT_TIME

        if level_min > level_max:
            swap = level_min
            level_min = level_max
            level_max = swap

        w_type = self.type_var.get()

        self.selected, total_time, session_level, avg_diff, summary = \
            select_workouts(self.workouts, w_type, target, level_min, level_max)

        self.display_results(
            self.selected, total_time, avg_diff,
            session_level, summary, w_type
        )

    def display_results(self, selected, total_time,
                        avg_diff, session_level, summary, w_type):

        self.text_area.delete("1.0", tk.END)
        levelName = ["", "Light", "Medium", "Intense"]

        # Color tags
        self.text_area.tag_config("green",foreground="green",font=("TkDefaultFont",10,"bold"))
        self.text_area.tag_config("orange",foreground="orange",font=("TkDefaultFont",10,"bold"))
        self.text_area.tag_config("red",foreground="red",font=("TkDefaultFont",10,"bold"))

        self.text_area.insert(tk.END, f"\nSelected Workouts: ({w_type})\n")
        for w in selected:
            color="green" if w["difficulty"]==1 else "orange" if w["difficulty"]==2 else "red"
            if w["music"] != "":
                w_music = ", "+w['music']
            else:
                w_music = ""
            self.text_area.insert(tk.END,f"  - {w['name']} ({w['duration']} min, {levelName[w['difficulty']]}{w_music})",color)
            if w["last_date"]:
                self.text_area.insert(tk.END,f"  -  last: "+w["last_date"].strftime("%Y-%m-%d"))
            self.text_area.insert(tk.END,"\n")

        self.text_area.insert(tk.END, f"\n  Duration: {total_time} min (")
        for diff in [1, 2, 3]:
            color="green" if diff==1 else "orange" if diff==2 else "red"
            self.text_area.insert(tk.END, f"{summary[diff]} min @ {levelName[diff]}",color)
            if diff < 3:
                self.text_area.insert(tk.END, f" / ")
        self.text_area.insert(tk.END, f")\n")

        if avg_diff < 1.5: session_color="green"
        elif avg_diff < 2.5: session_color="orange"
        else: session_color="red"
        self.text_area.insert(tk.END, f"  Average difficulty: {avg_diff:.2f} (")
        self.text_area.insert(tk.END, f"{session_level}",session_color)
        self.text_area.insert(tk.END, f")\n")

    # -------------------- Approve --------------------
    def approve(self):
        if not self.selected:
            messagebox.showwarning(
                "No Selection",
                "Generate workouts first!"
            )
            return

        today = datetime.today()

        print("\nWORKOUTS for "+str(today)+":")
        for w in self.workouts:
            if w in self.selected:
                w["last_date"] = today
                print(" - "+w["name"]+" - "+str(w["duration"])+" min ("+level_name[w["difficulty"]]+")")

        total_time = sum(w["duration"] for w in self.selected)
        avg_diff = sum(
            w["difficulty"] for w in self.selected
        ) / len(self.selected)

        print("Total Time: "+str(total_time)+" min")
        save_last_dates(self.workouts)

        log_session(
            self.selected,
            self.type_var.get(),
            total_time,
            avg_diff,
            ""
        )

        messagebox.showinfo(
            "Approved",
            "Workouts approved, dates saved and session logged!"
        )

    # -------------------- Weekly Plan --------------------
    def weekly_plan(self):
        try:
            days = simpledialog.askinteger(
                "Number of Days",
                "Enter number of days for weekly plan (default 5):",
                initialvalue=5,
                minvalue=1
            )
        except:
            days = 5

        try:
            target = int(self.duration_var.get())
        except:
            target = DEFAULT_TIME

        self.text_area.delete("1.0", tk.END)

        current_type = self.default_type
        weekly_selected = []

        for day in range(1, days + 1):
            selected, total_time, session_level, avg_diff, summary = \
                select_workouts(self.workouts, current_type, target)

            weekly_selected.extend(selected)

            self.text_area.insert(
                tk.END,
                f"Day {day} - Workout Type: {current_type}\n"
            )
            self.text_area.insert(
                tk.END,
                f"Total Duration: {total_time} min, "
                f"Avg Difficulty: {avg_diff:.2f}, "
                f"Session Level: {session_level}\n"
            )

            for w in selected:
                self.text_area.insert(
                    tk.END,
                    f"- {w['name']} "
                    f"({w['duration']} min, diff {w['difficulty']})\n"
                )

            self.text_area.insert(tk.END, "\n")

            current_type = "groove" \
                if current_type == "combat" else "combat"

        self.selected = weekly_selected

        messagebox.showinfo(
            "Weekly Plan",
            "Weekly plan generated! Approve to log all sessions."
        )

# -------------------- Run --------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = WorkoutApp(root)
    root.mainloop()

