# Hallucination and Failure Analysis Log

This document tracks instances of model hallucination, incorrect answers, and failure cases observed during testing.

## Format
Each entry should include:
- Problem ID and description
- Prompt type used
- Expected answer
- Model's response
- Type of failure
- Analysis of the cause
- Suggested improvements

## Observed Cases

### Case 1: Example Format
**Problem ID**: [ID]
**Problem**: [Description]
**Prompt Type**: [zero-shot/few-shot/cot/meta]
**Expected Answer**: [Correct answer]
**Model Response**: [What the model output]
**Failure Type**: [Hallucination/Wrong calculation/Misunderstanding/etc.]
**Analysis**: [Why did this failure occur?]
**Improvement Suggestions**: [How can we prevent this in future?]

## Common Patterns

### Types of Hallucinations Observed
1. Mathematical Rules
   - Inventing non-existent formulas
   - Misremembering mathematical properties

2. Calculation Errors
   - Intermediate step errors
   - Final answer discrepancies
   - Unit conversion mistakes

3. Reasoning Failures
   - Skipping logical steps
   - Making unfounded assumptions
   - Circular reasoning

## Prevention Strategies

1. Prompt Improvements
   - Add explicit verification steps
   - Include unit checking
   - Request step-by-step calculations

2. Model Constraints
   - Limit response length
   - Require formal mathematical notation
   - Enforce structured output format

3. Validation Techniques
   - Cross-check calculations
   - Verify formula usage
   - Test with edge cases

## Recommendations

1. Short-term Fixes
   - [List immediate actions]

2. Long-term Improvements
   - [List systematic changes needed]

## Statistics

- Total problems evaluated: [Number]
- Hallucination rate: [Percentage]
- Most common failure type: [Type]
- Best performing prompt type: [Type]
- Worst performing prompt type: [Type] 