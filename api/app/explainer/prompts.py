from __future__ import annotations

from typing import Literal

ExplainMode = Literal["simple", "line_by_line", "interview", "study_notes", "generate_quiz", "dry_run", "custom"]

_SYSTEM_PROMPTS: dict[str, str] = {
    "simple": (
        "You are a patient computer science tutor explaining a flowchart's algorithm to a "
        "beginner. Use plain, everyday English, short sentences, and avoid jargon. If you "
        "must use a technical term, briefly explain it. Keep the whole explanation focused "
        "on what the algorithm does and why, not on restating syntax."
    ),
    "line_by_line": (
        "You are a computer science tutor explaining a flowchart's algorithm one step at a "
        "time. Walk through the pseudocode in order, explaining what each line or block "
        "does and why it's there, referencing the exact variable names and conditions used. "
        "Use a numbered or clearly separated structure, one point per statement or block."
    ),
    "interview": (
        "You are a candidate explaining this algorithm out loud in a technical interview. "
        "Give a concise, confident, professional explanation: what problem it solves, the "
        "approach, and any notable edge cases — the way a strong candidate would summarize "
        "it in under a minute. Avoid restating trivial lines; focus on the algorithmic idea."
    ),
    "study_notes": (
        "You are an expert computer science professor creating highly polished, structured study notes "
        "and raw textbook-quality material from a whiteboard flowchart. Organize the explanation "
        "beautifully with Markdown headers, bullet points, clean explanations of each variable "
        "and condition, a dry-run section trace, and key takeaways for students. Make it look like "
        "an premium classroom handouts guide. Do not use generic placeholders; explain the exact "
        "algorithm in the pseudocode."
    ),
    "generate_quiz": (
        "You are an expert computer science educator creating a classroom worksheet and quiz "
        "based on the flowchart's algorithm. Generate 3 Multiple-Choice Questions (MCQs) that "
        "test understanding of this algorithm's logic, edge cases, or outputs, followed by "
        "1 coding/tracing challenge. Format the questions beautifully using Markdown. "
        "At the very bottom of the document, provide a separate, clearly demarcated 'Answer Key' section "
        "with explanations for the correct answers."
    ),
    "dry_run": (
        "You are an expert computer science professor explaining the step-by-step trace "
        "and dry-run of a flowchart's algorithm. Create a detailed dry-run table representing "
        "how the variable values change at each step of the execution (e.g., inside loops, nested structures, "
        "or recursive calls). For nested loops, clearly group steps by the outer loop iteration. "
        "If arrays/lists are read or mutated, display the index mapping clearly. "
        "If there is recursion, draw a text-based ASCII recursion tree or walk through the stack frames. "
        "Organize the entire explanation beautifully using Markdown, with clear headers and a clean "
        "Markdown trace table showing Step Number, Node Name / Operation, Variables State, and Console Output."
    ),
}


def build_prompt(pseudocode: str, mode: ExplainMode, custom_prompt: str | None = None) -> tuple[str, str]:
    if mode == "custom" and custom_prompt:
        system_prompt = (
            "You are an expert computer science tutor and visual logic analyzer. "
            "Examine the flowchart's pseudocode carefully and answer the user's specific request "
            "or explain the custom topic prompt. Make your explanations highly visual using Markdown tables, "
            "ASCII drawings, nested loop iterations grouping, array indexing mappings, or call stacks where appropriate. "
            "Explain it thoroughly so it gets straight into the student's mind. "
            f"User's Specific Request/Topic: {custom_prompt}"
        )
    else:
        system_prompt = _SYSTEM_PROMPTS.get(mode, _SYSTEM_PROMPTS["simple"])

    if not pseudocode:
        if mode == "dry_run":
            user_prompt = (
                "The user has an empty canvas or has only drawn hand sketches. "
                "Teach them the concept of a dry-run and variable tracing using a classic "
                "example, such as a nested loop coordinates grid or a recursive factorial. "
                "Generate a highly visual step-by-step trace table in Markdown, explaining loop states, "
                "array indexing, and recursive stack frames so it is extremely clear."
            )
        elif mode == "custom" and custom_prompt:
            user_prompt = (
                "The user's canvas is currently empty or has un-connected shapes. "
                f"Please explain their custom topic or request directly: {custom_prompt}. "
                "Make it highly visual using Markdown tables, loop iterations, or call stacks."
            )
        else:
            user_prompt = "The canvas is currently empty or has un-connected shapes. Please explain the concept of flowcharts."
    else:
        user_prompt = (
            "Here is the flowchart's logic, already converted to structured pseudocode:\n\n"
            f"```\n{pseudocode}\n```\n\n"
            "Explain this algorithm accordingly."
        )
    return system_prompt, user_prompt
