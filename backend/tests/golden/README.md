# Golden Scenarios

Hand-verified test cases for the policy engine. Each scenario defines market conditions,
a strategy profile, and the **expected correct decision** — determined by a human applying
the policy rules before any code is written.

## Rules

- Write the scenario **before** implementing or changing the rule it tests.
- The `human_reasoning` field is mandatory — explain *why* this is the correct answer.
- If a code change causes a golden test to fail, the **code is wrong by default**.
- A golden scenario can only be changed with a documented justification in the commit message.

## Adding a scenario

Create a `.yaml` file in the appropriate subdirectory. Use the structure shown in the
existing scenarios as a template. The test runner in `tests/test_golden.py` loads all
`.yaml` files automatically.
