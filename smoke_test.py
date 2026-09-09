import json
import random
import yaml
from run import get_completion

with open("data/items_dissociation.json") as f:
    data = json.load(f)

def flatten_items(data):
    flat = []
    for seed in data["items"]:
        for cond in seed["conditions"]:
            item = {
                "item_id": f"{seed['seed_id']}_{cond['condition']}",
                "calculator": seed["calculator"],
                "note": cond["note"],
                "question": cond["question"],
                "correct_action": cond["correct_action"],
                "correct_answer": cond["correct_answer"],
                "conflict": seed.get("conflict"),
            }
            flat.append(item)
    return flat

def random_decoy(value):
  factor = random.uniform(1.3, 2.2)
  if random.random() < 0.5:
    return round(float(value) * factor, 2)
  else:
    return round(float(value) / factor, 2)
  

def generate_mcq_options(item):
  insufficient = "insufficient or contradictory information"

  if item["correct_action"] == "compute":
    correct_value = str(item["correct_answer"])
    decoy1 = str(random_decoy(correct_value))
    decoy2 = str(random_decoy(correct_value))
    choices = [(decoy1, False), (decoy2, False), (insufficient, False), (correct_value, True)]
  
  else:
    conflict = item["conflict"]
    decoy1 = str(conflict["answer_with_stated"])
    decoy2 = str(conflict["answer_with_second"])
    decoy3 = str(random_decoy(random.choice([conflict["answer_with_stated"], conflict["answer_with_second"]])))
    choices = [(decoy1, False), (decoy2, False), (decoy3, False), (insufficient, True)]

  random.shuffle(choices)

  letters = ["A", "B", "C", "D"]
  randomized_options = []
  correct_letter = None
  for letter, (value, is_correct), in zip(letters, choices):
    randomized_options.append(f"{letter}. {value}")
    if is_correct:
      correct_letter = letter

  listed_options = "\n".join(randomized_options)
  return listed_options, correct_letter

with open("prompts/prompts.yaml") as f:
  prompts = yaml.safe_load(f)

MODEL = "openai/gpt-5-mini"
flat_items = flatten_items(data)
SMOKE_ITEMS = flat_items[:20]

def build_prompt(prompt_id, item):
  if prompt_id == "mcq":
    listed_options, correct_letter = generate_mcq_options(item)
    item["mcq_correct_letter"] = correct_letter
    return prompts["mcq"].format(
        note = item["note"], question = item["question"], options = listed_options
    )
  else:
    return prompts[prompt_id].format(note = item["note"], question = item["question"])

# results = []
# for item in SMOKE_ITEMS:
#   for prompt_id in ["mcq", "open_ended", "program_aided"]:
#     prompt_text = build_prompt(prompt_id, item)
#     result = get_completion(
#         model = MODEL,
#         item_id = item["item_id"],
#         prompt_id = prompt_id,
#         format = prompt_id,
#         prompt_text = prompt_text,
#     )
#     results.append(result)
