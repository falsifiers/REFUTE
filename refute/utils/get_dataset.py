from datasets import load_dataset, load_from_disk
import refute
import os


def get_dataset():
    dataset = load_dataset("bethgelab/REFUTE", split="train")

    return {problem["problem_id"]:
                {k: v for k, v in problem.items() if k != "problem_id"}
            for problem in dataset}