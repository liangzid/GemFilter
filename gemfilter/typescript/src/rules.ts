/**
 * Detection rule interface for SandFilter
 */
export interface DetectionRule {
  name: string;
  pattern: string;
  priority: number;
  sensitiveType: string;
  group: string;
  enabled: boolean;
  encryptable: boolean;
  description: string;
}

/**
 * Create a new detection rule
 */
export function createRule(options: Partial<DetectionRule> & { name: string; pattern: string }): DetectionRule {
  return {
    name: options.name,
    pattern: options.pattern,
    priority: options.priority ?? 100,
    sensitiveType: options.sensitiveType ?? 'general',
    group: options.group ?? 'default',
    enabled: options.enabled ?? true,
    encryptable: options.encryptable ?? false,
    description: options.description ?? '',
  };
}

// Built-in rules
export const BUILTIN_RULES: Record<string, DetectionRule> = {
  email: createRule({
    name: 'email',
    pattern: '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}',
    priority: 10,
    sensitiveType: 'contact',
    group: 'contact',
    encryptable: true,
    description: 'Email address',
  }),

  phone_cn: createRule({
    name: 'phone_cn',
    pattern: '1[3-9]\\d{9}',
    priority: 11,
    sensitiveType: 'contact',
    group: 'contact',
    encryptable: true,
    description: 'Chinese mobile phone number',
  }),

  phone_us: createRule({
    name: 'phone_us',
    pattern: '\\+?1?[-.\\s]?\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?\\d{4}',
    priority: 12,
    sensitiveType: 'contact',
    group: 'contact',
    encryptable: true,
    description: 'US phone number',
  }),

  id_card_cn: createRule({
    name: 'id_card_cn',
    pattern: '[1-9]\\d{5}(?:19|20)\\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\\d|3[01])\\d{3}[\\dXx]',
    priority: 5,
    sensitiveType: 'identification',
    group: 'identification',
    encryptable: true,
    description: 'Chinese ID card number',
  }),

  credit_card: createRule({
    name: 'credit_card',
    pattern: '\\d{4}[-\\s]?\\d{4}[-\\s]?\\d{4}[-\\s]?\\d{4}',
    priority: 3,
    sensitiveType: 'financial',
    group: 'financial',
    encryptable: true,
    description: 'Credit card number',
  }),

  password: createRule({
    name: 'password',
    pattern: '(?:password|passwd|pwd)[=:\\s]+[^\\s]{4,}',
    priority: 1,
    sensitiveType: 'security',
    group: 'security',
    encryptable: true,
    description: 'Password in key-value format',
  }),

  api_key: createRule({
    name: 'api_key',
    pattern: '(?:api[_-]?key|apikey)[=:\\s]+[a-zA-Z0-9_-]{20,}',
    priority: 1,
    sensitiveType: 'security',
    group: 'security',
    encryptable: true,
    description: 'API key',
  }),

  api_key_generic: createRule({
    name: 'api_key_generic',
    pattern: 'sk-[a-zA-Z0-9]{20,}',
    priority: 2,
    sensitiveType: 'security',
    group: 'security',
    encryptable: true,
    description: 'Generic API key (sk-...)',
  }),

  bearer_token: createRule({
    name: 'bearer_token',
    pattern: 'Bearer\\s+[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_-]+',
    priority: 2,
    sensitiveType: 'security',
    group: 'security',
    encryptable: true,
    description: 'Bearer token (JWT)',
  }),

  aws_access_key: createRule({
    name: 'aws_access_key',
    pattern: 'AKIA[0-9A-Z]{16}',
    priority: 1,
    sensitiveType: 'security',
    group: 'security',
    encryptable: true,
    description: 'AWS access key ID',
  }),

  ipv4: createRule({
    name: 'ipv4',
    pattern: '\\b(?:(?:25[0-5]|2[0-4]\\d|[01]?\\d\\d?)\\.){3}(?:25[0-5]|2[0-4]\\d|[01]?\\d\\d?)\\b',
    priority: 50,
    sensitiveType: 'network',
    group: 'network',
    encryptable: false,
    description: 'IPv4 address',
  }),

  ipv6: createRule({
    name: 'ipv6',
    pattern: '(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}',
    priority: 51,
    sensitiveType: 'network',
    group: 'network',
    encryptable: false,
    description: 'IPv6 address',
  }),

  mac_address: createRule({
    name: 'mac_address',
    pattern: '(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}',
    priority: 52,
    sensitiveType: 'network',
    group: 'network',
    encryptable: false,
    description: 'MAC address',
  }),

  url: createRule({
    name: 'url',
    pattern: 'https?://[^\\s<>\'"{}|\\\\^`\\[\\]]+',
    priority: 60,
    sensitiveType: 'network',
    group: 'network',
    encryptable: false,
    description: 'URL',
  }),
};

export function getBuiltinRules(): DetectionRule[] {
  return Object.values(BUILTIN_RULES);
}

export function getBuiltinRule(name: string): DetectionRule | undefined {
  return BUILTIN_RULES[name];
}
