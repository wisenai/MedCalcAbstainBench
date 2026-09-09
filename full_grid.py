import datetime
import hashlib
import json
import random
import yaml
from run import get_completion
import os
import subprocess

ITEMS_FILES = [
    "items_dissociation.json",
    "items_breadth_anion_gap.json",
    "items_breadth_ldl.json",
    "items_breadth_osmolality.json",
    "items_family_a.json",
    "items_family_a_anion_gap.json",
    "items_family_b.json",
    "items_family_c.json",
]

def load_all_seeds():
    all_seeds = []
    for filename in ITEMS_FILES:
        filepath = os.path.join("data", filename)
        with open(filepath) as f:
            file_data = json.load(f)
        seeds = file_data.get("items", [])
        all_seeds.extend(seeds)
        print(f"{filename}: {len(seeds)} seeds loaded")
    return all_seeds


def flatten_items(all_seeds):
    flat = []
    for seed in all_seeds:
        for cond in seed["conditions"]:
            item_id = cond.get("item_id") or f"{seed['seed_id']}_{cond['condition']}"
            item = {
                "item_id": item_id,
                "seed_id": seed["seed_id"],
                "calculator": seed.get("calculator"),
                "family": seed.get("family"),
                "note": cond["note"],
                "question": cond["question"],
                "correct_action": cond["correct_action"],
                "correct_answer": cond.get("correct_answer"),
                "condition": cond["condition"],
                "shape": cond.get("shape"),
                "conflict": seed.get("conflict"),
                "components": seed.get("components"),
                "documented_value": seed.get("documented_value"),
                "blood_pressure": seed.get("blood_pressure"),
                "injections": seed.get("injections"),
                "criterion": seed.get("criterion"),
                "injection": seed.get("injection"),
            }
            flat.append(item)
    return flat


all_seeds = load_all_seeds()
flat_items = flatten_items(all_seeds)


def random_decoy(value): #creates mcq decoy values
  factor = random.uniform(1.3, 2.2)
  if random.random() < 0.5:
    return round(float(value) * factor, 2)
  else:
    return round(float(value) / factor, 2)


def get_family_decoys(item):
    """Returns a list of plausible wrong numeric values, based on which family this item belongs to."""

    # Family C: yes/no criterion — decoys are the score with vs. without the criterion
    if item.get("injection") and "score_with_criterion" in item.get("injection", {}):
        inj = item["injection"]
        return [inj["score_with_criterion"], inj["score_without_criterion"]]

    # Family A: a derived value (e.g. BMI) contradicts its own components
    if item.get("documented_value"):
        dv = item["documented_value"]
        vals = [dv.get("published"), dv.get("recomputed_from_components")]
        return [v for v in vals if v is not None]

    # Family B: impossible value, shape-specific (transposed vs lowered)
    if item.get("injections") and item.get("shape"):
        shape_data = item["injections"].get(item["shape"], {})
        val = shape_data.get("answer_if_computed")
        return [val] if val is not None else []

    # Dissociation arm / breadth arm: two plausible readings of the same value
    if item.get("conflict"):
        c = item["conflict"]
        vals = [c.get("answer_with_stated"), c.get("answer_with_second")]
        return [v for v in vals if v is not None]

    return []


