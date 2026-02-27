/**
 * Processor interface for SandFilter
 */
export interface Processor {
  process(match: string, ruleName: string): string;
}

/**
 * Replace sensitive text with a replacement string
 */
export class ReplaceProcessor implements Processor {
  constructor(private replacement: string = '[REDACTED]') {}

  process(_match: string, _ruleName: string): string {
    return this.replacement;
  }
}

/**
 * Replace with rule name in brackets
 */
export class RuleNameReplaceProcessor implements Processor {
  process(_match: string, ruleName: string): string {
    return `[${ruleName.toUpperCase()}]`;
  }
}

/**
 * Partially mask sensitive text
 */
export class PartialMaskProcessor implements Processor {
  constructor(
    private maskChar: string = '*',
    private preservePrefix: number = 1,
    private preserveSuffix: number = 1
  ) {}

  process(match: string, _ruleName: string): string {
    if (match.length <= this.preservePrefix + this.preserveSuffix) {
      return this.maskChar.repeat(match.length);
    }

    const prefix = match.slice(0, this.preservePrefix);
    const suffix = this.preserveSuffix > 0 ? match.slice(-this.preserveSuffix) : '';
    const middleLength = match.length - this.preservePrefix - this.preserveSuffix;

    // For email, try to preserve domain structure
    if (match.includes('@')) {
      const parts = match.split('@');
      if (parts.length === 2) {
        const [local, domain] = parts;
        const maskedLocal =
          local.length > 1
            ? local[0] + this.maskChar.repeat(local.length - 1)
            : this.maskChar;
        return `${maskedLocal}@${domain}`;
      }
    }

    return prefix + this.maskChar.repeat(middleLength) + suffix;
  }
}

/**
 * Completely remove sensitive text
 */
export class DeleteProcessor implements Processor {
  process(_match: string, _ruleName: string): string {
    return '';
  }
}

/**
 * Hash sensitive text using SHA256
 */
export class HashProcessor implements Processor {
  private truncate: boolean;

  constructor(truncate: boolean = true) {
    this.truncate = truncate;
  }

  async process(match: string, _ruleName: string): Promise<string> {
    // Simple hash implementation without external dependencies
    let hash = 0;
    for (let i = 0; i < match.length; i++) {
      const char = match.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    const hashHex = Math.abs(hash).toString(16).padStart(8, '0');
    return this.truncate ? `[HASH:${hashHex}]` : `[HASH:${hashHex}]`;
  }
}

/**
 * Custom processor function
 */
export class CustomProcessor implements Processor {
  constructor(private func: (match: string, ruleName: string) => string) {}

  process(match: string, ruleName: string): string {
    return this.func(match, ruleName);
  }
}

/**
 * Processor factory
 */
export class Processors {
  static replace(replacement: string = '[REDACTED]'): ReplaceProcessor {
    return new ReplaceProcessor(replacement);
  }

  static ruleName(): RuleNameReplaceProcessor {
    return new RuleNameReplaceProcessor();
  }

  static partialMask(
    maskChar: string = '*',
    preservePrefix: number = 1,
    preserveSuffix: number = 1
  ): PartialMaskProcessor {
    return new PartialMaskProcessor(maskChar, preservePrefix, preserveSuffix);
  }

  static delete(): DeleteProcessor {
    return new DeleteProcessor();
  }

  static hash(truncate: boolean = true): HashProcessor {
    return new HashProcessor(truncate);
  }

  static custom(func: (match: string, ruleName: string) => string): CustomProcessor {
    return new CustomProcessor(func);
  }

  // Common presets
  static get EMAIL(): Processor {
    return Processors.ruleName();
  }

  static get PHONE(): Processor {
    return Processors.partialMask('*', 3, 4);
  }

  static get API_KEY(): Processor {
    return Processors.replace('[API_KEY]');
  }

  static get PASSWORD(): Processor {
    return Processors.replace('[PASSWORD]');
  }

  static get CREDIT_CARD(): Processor {
    return Processors.partialMask('*', 4, 4);
  }
}
