# Course Requirement
Project (30%)
each student is expected to do a small project; this will be the re-implementation of or small improvement to the system that is described in the paper that they present


# Paper Assigned:
Nautilus: Fishing for Deep Bugs with Grammars

File: ./nautilus.pdf

# Email with professor:

## 1
Dear Professor Kruegel,

I hope you have a safe trip to the Bay Area.

For my course project, I propose to work on a re-implementation of the core system described in the paper I will be presenting (Nautilus: Fishing for Deep Bugs with Grammars). My goal is to develop a lightweight, grammar-aware fuzzing engine that reproduces the paper's key contributions, which is combining structured generation with code coverage feedback.

Specifically, I plan to implement a parser that handles Context-Free Grammars and maintains inputs as syntax trees rather than flat byte sequences. This will allow me to apply the structured mutation strategies highlighted in the paper, such as subtree replacement and recursive splicing, ensuring that mutated inputs remain syntactically valid. I will then connect this generator to a coverage feedback loop (likely using a lightweight instrumentation approach) to guide the fuzzer toward exploring new code paths.

To evaluate the project, I intend to benchmark my implementation against a naive grammar fuzzer (random generation without feedback) on a structured target, such as a JSON parser or a mathematical expression evaluator. I expect to demonstrate that the Nautilus-style coverage-guided approach significantly outperforms blind generation in finding unique paths.

Please let me know if this proposal meets the course expectations.

Best regards,

Zhen Zhang

## 2
Zhen,

	thanks for submitting your proposal. I like it but wanted to make two observations:

* Is there a specific reason why you want to re-implement the tool? Nautilus is available as open source. Are there specific difference / improvements that you have in mind? Why not building that into Nautilus directly.

* Overall, the project seems to be a lot of work. Are you confident that the scope is not too big?

Thanks.
Chris

## 3
Dear Professor Kruegel,  

I hope this email finds you well. My apologies for the delay in responding, as I was finalizing a submission for the ICML deadline.  

Thank you for your thoughtful feedback on my project proposal. I completely agree that a full re-implementation of Nautilus would be a considerable undertaking. To address your concerns and ensure the project is both feasible and meaningful, I have revised the scope and adopted a Baseline + Stretch Goals approach:

1. Baseline (Core Deliverables):
At a minimum, I will implement the core Tree Mutation Engine (subtree replacement and splicing) described in the paper. I will test this functionality on a synthetic target, such as a simple Python function with nested conditions that require specific grammar structures to trigger. This will allow me to demonstrate the core algorithm in action, along with its advantages over random input generation.

2. Stretch Goals (Time Permitting):
If time allows, I aim to extend the prototype by implementing more advanced features or testing on a real-world target. For example, I could attempt to fuzz a small JSON parser or explore grammar minimization techniques as described in the paper.

This flexible plan ensures that I can deliver the core functionality within the project timeline while leaving room to explore additional features if feasible.

Could you please confirm if this revised scope aligns with the course requirements?

Thank you again for your guidance, and I look forward to hearing your thoughts.

Best regards,

Zhen Zhang

## 4
Sounds good, thanks for the update.

Chris



## My requirement
read the paper
帮我 brainstorm 一下我应该如何完成课程任务
