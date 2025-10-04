# MathML to TipTap + MathLive Conversion Plan

## Overview
Convert existing MathML content from mpcstudy.com to TipTap + MathLive format for enhanced interactive math editing and evaluation capabilities.

## Current State Analysis

### MathML Content Structure
- **Format**: Standard MathML with `xmlns="http://www.w3.org/1998/Math/MathML"`
- **Usage**: Embedded in HTML content within `que_en_desc`, `que_en_solution`, `que_en_answers`
- **Examples**:
  ```xml
  <math xmlns="http://www.w3.org/1998/Math/MathML">
    <mfrac><mrow><mn>180</mn><mo>°</mo></mrow><mn>2</mn></mfrac>
  </math>
  ```

### Content Distribution
- **Mathematics Problems**: ~80% contain MathML
- **Biology Problems**: ~15% contain basic math (percentages, ratios)
- **Physics Problems**: ~5% contain complex equations

## Conversion Strategy

### Phase 1: MathML Parser and Converter
```typescript
// mathml-converter.ts
interface MathMLNode {
  tag: string;
  attributes: Record<string, string>;
  children: (MathMLNode | string)[];
}

interface TipTapMathNode {
  type: 'mathLive';
  attrs: {
    value: string;
    readonly?: boolean;
    config?: Record<string, any>;
  };
}

class MathMLToTipTapConverter {
  // Convert MathML to LaTeX-like syntax for MathLive
  convertMathMLToLaTeX(mathml: string): string {
    // Implementation for common MathML patterns
  }
  
  // Convert to TipTap node structure
  convertToTipTapNode(mathml: string): TipTapMathNode {
    // Implementation for TipTap integration
  }
}
```

### Phase 2: TipTap + MathLive Integration
```typescript
// tiptap-math-extension.ts
import { Node } from '@tiptap/core';
import { MathLive } from 'mathlive';

export const MathLiveExtension = Node.create({
  name: 'mathLive',
  
  group: 'inline',
  inline: true,
  atom: true,
  
  addAttributes() {
    return {
      value: {
        default: '',
        parseHTML: element => element.getAttribute('data-value'),
        renderHTML: attributes => ({
          'data-value': attributes.value,
        }),
      },
      readonly: {
        default: false,
        parseHTML: element => element.getAttribute('data-readonly') === 'true',
        renderHTML: attributes => ({
          'data-readonly': attributes.readonly,
        }),
      },
    };
  },
  
  parseHTML() {
    return [
      {
        tag: 'span[data-type="mathlive"]',
      },
    ];
  },
  
  renderHTML({ HTMLAttributes }) {
    return ['span', HTMLAttributes];
  },
  
  addNodeView() {
    return ({ node, getPos, editor }) => {
      const container = document.createElement('span');
      container.setAttribute('data-type', 'mathlive');
      container.setAttribute('data-value', node.attrs.value);
      
      const mathField = new MathLive.MathField(container, {
        virtualKeyboardMode: 'manual',
        smartFence: true,
        smartSuperscript: true,
        removeExtraneousParentheses: true,
      });
      
      mathField.value = node.attrs.value;
      mathField.readOnly = node.attrs.readonly;
      
      return {
        dom: container,
        update: (updatedNode) => {
          if (updatedNode.type.name !== 'mathLive') return false;
          mathField.value = updatedNode.attrs.value;
          return true;
        },
      };
    };
  },
});
```

### Phase 3: Database Migration Script
```sql
-- Migration script to convert existing MathML content
CREATE OR REPLACE FUNCTION convert_mathml_to_tiptap()
RETURNS void AS $$
DECLARE
    question_record RECORD;
    converted_content JSONB;
    mathml_pattern TEXT;
    latex_content TEXT;
BEGIN
    -- Process each question with MathML content
    FOR question_record IN 
        SELECT id, que_en_desc, que_en_solution, que_en_answers
        FROM questions_enhanced 
        WHERE que_mathml_content IS NOT NULL
    LOOP
        -- Extract and convert MathML to LaTeX
        mathml_pattern := '<math[^>]*>.*?</math>';
        
        -- Convert MathML to LaTeX (simplified example)
        latex_content := regexp_replace(
            question_record.que_en_desc,
            mathml_pattern,
            '\\(' || extract_mathml_content('\1') || '\\)',
            'g'
        );
        
        -- Create TipTap document structure
        converted_content := jsonb_build_object(
            'type', 'doc',
            'content', jsonb_build_array(
                jsonb_build_object(
                    'type', 'paragraph',
                    'content', jsonb_build_array(
                        jsonb_build_object(
                            'type', 'text',
                            'text', latex_content
                        )
                    )
                )
            )
        );
        
        -- Update the question with converted content
        UPDATE questions_enhanced 
        SET que_tiptap_content = converted_content
        WHERE id = question_record.id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

## Implementation Steps

### Step 1: Setup TipTap + MathLive Environment
```bash
# Install required packages
npm install @tiptap/core @tiptap/starter-kit @tiptap/extension-math
npm install mathlive

