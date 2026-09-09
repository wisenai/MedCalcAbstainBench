import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import hashlib
import json
import os

api_key = os.environ["OPENROUTER_API_KEY"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

@retry(stop = stop_after_attempt(3), wait= wait_exponential(multiplier = 1, min = 2, max = 10))
def prompt_model(model_name, prompt_text):
  response = client.chat.completions.create(
      model = model_name,
      messages = [{"role": "user", "content": prompt_text}],
      extra_body = {"usage": {"include": True}},
  )

  result = {
      "model": model_name,
      "prompt": prompt_text,
      "response_text": response.choices[0].message.content,
      "input_tokens": response.usage.prompt_tokens,
      "output_tokens": response.usage.completion_tokens,
      "cost": response.usage.cost,
  }

  return result

CACHE_PATH = "cache"

if not os.path.isdir(CACHE_PATH):
    raise RuntimeError(
        "Can't find the 'cache' folder. Make sure you've run "
        "%cd into the MedCalcAbstainBench folder before using run.py."
    )

def make_cache_key(model, item_id, prompt_id, format):
  join = f"{model}_{item_id}_{prompt_id}_{format}"
  hash_object = hashlib.sha256(join.encode())
  return hash_object.hexdigest()

def get_completion(model, item_id, prompt_id, format, prompt_text):
  cache_key = make_cache_key(model, item_id, prompt_id, format)
  cache_path = os.path.join(CACHE_PATH, f"{cache_key}.json")

  if os.path.exists(cache_path):
    with open(cache_path, "r") as f:
      return json.load(f)

  result = prompt_model(model, prompt_text)

  with open(cache_path, "w") as f:
    json.dump(result, f)

  return result
