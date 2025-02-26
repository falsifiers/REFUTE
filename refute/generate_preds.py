import json, argparse
from refute.utils.get_dataset import get_dataset
from refute.utils.logging_config import get_logger
from refute.utils.dataset_parser import get_correct_sub
from refute.utils.models import VanillaLLM, VanillaOracleLLM, RandSearchOracleLLM
from refute.utils.xml_parser import parse_multiple_actions

parser = argparse.ArgumentParser()
parser.add_argument("--model_name", type=str, required=True,
                    help="Either an OpenRouter model (e.g. deepseek/deepseek-chat) or gemini-2.0-flash-thinking-exp-01-21")
parser.add_argument("--method", type=str, required=True,
                    choices=["few_shot", "zero_shot", "zero_shot_oracle", "randsearch", "randsearch_oracle"],
                    help="One of standard, standard_oracle, randsearch, and randsearch_oracle")
parser.add_argument("--n_attempts", type=int, required=False, default=1, help="Number of attempts per task")
parser.add_argument("--pred_path", type=str, required=False, default="preds.json", help="Path to predictions JSON file")

args = parser.parse_args()
logger = get_logger(__name__)
dataset = get_dataset()

MODEL_CLASSES = {
    "few_shot": VanillaLLM,
    "zero_shot": VanillaLLM,
    "randsearch": VanillaLLM,
    "zero_shot_oracle": VanillaOracleLLM,
    "randsearch_oracle": RandSearchOracleLLM,
}

EVAL_METHODS = {
    "few_shot": "standard",
    "zero_shot": "standard",
    "zero_shot_oracle": "standard",
    "randsearch": "randsearch",
    "randsearch_oracle": "randsearch_oracle",
}

model = MODEL_CLASSES[args.method](args.model_name, args.method)
eval_method = EVAL_METHODS[args.method]

all_preds = []

for problem_id, task in dataset.items():
    logger.info(f"Starting {problem_id}") # 1975F is nice for v3
    curr_preds = []

    for _ in range(args.n_attempts):
        if args.method in ["zero_shot_oracle", "randsearch_oracle"]:
            resp = model.ask(task, task["wrong_code"], get_correct_sub(problem_id)["code"])
        else:
            resp = model.ask(task, task["wrong_code"])

        parsed = parse_multiple_actions(resp)
        if eval_method == "standard":
            pred = {"generate_inp": parsed["print_fail_case"]}
        elif eval_method == "randsearch_oracle":
            pred = {"generate_inp": parsed["generate_tc"]}
        elif eval_method == "randsearch":
            pred = {"generate_inp": parsed["generate_tc"], "solve_brute": parsed["solve_brute"]}

        curr_preds.append(pred)

    all_preds.append({"problem_id": problem_id, "method": eval_method, "attempts": curr_preds})

    with open(args.pred_path, "w") as f:
        json.dump(all_preds, f)
    break
