# Is model-a better than model-b?

**No. After fixing the measurement, they are about equal.**

## What was wrong
1. **Strict matching.** score.py needs an exact match. model-b often writes "The answer is 6,120." or "**6046**", which counted as wrong. model-a only outputs bare numbers.
2. **Wrong answer key.** I solved each question myself. q008, q040 and q056 have wrong keys.
3. **Duplicate questions.** Six questions repeat an earlier one (q022, q023, q033, q047, q049, q052), so they were counted twice.
4. **Different settings.** model-a ran at temperature 0.0, model-b at 0.7. model-a gave identical answers in all 3 runs, so its runs add no new information.

## What I changed
I took the last number in each response, removed commas, fixed the key, and dropped the later copy of each duplicate. That leaves 50 questions x 3 runs.

| Step | model-a | model-b |
|---|---|---|
| Original | 80.4% | 47.0% |
| Number extracted | 80.4% | 78.6% |
| Key fixed | 85.7% | 82.1% |
| Duplicates dropped | **84.0%** | **86.0%** |

## Conclusion
The gap is -2.0 points (model-b ahead). A bootstrap over questions gives a 95% interval of about -13 to +9, so I cannot say either is better. With the corrected key, other duplicate choices (sensitivity.py) gave gaps from -9 to +4; I did not test those for significance. The original 33-point gap was mostly by how the scoring is done.

## What this does not prove
- Only 50 easy arithmetic questions; nothing about other tasks.
- The temperature difference means I cannot tell if differences in results come from the model or the setting i.e tempearture.
- Assumed the last number is the final answer, and the later duplicate is the extra one.
- Speed, cost and reliability were not compared.
