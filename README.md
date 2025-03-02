# REFUTE

_Official repository for the paper "Can Language Models Falsify? Evaluating Algorithmic Reasoning with Counterexample
Creation"._
<p align="center">
    <a href="https://arxiv.org/abs/2502.19414"><strong>Paper</strong></a> &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="https://falsifiers.github.io/"><strong>Home Page</strong></a> &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="https://huggingface.co/datasets/bethgelab/REFUTE"><strong>🤗 Dataset</strong></a>
</p>

REFUTE evaluates whether language models can reason about when code might fail.
Specifically, given a problem statement and an incorrect code, the task is to find a valid input on which the code fails
to produce the desired output.

This repository provides the evaluation environment along with simplified code from our paper to query models for
solutions.

## Installation

### Setting up the package

```bash
git clone https://github.com/falsifiers/REFUTE.git
cd REFUTE
pip install -e .
```

### Environment Variables

If you plan to query models, you need to set the following environment variables:

- `OPENROUTER_KEY`: Required for using OpenRouter models.
- `GOOGLE_API_KEY`: Required for using Gemini models.

## Evaluation

To evaluate your attempts, prepare a JSON file in the following format:

```json
[
  {
    "problem_id": "1975F",
    "method": "standard",
    "attempts": [
      {
        "generate_inp": {
          "code": "print(1)\nprint(\"0\")",
          "lang": "Python 3"
        }
      }
    ]
  }
]
```

The method can be either `standard`, `randsearch`, or `randsearch_oracle`. You probably only care about `standard`,
but feel free to refer to our paper for details about the other methods. Each problem can have multiple attempts, where
each `generate_inp` block contains a program that prints a counterexample to break the incorrect code.

For `randsearch` and `randsearch_oracle`, the outputs of `generate_inp` should (ideally) be randomised. `randsearch`
additionally requires a `solve_brute` field with a correct implementation in the same format as generate_inp. The lang
field should specify a valid Python or C++ version.

Evaluation results are stored in a JSON file with the following structure:

```json
[
  {
    "problem_id": "1975F",
    "verdicts": [
      {
        "success": true,
        "info": ""
      }
    ]
  }
]

```

Each attempt receives a verdict, where `success` is a boolean, and `info` may contain feedback like validation failure
or timeout. For example, to compute _pass@k_, pass _k_ attempts per problem and check if any succeed.

Here's the command to evaluate your attempts. You can run this from any directory. This will store the verdicts in
`results.json`. To change this and other params, feel free to use `--help`.

```bash
python -m refute.eval --pred_path PATH_TO_PREDICTIONS
```

## Querying Models

You can also use our existing prompts to query models. We currently support using any model through OpenRouter.
Make sure to set the relevant [environment variables](#environment-variables) before running the following command.

```bash
python -m refute.generate_preds --model MODEL_NAME --method few_shot
```

This writes the attempts to `preds.json`. Find more details about valid model and method names (along with other params)
using CLI help.

## Miscellaneous

- To speed up evaluation, compiled code is cached in `refute/tmp` after the first run.
- Make sure that your antivirus software (including Windows Defender) doesn't interfere with executions (atleast the
  harmless ones :D).
- The dataset includes exact language versions from Codeforces. To map them to simple `python` or `cpp` strings, use
  `parse_lang` from `refute/utils/dataset_parser.py`.

## Citation

```bibtex
@article{sinha2025falsify,
  title={Can Language Models Falsify? Evaluating Algorithmic Reasoning with Counterexample Creation},
  author={Sinha, Shiven and Goel, Shashwat and Kumaraguru, Ponnurangam and Geiping, Jonas and Bethge, Matthias and Prabhu, Ameya},
  journal={arXiv preprint arXiv:2502.19414},
  year={2025}
}
```
