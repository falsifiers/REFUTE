from typing import List, Tuple


class AdaptiveChecker:
    @staticmethod
    def _tokenize(output: str) -> List[str]:
        """Convert output string into tokens, handling whitespace properly."""
        # Remove trailing whitespace from each line and empty lines
        lines = [line.rstrip() for line in output.splitlines() if line.strip()]
        # Join lines with spaces and split into tokens
        return ' '.join(lines).split()

    @classmethod
    def _is_yes(cls, token: str) -> bool:
        """Check if a token is equivalent to YES."""
        return token.lower() == "yes"

    @classmethod
    def _is_no(cls, token: str) -> bool:
        """Check if a token is equivalent to NO."""
        return token.lower() == "no"

    @classmethod
    def _is_yes_no_output(cls, tokens: List[str]) -> bool:
        """
        Determine if the output appears to be a YES/NO problem.
        Returns True if all tokens are valid YES/NO variants.
        """
        if not tokens:
            return False
        return all(cls._is_yes(token) or cls._is_no(token) for token in tokens)

    @classmethod
    def _check_yes_no(cls, jury_tokens: List[str], contestant_tokens: List[str]) -> Tuple[bool, str]:
        """Compare outputs for YES/NO problem."""
        if len(jury_tokens) != len(contestant_tokens):
            return False, f"Expected {len(jury_tokens)} answers, but found {len(contestant_tokens)}"

        for i, (jury, contestant) in enumerate(zip(jury_tokens, contestant_tokens)):
            if not (cls._is_yes(contestant) or cls._is_no(contestant)):
                return False, f"Token {i + 1}: Expected YES/NO, found '{contestant}'"

            jury_is_yes = cls._is_yes(jury)
            contestant_is_yes = cls._is_yes(contestant)

            if jury_is_yes != contestant_is_yes:
                return False, f"Token {i + 1}: Expected {'YES' if jury_is_yes else 'NO'}, found '{contestant}'"

        return True, "OK"

    @classmethod
    def _check_typical(cls, jury_tokens: List[str], contestant_tokens: List[str]) -> Tuple[bool, str]:
        """Compare outputs for typical problems (exact match required)."""
        if len(jury_tokens) != len(contestant_tokens):
            return False, f"Expected {len(jury_tokens)} tokens, but found {len(contestant_tokens)}"

        for i, (jury, contestant) in enumerate(zip(jury_tokens, contestant_tokens)):
            if jury != contestant:
                return False, f"Token {i + 1}: Expected '{jury}', found '{contestant}'"

        return True, "OK"

    @classmethod
    def check(cls, jury_output: str, contestant_output: str) -> Tuple[bool, str]:
        """
        Compare two outputs, automatically detecting YES/NO problems.

        Args:
            jury_output (str): The jury's correct output
            contestant_output (str): The contestant's output

        Returns:
            Tuple[bool, str]: (is_correct, message)
                is_correct: True if outputs match according to rules
                message: Detailed explanation if outputs don't match
        """
        # Handle empty outputs
        if not jury_output.strip() and not contestant_output.strip():
            return True, "OK"

        if not jury_output.strip():
            return False, "Expected empty output"

        if not contestant_output.strip():
            return False, "Contestant's output is empty"

        # Tokenize both outputs
        jury_tokens = cls._tokenize(jury_output)
        contestant_tokens = cls._tokenize(contestant_output)

        # Detect if this is a YES/NO problem based on jury output
        if cls._is_yes_no_output(jury_tokens):
            return cls._check_yes_no(jury_tokens, contestant_tokens)
        else:
            return cls._check_typical(jury_tokens, contestant_tokens)


def compare_outputs(jury: str, contestant: str) -> Tuple[bool, str]:
    """Convenience function to check outputs."""
    return AdaptiveChecker.check(jury, contestant)
