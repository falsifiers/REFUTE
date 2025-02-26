from typing import Union

from refute.utils.get_dataset import get_dataset


def desc_problem(problem: dict[str, str]) -> str:
    """Takes a row from the dataset and returns the formatted problem description."""
    desc = ""
    if problem["statement"] is not None:
        desc += f"## Statement \n{problem['statement']}\n\n"

    # check if time_limit is int, and add if yes
    try:
        desc += f"Time Limit: {int(problem['time_limit'])}ms\n\n"
    except:
        pass

    try:
        desc += f"Memory Limit: {problem['memory_limit']} megabytes\n\n"
    except:
        pass

    if problem['input'] is not None:
        desc += f"## Input Format \n{problem['input']}\n\n"

    if problem['output'] is not None:
        desc += f"## Output Format \n{problem['output']}\n\n"

    if problem['example_input'] is not None:
        desc += f"## Example Input \n```\n{problem['example_input']}\n```\n\n"

    if problem['example_output'] is not None:
        desc += f"## Example Output \n```\n{problem['example_output']}\n```\n\n"

    if problem['note'] is not None:
        desc += f"## Note \n{problem['note']}\n\n"

    # replace $$$ with $$
    desc = desc.replace("$$$", "$$")

    return desc


def parse_lang(language: str) -> Union[str, bool]:
    """
    Validates if a programming language string from Codeforces API is either:
    1. Any variant of C++
    2. Any variant of Python >= 3 (including PyPy)

    Args:
        language (str): Programming language string from Codeforces API

    Returns:
        False if language is invalid, otherwise returns "cpp" or "python"
    """
    if not language:
        return False

    # Convert to lowercase for case-insensitive comparison
    lang = language.lower().strip()

    # Check for C++ variants
    if "c++" in lang or "cpp" in lang or "g++" in lang:
        return "cpp"

    # Check for Python 3+ variants
    if "python" in lang or "pypy" in lang:
        # Extract version number if present
        version = ""
        for char in lang:
            if char.isdigit() or char == ".":
                version += char

        # If no version found in PyPy, assume it's Python 3
        if "pypy" in lang and not version:
            return "python"

        # If version found, check if it's >= 3
        if version:
            try:
                major_version = float(version.split(".")[0])
                return "python" if major_version >= 3 else False
            except (ValueError, IndexError):
                return False

        # If no version number found and not PyPy, consider it invalid
        return False

    return False


dataset = get_dataset()


def get_wrong_sub(problem_id: str) -> dict[str, str]:
    task = dataset[problem_id]
    return {"code": task["wrong_code"], "lang": task["wrong_code_lang"]}


def get_correct_sub(problem_id: str) -> dict[str, str]:
    task = dataset[problem_id]
    correct_sub = {"code": task["correct_cpp"], "lang": "C++ 20"}
    if correct_sub["code"] is None:
        correct_sub = {"code": task["correct_python"], "lang": "Python 3"}
    return correct_sub