# Create TipTap editor component
```

### Step 2: Create MathML Parser
```typescript
// mathml-parser.ts
export class MathMLParser {
  private static mathmlToLatexMap = {
    'mfrac': (node: MathMLNode) => `\\frac{${this.parseChildren(node.children[0])}}{${this.parseChildren(node.children[1])}}`,
    'msup': (node: MathMLNode) => `${this.parseChildren(node.children[0])}^{${this.parseChildren(node.children[1])}}`,
    'msub': (node: MathMLNode) => `${this.parseChildren(node.children[0])}_{${this.parseChildren(node.children[1])}}`,
    'mn': (node: MathMLNode) => node.children[0] as string,
    'mo': (node: MathMLNode) => this.convertOperator(node.children[0] as string),
    'mi': (node: MathMLNode) => node.children[0] as string,
  };
  
  static parseMathML(mathml: string): string {
    // Parse MathML and convert to LaTeX
  }
  
  private static convertOperator(op: string): string {
    const operatorMap: Record<string, string> = {
      '°': '^\\circ',
      '×': '\\times',
      '÷': '\\div',
      '±': '\\pm',
      '≤': '\\leq',
      '≥': '\\geq',
      '≠': '\\neq',
      '∞': '\\infty',
    };
    return operatorMap[op] || op;
  }
}
```

### Step 3: Create Question Editor Component
```typescript
// QuestionEditor.tsx
import { useEditor, EditorContent } from '@tiptap/react';
import { MathLiveExtension } from './tiptap-math-extension';

export const QuestionEditor: React.FC<{ question: QuestionResponse }> = ({ question }) => {
  const editor = useEditor({
    extensions: [
      StarterKit,
      MathLiveExtension,
    ],
    content: question.tiptap_content || question.description,
    editable: false, // For displaying questions
  });
  
  return (
    <div className="question-editor">
      <EditorContent editor={editor} />
    </div>
  );
};

export const AnswerEditor: React.FC<{ onSubmit: (answer: string) => void }> = ({ onSubmit }) => {
  const editor = useEditor({
    extensions: [
      StarterKit,
      MathLiveExtension,
    ],
    content: '',
    editable: true,
  });
  
  const handleSubmit = () => {
    const content = editor?.getJSON();
    onSubmit(JSON.stringify(content));
  };
  
  return (
    <div className="answer-editor">
      <EditorContent editor={editor} />
      <button onClick={handleSubmit}>Submit Answer</button>
    </div>
  );
};
```

### Step 4: Answer Evaluation System
```typescript
// answer-evaluator.ts
export class AnswerEvaluator {
  static evaluateMathAnswer(
    userAnswer: string, 
    correctAnswer: string, 
    tolerance: number = 0.01
  ): boolean {
    try {
      // Parse LaTeX expressions
      const userValue = this.parseLatexToNumber(userAnswer);
      const correctValue = this.parseLatexToNumber(correctAnswer);
      
      // Compare with tolerance
      return Math.abs(userValue - correctValue) < tolerance;
    } catch (error) {
      // Fallback to string comparison
      return this.normalizeAnswer(userAnswer) === this.normalizeAnswer(correctAnswer);
    }
  }
  
  private static parseLatexToNumber(latex: string): number {
    // Convert LaTeX to evaluable expression
    // Handle fractions, exponents, etc.
  }
  
  private static normalizeAnswer(answer: string): string {
    // Normalize for string comparison
    return answer.toLowerCase().replace(/\s+/g, '');
  }
}
```

## Migration Timeline

### Week 1-2: Foundation
- [ ] Setup TipTap + MathLive environment
- [ ] Create MathML parser
- [ ] Implement basic conversion functions

### Week 3-4: Integration
- [ ] Create TipTap extensions
- [ ] Build question editor components
- [ ] Implement answer evaluation system

### Week 5-6: Migration
- [ ] Run database migration script
- [ ] Test converted content
- [ ] Fix conversion issues

### Week 7-8: Testing & Optimization
- [ ] User testing with converted content
- [ ] Performance optimization
- [ ] Bug fixes and refinements

## Quality Assurance

### Testing Strategy
1. **Unit Tests**: Test MathML parser with various expressions
2. **Integration Tests**: Test TipTap + MathLive integration
3. **User Testing**: Test with actual students and teachers
4. **Performance Tests**: Ensure editor performance with large documents

### Validation
- **Math Accuracy**: Verify converted expressions are mathematically equivalent
- **Rendering Quality**: Ensure proper display across browsers
- **User Experience**: Test ease of input and editing

## Future Enhancements

### Advanced Features
- **Step-by-step Solutions**: Interactive solution walkthroughs
- **Graphing Calculator**: Integration with graphing capabilities
- **Voice Input**: Speech-to-math conversion
- **Collaborative Editing**: Real-time collaborative problem solving

### Accessibility
- **Screen Reader Support**: Proper ARIA labels for math content
- **Keyboard Navigation**: Full keyboard accessibility
- **High Contrast Mode**: Support for visual accessibility needs

## Success Metrics

### Technical Metrics
- **Conversion Accuracy**: >95% of MathML expressions converted correctly
- **Performance**: <200ms load time for math-heavy questions
- **Compatibility**: Works on 95% of target browsers

### User Experience Metrics
- **Input Speed**: 50% faster math input compared to traditional methods
- **Error Rate**: <5% input errors for common expressions
- **User Satisfaction**: >4.5/5 rating for math editing experience

This conversion plan provides a comprehensive roadmap for modernizing the math content experience in DreamSeedAI, enabling interactive problem-solving and enhanced learning outcomes.
