# Week 2 -- Task 2 result

Independent judge (`score.py`'s `get_judge_label`) vs. `classify_response`,
on a stratified 20% sample (n=72: 8 rows from each of the 9 arm x condition cells, fixed seed 42).

- Coarse agreement (flag vs. commit): 72/72 (100.0% [94.9% - 100.0%]), Cohen's kappa = 1.000 (PREREGISTRATION.md sect7's kappa<0.6 reliability threshold applies to this figure)
- Three-way agreement: 56/72 (77.8% [66.9% - 85.8%]), Cohen's kappa = 0.667

Disagreements: 16 of 72. 16 at the acknowledged/silent boundary (never crosses the flag/commit line the primary metric depends on), 0 cross the flag/commit line.
