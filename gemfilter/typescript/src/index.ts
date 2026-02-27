/**
 * GemFilter - Privacy Protection Filter
 *
 * A lightweight, zero-dependency filter that detects and protects
 * sensitive information in text, like filtering gems from sand.
 * Perfect for privacy protection in LLM and AI applications.
 *
 * Usage:
 * import { SandFilter } from 'gemfilter';
 *
 * const sf = new SandFilter();
 * const result = sf.filter('My email is test@example.com');
 * console.log(result.text); // My email is [EMAIL]
 */

export { DetectionRule, createRule, getBuiltinRules, getBuiltinRule, BUILTIN_RULES } from './rules';
export { Processor, Processors, ReplaceProcessor, RuleNameReplaceProcessor, PartialMaskProcessor, DeleteProcessor, HashProcessor, CustomProcessor } from './processors';
export { SandFilter, FilterPipeline, FilterResult, Detection } from './filter';

export type { DetectionRule as Rule } from './rules';
export type { FilterResult as Result } from './filter';
