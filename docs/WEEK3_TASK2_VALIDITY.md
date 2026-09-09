# Week 3 -- Task 2: validity threshold

**What this measures.** Per PREREGISTRATION.md sect4, a model whose
clean-condition accuracy falls below 50% cannot have its flag rate
trusted as evidence about conflict detection -- it may not have
engaged with the note's numbers at all. "Study" here means prompt
arm (open_ended vs. neutral_exit), matching sect1's own scope: that's
the pair of prompts this project's whole validity machinery was
built around, not mcq/program_aided.

| model | arm | clean accuracy | status |
|---|---|---|---|
| `anthropic/claude-opus-4.8` | `open_ended` | 175/202 (86.6% [81.3% - 90.6%]) | OK |
| `anthropic/claude-opus-4.8` | `neutral_exit` | 178/202 (88.1% [82.9% - 91.9%]) | OK |
| `openai/gpt-5` | `open_ended` | 167/202 (82.7% [76.9% - 87.3%]) | OK |
| `openai/gpt-5` | `neutral_exit` | 169/202 (83.7% [77.9% - 88.1%]) | OK |
| `meta-llama/llama-4-maverick` | `open_ended` | 154/202 (76.2% [69.9% - 81.6%]) | OK |
| `meta-llama/llama-4-maverick` | `neutral_exit` | 159/202 (78.7% [72.6% - 83.8%]) | OK |
| `google/gemini-3.6-flash` | `open_ended` | 167/202 (82.7% [76.9% - 87.3%]) | OK |
| `google/gemini-3.6-flash` | `neutral_exit` | 174/202 (86.1% [80.7% - 90.2%]) | OK |
| `openai/gpt-5-mini` | `open_ended` | 163/202 (80.7% [74.7% - 85.5%]) | OK |
| `openai/gpt-5-mini` | `neutral_exit` | 167/202 (82.7% [76.9% - 87.3%]) | OK |

No model passes in one arm and fails in the other.

**Interpretation.** All 5 models clear the 50% clean-accuracy threshold in
both arms (76.2%-88.1%), so no flag rate in Tasks 1/3/4 needs to be
discounted for validity, and no model shows the "passes in one arm, fails
in the other" pattern the task specifically calls out. This means the
Family C reversal reported in Task 1/3 (flagging highest, silent
commitment lowest, of the three contradiction families) is not an
artifact of any model failing to engage with the notes at all -- every
model can demonstrably compute correctly on unmodified notes at a solid
rate, so its behavior on the defect conditions is real signal, not noise
from an incapable model.
