---
name: calculator
description: Perform basic mathematical operations including addition, subtraction, multiplication, and division. Use when user needs to calculate numbers or perform arithmetic operations.
license: MIT
compatibility: Requires Python 3.9+
metadata:
  version: "1.0.0"
  author: Skill Service Team
  category: utility
---

# Calculator

## When to use this skill

Use this skill when:
- User needs to perform mathematical calculations
- User asks about sums, differences, products, or quotients
- User wants to add, subtract, multiply, or divide numbers

## How to use

### Parameters

- `operation` (required): Operation type - "add", "subtract", "multiply", or "divide"
- `a` (required): First operand (number)
- `b` (required): Second operand (number)

### Example

```bash
skill-service run calculator --param operation=add --param a=5 --param b=3
skill-service run calculator --param operation=multiply --param a=4 --param b=7
```

## Implementation

The skill supports four basic operations:
- **add**: Addition (a + b)
- **subtract**: Subtraction (a - b)
- **multiply**: Multiplication (a × b)
- **divide**: Division (a ÷ b), with zero-division protection
