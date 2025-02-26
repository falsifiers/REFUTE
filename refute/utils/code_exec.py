import subprocess
from pathlib import Path
import psutil
import hashlib
from typing import Dict, Tuple, Optional, Any, Union, List, TypedDict

from refute.utils.get_dataset import get_dataset
from refute.utils.dataset_parser import parse_lang, get_wrong_sub, get_correct_sub
from refute.utils.checker import compare_outputs
import refute

dataset = get_dataset()
root_dir = Path(refute.__file__).parent
temp_code_dir = root_dir / "tmp"

if not Path(temp_code_dir).exists():
    Path(temp_code_dir).mkdir()


class Submission(TypedDict):
    """Type representing a code submission with language information."""
    code: str
    lang: str


def get_code_hash(code: str) -> str:
    """Generate an SHA-256 hash of the provided code."""
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def run_code(code: str, lang: str, inp: str = "") -> Dict[str, str]:
    """
    Executes the provided code in the specified language with the given input.

    Returns:
        A dictionary with the status and output.
    """
    # Validate language
    lang = parse_lang(lang)

    if lang is None:
        return {"status": "INVALID_LANGUAGE", "output": ""}

    compile_command: Optional[List[str]] = None

    code_hash = get_code_hash(code)

    if lang == "cpp":
        file_extension = ".cpp"
        source_file = temp_code_dir / f"{code_hash}{file_extension}"
        executable_file = temp_code_dir / f"{code_hash}{file_extension}.exe"

        compile_command = ['g++', source_file, '-static', '-DONLINE_JUDGE', '-O2', '-std=c++23',
                           '-Wl,--stack=268435456', '-lstdc++exp', '-march=x86-64', '-mno-avx2', '-o', executable_file]
        execute_command = [executable_file]

        # if os.path.exists(source_file) and os.path.exists(executable_file):
        if source_file.exists() and executable_file.exists():
            compile_command = None

    else:
        file_extension = ".py"
        source_file = temp_code_dir / f"{code_hash}{file_extension}"
        execute_command = ["python", source_file]

    with open(source_file, "w", encoding="utf-8") as f:
        f.write(code)

    # Compile the code if needed
    if compile_command:
        try:
            subprocess.run(
                compile_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=True
            )
        except subprocess.CalledProcessError as e:
            return {"status": "COMPILE_ERROR", "output": e.stderr.decode()}
        except Exception as e:
            return {"status": "COMPILE_ERROR", "output": str(e)}

    exec_time_lim = 20
    try:
        process = subprocess.run(
            execute_command,
            input=inp.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=exec_time_lim + 1,
        )

        # Check for runtime errors
        if process.returncode != 0:
            return {"status": "RUNTIME_ERROR",
                    "output": process.stderr.decode() or process.stdout.decode(),
                    "return_code": process.returncode}

        # Return successful output
        return {"status": "OK", "output": process.stdout.decode()}

    except subprocess.TimeoutExpired:
        return {"status": "TIME_LIMIT_EXCEEDED", "output": ""}
    except Exception as e:
        return {"status": "RUNTIME_ERROR", "output": str(e)}


def eval_sub(correct_sub: Submission, candidate_sub: Submission, inp: str, debug: bool = False) -> Tuple[bool, str]:
    """
    Evaluate the candidate submission against the correct submission.

    Returns:
        A tuple (is_correct, info_message) where is_correct indicates if outputs match,
        and info_message contains additional information.
    """
    try:
        candidate_run = run_code(candidate_sub["code"], candidate_sub["lang"], inp)
    except Exception as e:
        print("Error while executing candidate code:", e)
        return False, "Didn't get to compare outputs"
    if candidate_run["status"] != "OK":
        print("Error while executing candidate code:", candidate_run)
        return False, "Didn't get to compare outputs"

    try:
        correct_run = run_code(correct_sub["code"], correct_sub["lang"], inp)
    except Exception as e:
        raise Exception(f"Exception while executing correct code: {e}")
    if correct_run["status"] != "OK":
        raise Exception(f"Error while executing correct code: {correct_run}")

    if debug:
        print("jury output:", correct_run["output"])
        print("candidate output:", candidate_run["output"])

    return compare_outputs(correct_run["output"], candidate_run["output"])


def is_fail_case(problem_id: str, inp: str, runs_per_eval: int, debug: bool = False) -> Dict[str, Any]:
    """Check if the provided input is a failing test case for the given problem."""
    candidate_sub = get_wrong_sub(problem_id)
    correct_sub = get_correct_sub(problem_id)

    if debug:
        print("Candidate code:\n", candidate_sub["code"])
        print("Jury code:\n", correct_sub["code"])

    validator_result = run_code(dataset[problem_id]["validator"], "Python 3", inp)
    if validator_result["status"] != "OK":
        return {"success": False, "info": f"Validation failed: {validator_result}"}

    for _ in range(runs_per_eval):
        verdict = eval_sub(correct_sub, candidate_sub, inp, debug)
        if debug:
            print("Verdict:", verdict)
        if not verdict[0]:
            return {"success": True, "info": ""}

    return {"success": False, "info": "Buggy and correct codes agree"}


def save_to_file(sub: Submission, dir: str, name: str) -> str:
    """Save a submission to a file with correct extension and return the absolute file path."""
    lang = parse_lang(sub["lang"])
    if lang is None:
        raise ValueError("Invalid language")

    file_extension = ".cpp" if lang == "cpp" else ".py"
    source_file = Path(dir) / f"{name}{file_extension}"

    with open(source_file, "w", encoding="utf-8") as f:
        f.write(sub["code"])

    # return os.path.abspath(source_file)
    return str(source_file.resolve())


def run_randsearch(problem_id: str, brute_sub: Submission, gen_sub: Submission,
                   timeout: int, runs_per_eval: int) -> Union[Dict[str, Any], Tuple[bool, str]]:
    """
    Run randsearch until timeout.

    Returns:
        A dictionary with "success" indicating if a failing test case was found and
        "info" containing additional information.
    """
    test_path = (temp_code_dir / f"{get_code_hash(problem_id + brute_sub['code'] + gen_sub['code'])}.txt").resolve()
    with open(test_path, "w") as f:
        f.write("")

    wrong_sub = get_wrong_sub(problem_id)

    brute_file = save_to_file(brute_sub, temp_code_dir, get_code_hash(brute_sub["code"]))
    gen_file = save_to_file(gen_sub, temp_code_dir, get_code_hash(gen_sub["code"]))
    wrong_file = save_to_file(wrong_sub, temp_code_dir, get_code_hash(wrong_sub["code"]))

    script_path = (root_dir / "utils" / "stress.bat").resolve()
    process = subprocess.Popen(
        [script_path, gen_file, wrong_file, brute_file, test_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=temp_code_dir
    )

    try:
        stdout, stderr = process.communicate(timeout=timeout)

        # Check for runtime errors
        if process.returncode != 0:
            return False, process.stderr.decode() or process.stdout.decode()

        # Evaluate the stored test case
        with open(test_path, "r") as f:
            tc = f.read()

        assert len(tc) > 0, "Empty test case!!!"

        # print("Test case:", tc)
        verdict = is_fail_case(problem_id, tc, runs_per_eval)
        verdict["info"] = f"""
stdout::
{stdout.decode()}
stderr::
{stderr.decode()}
---
{verdict["info"]}"""

        return verdict
    except subprocess.TimeoutExpired:
        parent = psutil.Process(process.pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
        process.kill()

        return {"success": False, "info": "Search time limit exceeded"}
    except Exception as e:
        return {"success": False, "info": f"Exception in RandSearch: {e}"}
