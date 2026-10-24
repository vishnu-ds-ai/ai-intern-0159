# Run with:  python3 sensitivity.py   (same folder as the CSVs)
# Tries every scoring choice to see if the model-a vs model-b conclusion changes.
import csv, re

def read(name):
    return list(csv.DictReader(open(name, encoding="utf-8")))

questions = {r["question_id"]: r["question"] for r in read("questions.csv")}
old_key   = {r["question_id"]: r["expected"] for r in read("answer_key.csv")}
results   = read("results.csv")

# Correct answers, computed from the question text.
def solve(text):
    a, op, b = re.search(r"(\d+)\s*([+\-×])\s*(\d+)", text).groups()
    a, b = int(a), int(b)
    return str({"+": a + b, "-": a - b, "×": a * b}[op])
new_key = {q: solve(t) for q, t in questions.items()}

# Duplicate pairs: (first copy, later copy) of the same question text.
first_seen, pairs = {}, []
for q in sorted(questions):
    text = " ".join(questions[q].split()).lower()
    if text in first_seen:
        pairs.append((first_seen[text], q))
    else:
        first_seen[text] = q

# Choice 1: how to read the response.
def read_response(response, how):
    numbers = re.findall(r"\d[\d,]*", response)
    if how == "strict":
        return response.strip()
    if not numbers:
        return ""
    pick = numbers[0] if how == "first" else numbers[-1]
    return pick.replace(",", "")

# Choice 3: which duplicate questions to leave out.
def questions_to_skip(how):
    if how == "keep_both":  return []
    if how == "keep_first": return [later for first, later in pairs]
    if how == "keep_later": return [first for first, later in pairs]
    if how == "drop_all":   return [q for pair in pairs for q in pair]

def accuracy(model, read_how, key, dup_how):
    skip = questions_to_skip(dup_how)
    rows = [r for r in results if r["model"] == model and r["question_id"] not in skip]
    hits = sum(read_response(r["response"], read_how) == key[r["question_id"]] for r in rows)
    return 100 * hits / len(rows)

print(f"{'read':7s} {'key':9s} {'duplicates':11s} {'model-a':>8s} {'model-b':>8s} {'a-b':>6s}")
for read_how in ["strict", "first", "last"]:
    for key_name, key in [("original", old_key), ("fixed", new_key)]:
        for dup_how in ["keep_both", "keep_first", "keep_later", "drop_all"]:
            a = accuracy("model-a", read_how, key, dup_how)
            b = accuracy("model-b", read_how, key, dup_how)
            print(f"{read_how:7s} {key_name:9s} {dup_how:11s} {a:7.1f}% {b:7.1f}% {a - b:6.1f}")

# Are model-b's remaining mistakes real? (final rule: last number, fixed key, keep first copy)
skip = questions_to_skip("keep_first")
print("\nmodel-b wrong answers under the final rule:")
for r in results:
    q = r["question_id"]
    if r["model"] == "model-b" and q not in skip and read_response(r["response"], "last") != new_key[q]:
        print(f"  run {r['run']} {q}: {r['response']!r}  correct = {new_key[q]}")
