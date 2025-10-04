# GPT MathML Conversion Prompt Template

## System Prompt
```
You are an expert mathematician and LaTeX specialist with deep knowledge of:
- Mathematical notation and symbols
- LaTeX syntax and best practices
- MathLive compatibility requirements
- Complex mathematical expressions (matrices, integrals, summations, etc.)

Your task is to convert MathML expressions to clean, valid LaTeX that works perfectly with MathLive.
```

## User Prompt Template
```
Convert the following MathML expression to MathLive-compatible LaTeX:

**MathML Input:**
```xml
{mathml_expression}
```

**Requirements:**
1. **Accuracy**: Preserve mathematical meaning exactly
2. **MathLive Compatibility**: Use only LaTeX commands supported by MathLive
3. **Formatting**: Choose appropriate display mode (\\[ \\] for complex, \\( \\) for simple)
4. **Clean Syntax**: Use proper LaTeX structure and spacing

**MathLive LaTeX Guidelines:**
- Fractions: `\frac{numerator}{denominator}`
- Superscripts: `^{exponent}`, Subscripts: `_{subscript}`
- Summations: `\sum_{i=1}^{n} expression`
- Integrals: `\int_{a}^{b} expression`
- Square roots: `\sqrt{expression}`
- Matrices: `\begin{matrix} ... \end{matrix}`
- Parentheses: `\left( ... \right)` for proper sizing
- Greek letters: `\alpha, \beta, \gamma, \delta, \epsilon, \theta, \lambda, \mu, \pi, \sigma, \tau, \phi, \omega`
- Operators: `\cdot` (multiplication), `\times` (cross product), `\pm` (plus-minus)
- Special symbols: `\infty` (infinity), `\partial` (partial derivative), `\nabla` (gradient)

**Output Format:**
Respond with a JSON object:
```json
{
    "latex": "converted LaTeX expression",
    "display_mode": true/false,
    "confidence": 0.0-1.0,
    "notes": "conversion notes or assumptions",
    "complexity": "simple/medium/complex"
}
```

**Examples:**

Input: `<math><mfrac><mn>1</mn><mn>2</mn></mfrac></math>`
Output: `{"latex": "\\frac{1}{2}", "display_mode": false, "confidence": 1.0, "notes": "Simple fraction", "complexity": "simple"}`

Input: `<math><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover><msup><mi>k</mi><mn>2</mn></msup></math>`
Output: `{"latex": "\\sum_{k=1}^{n} k^2", "display_mode": true, "confidence": 1.0, "notes": "Summation with limits", "complexity": "medium"}`

Input: `<math><mtable><mtr><mtd><mn>1</mn></mtd><mtd><mn>2</mn></mtd></mtr><mtr><mtd><mn>3</mn></mtd><mtd><mn>4</mn></mtd></mtr></mtable></math>`
Output: `{"latex": "\\begin{matrix} 1 & 2 \\\\ 3 & 4 \\end{matrix}", "display_mode": true, "confidence": 1.0, "notes": "2x2 matrix", "complexity": "medium"}`

Now convert the provided MathML expression:
```

## Quality Assurance Checklist

### Before Conversion:
- [ ] MathML is well-formed XML
- [ ] All required elements are present
- [ ] No missing closing tags

### During Conversion:
- [ ] Mathematical meaning preserved
- [ ] Proper LaTeX syntax used
- [ ] MathLive compatibility ensured
- [ ] Appropriate display mode selected
- [ ] Confidence level assessed

### After Conversion:
- [ ] LaTeX syntax is valid
- [ ] Expression renders correctly
- [ ] No missing symbols or operators
- [ ] Proper spacing and formatting
- [ ] Confidence level is appropriate

## Common MathML to LaTeX Mappings

| MathML Element | LaTeX Equivalent | Notes |
|----------------|------------------|-------|
| `<mfrac>` | `\frac{num}{den}` | Fractions |
| `<msup>` | `^{exp}` | Superscripts |
| `<msub>` | `_{sub}` | Subscripts |
| `<msubsup>` | `_{sub}^{exp}` | Subscript + superscript |
| `<msqrt>` | `\sqrt{expr}` | Square root |
| `<mroot>` | `\sqrt[n]{expr}` | nth root |
| `<munderover>` | `\sum_{i=1}^{n}` | Summations, integrals |
| `<mtable>` | `\begin{matrix}...\end{matrix}` | Matrices |
| `<mtr>` | `... \\` | Matrix rows |
| `<mtd>` | `... &` | Matrix cells |
| `<mi>` | `variable` | Identifiers |
| `<mn>` | `number` | Numbers |
| `<mo>` | `operator` | Operators |
| `<mtext>` | `\text{text}` | Text |
| `<mspace>` | `\quad` | Spacing |

## Error Handling

### Common Issues:
1. **Malformed MathML**: Report error, suggest correction
2. **Unsupported elements**: Use closest LaTeX equivalent
3. **Complex expressions**: Break down into simpler parts
4. **Ambiguous notation**: Add clarifying notes

### Error Response Format:
```json
{
    "latex": "",
    "display_mode": false,
    "confidence": 0.0,
    "notes": "Error: [description of issue]",
    "complexity": "error"
}
```

## Testing and Validation

### Test Cases:
1. Simple fractions: `1/2`, `x/y`
2. Complex fractions: `(x+1)/(x-1)`
3. Superscripts/subscripts: `x^2`, `a_n`
4. Summations: `∑(k=1 to n) k^2`
5. Integrals: `∫(a to b) f(x)dx`
6. Matrices: 2x2, 3x3 matrices
7. Roots: `√x`, `∛x`
8. Greek letters: `α`, `β`, `γ`
9. Special functions: `sin`, `cos`, `log`
10. Complex expressions: Combinations of above

### Validation Steps:
1. Check LaTeX syntax validity
2. Verify mathematical meaning
3. Test MathLive rendering
4. Confirm display mode appropriateness
5. Assess confidence level accuracy