def generate_mcq_options(item):
    insufficient = "insufficient or contradictory information"

    if item["correct_action"] == "compute":
        correct_value = str(item["correct_answer"])
        decoy1 = str(random_decoy(item["correct_answer"]))
        decoy2 = str(random_decoy(item["correct_answer"]))
        choices = [(decoy1, False), (decoy2, False), (insufficient, False), (correct_value, True)]

    else:
        decoys = get_family_decoys(item)

        if len(decoys) >= 2:
            base = decoys[:2]
        elif len(decoys) == 1:
            base = [decoys[0], random_decoy(decoys[0])]
        else:
            print("WARNING: no decoys found for", item["item_id"])
            base = [0.0, 0.0]  # placeholder — flag for investigation, should be rare

        decoy_strs = [str(v) for v in base]
        extra_decoy = str(random_decoy(random.choice(base)))
        choices = [(decoy_strs[0], False), (decoy_strs[1], False), (extra_decoy, False), (insufficient, True)]

    random.shuffle(choices)

    letters = ["A", "B", "C", "D"]
    randomized_options = []
    correct_letter = None
    for letter, (value, is_correct) in zip(letters, choices):
        randomized_options.append(f"{letter}. {value}")
        if is_correct:
            correct_letter = letter

    listed_options = "\n".join(randomized_options)
    return listed_options, correct_letter


def build_prompt(prompt_id, item): #creates prompt for models
  if prompt_id == "mcq":
    listed_options, correct_letter = generate_mcq_options(item)
    item["mcq_correct_letter"] = correct_letter
    return prompts["mcq"].format(
        note = item["note"], question = item["question"], options = listed_options
    )
  else:
    return prompts[prompt_id].format(note = item["note"], question = item["question"])


MANIFEST_PATH = "manifest.jsonl"

def log_manifest_entries(model_name, prompt_id, prompt_text, settings = None):
  line = {
      "model": model_name,
      "date": datetime.datetime.now().isoformat(),
      "prompt_id": prompt_id,
      "prompt_hash": hashlib.sha256(prompt_text.encode()).hexdigest(),
      "settings": settings if settings is not None else {}
  }
  with open(MANIFEST_PATH, "a") as f:
    f.write(json.dumps(line) + "\n")


with open("prompts/prompts.yaml") as f: #loads prompts
  prompts = yaml.safe_load(f)

MODELS = ["anthropic/claude-opus-4.8", "openai/gpt-5", "meta-llama/llama-4-maverick", "google/gemini-3.6-flash", "openai/gpt-5-mini"]
# items = flatten_items(data)[:2]
FORMATS = ["open_ended", "mcq", "program_aided"]

def run_item(model, prompt_id, item, format):
    prompt_text = build_prompt(prompt_id, item)
    result = get_completion(
        model = model,
        item_id = item["item_id"],
        prompt_id = prompt_id,
        format = format,
        prompt_text = prompt_text,
    )
    log_manifest_entries(model, prompt_id, prompt_text)
    return result

CHUNK_SIZE = 100
CHUNK_INDEX = 1  # change this each run: 0, 1, 2, 3, 4, 5

start = CHUNK_INDEX * CHUNK_SIZE
if CHUNK_INDEX == 5:
    end = len(flat_items)
else:
    end = start + CHUNK_SIZE

items_this_run = flat_items[start:end]
print(f"Running chunk {CHUNK_INDEX}: items {start} to {end} ({len(items_this_run)} items)")

# ... (all your existing function definitions stay exactly where they are) ...

for model in MODELS:
  for prompt in prompts:
    if prompt in FORMATS:
      for item in items_this_run:
        try:
          result = run_item(model, prompt, item, prompt)
          print(model)
          print("  cost:", result["cost"])
          # print("  input/output tokens:", result["input_tokens"], "/", result["output_tokens"])
          # print("  response preview:", result["response_text"][:100])      
          print("---")
        except Exception as e:
          print(f"FAILED: {model} / {prompt} / {item['item_id']} -> {e}")

def push_to_github(chunk_index):
    subprocess.run(["git", "add", "cache/", "manifest.jsonl"])
    subprocess.run(["git", "commit", "-m", f"Full grid: chunk {chunk_index} auto-pushed"])
    subprocess.run(["git", "config", "pull.rebase", "false"])
    pull_result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
    if pull_result.returncode == 0:
        subprocess.run(["git", "commit", "--no-edit"])
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Pushed to GitHub successfully.")
    else:
        print("PUSH FAILED —", result.stderr)

push_to_github(CHUNK_INDEX)


