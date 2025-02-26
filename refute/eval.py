import json
import argparse
from typing import Any, Dict, List, Union
from refute.utils.code_exec import run_code, is_fail_case, run_randsearch
from refute.utils.dataset_parser import get_correct_sub
from refute.utils.logging_config import get_logger

logger = get_logger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--pred_path", type=str, required=True, help="Path to predictions file")
parser.add_argument("--output_path", type=str, default="results.json", help="Path to save JSON results")
parser.add_argument("--runs_per_eval", type=int, default=5,
                    help="Number of code runs to compare outputs with ground truth")
parser.add_argument("--randsearch_timeout", type=int, default=60, help="Time limit for search strategies")
args = parser.parse_args()

with open(args.pred_path, "r") as f:
    preds = json.load(f)


def standard_eval(problem_id: str, attempt: Dict[str, Any]) -> Dict[str, Union[bool, str]]:
    """
    Evaluates a standard attempt which has a generate_inp script to print a single test.

    Returns:
        A dictionary with success status and failure information if applicable.
    """
    try:
        code, lang = attempt["generate_inp"]["code"], attempt["generate_inp"]["lang"]
        inp = run_code(code, lang)["output"]
        return is_fail_case(problem_id, inp, args.runs_per_eval)
    except Exception as e:
        return {"success": False, "info": f"Failed to test: {e}"}


def randsearch_eval(problem_id: str, attempt: Dict[str, Any], oracle: bool = False) -> Dict[str, Union[bool, str]]:
    """
    Evaluates a randsearch attempt with generate_inp and solve_brute scripts.

    Returns:
        A dictionary with success status and additional evaluation details.
    """
    try:
        gen_sub = attempt["generate_inp"]
        brute_sub = get_correct_sub(problem_id) if oracle else attempt["solve_brute"]
        return run_randsearch(problem_id, brute_sub, gen_sub, args.randsearch_timeout, args.runs_per_eval)
    except Exception as e:
        return {"success": False, "info": f"Failed to test: {e}"}


all_results: List[Dict[str, Any]] = []

for i, pred in enumerate(preds):
    problem_id, method = pred["problem_id"], pred["method"]
    logger.info(f"Evaluating prediction {i + 1}\t{problem_id} {method}")
    curr_verdicts: List[Dict[str, Any]] = []

    for attempt in pred["attempts"]:
        if method == "standard":
            verdict = standard_eval(problem_id, attempt)
        elif method in ["randsearch", "randsearch_oracle"]:
            verdict = randsearch_eval(problem_id, attempt, "oracle" in method)
        else:
            raise ValueError(f"Invalid method: {method}")

        curr_verdicts.append(verdict)

    all_results.append({"problem_id": problem_id, "verdicts": curr_verdicts})
    logger.info(f"Results: \t{[int(v['success']) for v in curr_verdicts]}")
    with open(args.output_path, "w") as f:
        json.dump(all_results, f)
