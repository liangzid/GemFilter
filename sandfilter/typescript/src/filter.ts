import { DetectionRule, BUILTIN_RULES, getBuiltinRules } from './rules';
import { Processor, RuleNameReplaceProcessor } from './processors';

export interface Detection {
  ruleName: string;
  match: string;
  start: number;
  end: number;
  sensitiveType: string;
  replacement: string;
}

export interface FilterResult {
  text: string;
  detections: Detection[];
  summary: Record<string, number>;
}

export class FilterPipeline {
  private rules: DetectionRule[] = [];
  private ruleToProcessor: Map<string, Processor> = new Map();
  private compiledPatterns: Map<string, RegExp> = new Map();

  addRule(rule: DetectionRule, processor?: Processor): FilterPipeline {
    this.rules.push(rule);

    if (!processor) {
      processor = new RuleNameReplaceProcessor();
    }

    this.ruleToProcessor.set(rule.name, processor);
    this.compiledPatterns.set(rule.name, new RegExp(rule.pattern, 'g'));

    return this;
  }

  setProcessor(ruleName: string, processor: Processor): FilterPipeline {
    this.ruleToProcessor.set(ruleName, processor);
    return this;
  }

  getProcessor(ruleName: string): Processor | undefined {
    return this.ruleToProcessor.get(ruleName);
  }

  process(text: string): FilterResult {
    const detections: Detection[] = [];
    let resultText = text;

    // Sort rules by priority
    const sortedRules = [...this.rules].sort((a, b) => a.priority - b.priority);

    for (const rule of sortedRules) {
      if (!rule.enabled) continue;

      const pattern = this.compiledPatterns.get(rule.name);
      if (!pattern) continue;

      const processor = this.ruleToProcessor.get(rule.name);
      if (!processor) continue;

      // Reset regex lastIndex
      pattern.lastIndex = 0;

      // Find all matches
      let match: RegExpExecArray | null;
      while ((match = pattern.exec(resultText)) !== null) {
        const matchedText = match[0];
        const replacement = processor.process(matchedText, rule.name);

        const detection: Detection = {
          ruleName: rule.name,
          match: matchedText,
          start: match.index,
          end: match.index + matchedText.length,
          sensitiveType: rule.sensitiveType,
          replacement,
        };
        detections.push(detection);

        // Replace in text
        resultText =
          resultText.slice(0, match.index) +
          replacement +
          resultText.slice(match.index + matchedText.length);
      }
    }

    // Build summary
    const summary: Record<string, number> = {};
    for (const d of detections) {
      summary[d.ruleName] = (summary[d.ruleName] || 0) + 1;
    }

    return { text: resultText, detections, summary };
  }

  getRules(): DetectionRule[] {
    return [...this.rules];
  }

  enableRule(ruleName: string, enabled: boolean = true): FilterPipeline {
    for (const rule of this.rules) {
      if (rule.name === ruleName) {
        rule.enabled = enabled;
      }
    }
    return this;
  }

  disableRule(ruleName: string): FilterPipeline {
    return this.enableRule(ruleName, false);
  }
}

export class SandFilter {
  private pipeline: FilterPipeline;
  private defaultProcessor: Processor;

  constructor(defaultProcessor?: Processor) {
    this.pipeline = new FilterPipeline();
    this.defaultProcessor = defaultProcessor || new RuleNameReplaceProcessor();
    this.loadBuiltinRules();
  }

  private loadBuiltinRules(): void {
    const builtin = getBuiltinRules();
    for (const rule of builtin) {
      this.pipeline.addRule(rule, this.defaultProcessor);
    }
  }

  filter(text: string): FilterResult {
    return this.pipeline.process(text);
  }

  addRule(rule: DetectionRule, processor?: Processor): SandFilter {
    this.pipeline.addRule(rule, processor || this.defaultProcessor);
    return this;
  }

  setProcessor(ruleName: string, processor: Processor): SandFilter {
    this.pipeline.setProcessor(ruleName, processor);
    return this;
  }

  enableRules(...ruleNames: string[]): SandFilter {
    for (const name of ruleNames) {
      this.pipeline.enableRule(name, true);
    }
    return this;
  }

  disableRules(...ruleNames: string[]): SandFilter {
    for (const name of ruleNames) {
      this.pipeline.disableRule(name);
    }
    return this;
  }

  enableGroup(group: string): SandFilter {
    for (const rule of this.pipeline.getRules()) {
      if (rule.group === group) {
        rule.enabled = true;
      }
    }
    return this;
  }

  disableGroup(group: string): SandFilter {
    for (const rule of this.pipeline.getRules()) {
      if (rule.group === group) {
        rule.enabled = false;
      }
    }
    return this;
  }

  getEnabledRules(): string[] {
    return this.pipeline.getRules()
      .filter(r => r.enabled)
      .map(r => r.name);
  }

  getDisabledRules(): string[] {
    return this.pipeline.getRules()
      .filter(r => !r.enabled)
      .map(r => r.name);
  }
}
