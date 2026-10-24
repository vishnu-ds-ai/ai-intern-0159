# Run with:  python3 analysis.py      (questions.csv, answer_key.csv, results.csv in the same folder)
import csv, re, random

# ---------- 1. Load ----------
def read(name):
    return list(csv.DictReader(open(name, encoding="utf-8")))

questions = {r["question_id"]: r["question"] for r in read("questions.csv")}
key       = {r["question_id"]: r["expected"] for r in read("answer_key.csv")}
results   = read("results.csv")

# ---------- 2. Check the answer key by doing the arithmetic ourselves ----------
def solve(text):
    a, op, b = re.search(r"(\d+)\s*([+\-×])\s*(\d+)", text).groups()
    a, b = int(a), int(b)
    return str({"+": a + b, "-": a - b, "×": a * b}[op])

true_answer = {q: solve(t) for q, t in questions.items()}
wrong_key_ids = [q for q in sorted(key) if key[q] != true_answer[q]]

# ---------- 3. Find duplicate questions (same text) ----------
# Keep the first copy, mark later copies as duplicates.
seen, duplicate_ids = {}, []
for q in sorted(questions):
    text = " ".join(questions[q].split()).lower()
    if text in seen:
        duplicate_ids.append(q)
    else:
        seen[text] = q

# ---------- 4. Pull the number out of a response ----------
def extract_number(response):
    # "The answer is 7,364." -> "7364"   "**6046**" -> "6046"   "12 × 63 = 756" -> "756"
    numbers = re.findall(r"\d[\d,]*", response)
    return numbers[-1].replace(",", "") if numbers else ""   # last number = the final answer

# ---------- 5. Score, one fix at a time ----------
def accuracy(model, answer_key, skip_ids=(), clean=False):
    hits = total = 0
    for r in results:
        if r["model"] != model or r["question_id"] in skip_ids:
            continue
        got = extract_number(r["response"]) if clean else r["response"].strip()
        total += 1
        hits += got == answer_key[r["question_id"]]
    return 100 * hits / total, hits, total

steps = [
    ("original (as colleague scored it)", key,         (),            False),
    ("+ read the number inside the text", key,         (),            True),
    ("+ fix wrong answer-key rows",       true_answer, (),            True),
    ("+ drop duplicate questions",        true_answer, duplicate_ids, True),
]
print(f"{'step':36s} {'model-a':>16s} {'model-b':>16s}")
for name, k, skip, clean in steps:
    a = accuracy("model-a", k, skip, clean)
    b = accuracy("model-b", k, skip, clean)
    print(f"{name:36s} {a[0]:6.1f}% ({a[1]}/{a[2]})  {b[0]:6.1f}% ({b[1]}/{b[2]})")

# ---------- 6. Final numbers ----------
final_a = accuracy("model-a", true_answer, duplicate_ids, True)[0]
final_b = accuracy("model-b", true_answer, duplicate_ids, True)[0]
print(f"\naccuracy_model_a: {final_a:.1f}")
print(f"accuracy_model_b: {final_b:.1f}")
print("duplicate_question_ids:", ",".join(duplicate_ids))
print("wrong_answer_key_ids:", ",".join(wrong_key_ids))

# ---------- 7. How sure are we? ----------
# The 3 runs of one question are not independent, so resample QUESTIONS, not rows.
# For each question: the share of its 3 runs that each model got right.
good = [q for q in sorted(questions) if q not in duplicate_ids]
share = {"model-a": {}, "model-b": {}}
for m in share:
    for q in good:
        runs = [r for r in results if r["model"] == m and r["question_id"] == q]
        share[m][q] = sum(extract_number(r["response"]) == true_answer[q] for r in runs) / len(runs)

random.seed(0)
gaps = []
for _ in range(10000):
    pick = [random.choice(good) for _ in good]            # resample questions with replacement
    gaps.append(sum(share["model-a"][q] - share["model-b"][q] for q in pick) / len(pick) * 100)
gaps.sort()
print(f"\ngap a-b: {final_a - final_b:.1f} points, 95% interval {gaps[250]:.1f} to {gaps[9750]:.1f}")

# Does model-a (temperature 0) just repeat itself across its 3 runs?
same = sum(len({extract_number(r["response"]) for r in results
                if r["model"] == "model-a" and r["question_id"] == q}) == 1 for q in good)
print(f"model-a gave the same answer in all 3 runs on {same}/{len(good)} questions")
print("temperatures used:", {m: sorted({r["temperature"] for r in results if r["model"] == m}) for m in share})
