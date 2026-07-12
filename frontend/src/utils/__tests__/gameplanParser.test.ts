import { parseLLMResponse, extractResponseText } from '../gameplanParser';

const RICH_RESPONSE = `
Here is my assessment of your case.

1. Case Analysis
Your situation involves a custody schedule dispute that the court can address through a Request for Order.

2. Legal Strategy
File an FL-300 requesting a modified visitation schedule with specific exchange times.

3. Forms
You will need FL-300 and FL-150.

4. Timeline
File within the next two weeks so a hearing can be set promptly.

5. Key Considerations
- Keep records of all missed exchanges
- The court prioritizes the children's best interests

6. Next Steps
1. Gather your existing court orders
2. Complete the FL-300
`;

describe('parseLLMResponse', () => {
  it('extracts sections and forms from a structured response', () => {
    const { data, isFallback } = parseLLMResponse(RICH_RESPONSE);

    expect(isFallback).toBe(false);
    expect(data.recommendedForms).toContain('FL-300');
    expect(data.recommendedForms).toContain('FL-150');
    expect(data.analysis).toMatch(/custody schedule dispute/i);
    expect(data.legalStrategy).toMatch(/FL-300 requesting/i);
    expect(data.keyConsiderations.length).toBeGreaterThan(0);
    expect(data.nextSteps.length).toBeGreaterThan(0);
  });

  it('flags unparseable output as fallback with honestly generic content', () => {
    const { data, isFallback } = parseLLMResponse('OK');

    expect(isFallback).toBe(true);
    expect(data.recommendedForms).toEqual(['FL-300']);
    // Fallback content must not masquerade as tailored analysis
    expect(data.analysis).toMatch(/couldn't|general/i);
    expect(data.nextSteps.length).toBeGreaterThan(0);
  });

  it('rejects an echoed prompt fragment instead of presenting it as analysis', () => {
    // The exact fragment the live LLM run rendered as the entire "Case
    // Analysis" section (real-LLM browser finding L10, flow2-05-gameplan.png)
    const echoedFragmentResponse = `
Case Analysis:
"Help me prepare a Form FL-410 (enforce the order)."
`;
    const { data, isFallback } = parseLLMResponse(echoedFragmentResponse);

    expect(isFallback).toBe(true);
    expect(data.analysis).not.toMatch(/help me prepare/i);
    expect(data.analysis).toMatch(/couldn't analyze/i);
  });

  it('still extracts real prose following a Case Analysis: header', () => {
    const response = `
Case Analysis:
Your situation involves repeated custody order violations that the court can enforce.
`;
    const { data, isFallback } = parseLLMResponse(response);

    expect(isFallback).toBe(false);
    expect(data.analysis).toMatch(/repeated custody order violations/i);
  });

  it('skips header-like candidate lines ending with a colon in favor of prose', () => {
    const response = `
1. Case Analysis
Detailed Background Assessment:
The parenting schedule has broken down because exchanges are being missed.
`;
    const { data } = parseLLMResponse(response);

    expect(data.analysis).toMatch(/parenting schedule has broken down/i);
  });
});

describe('extractResponseText', () => {
  it('unwraps plain strings, response wrappers, and data wrappers', () => {
    expect(extractResponseText('hello')).toBe('hello');
    expect(extractResponseText({ response: 'hello' })).toBe('hello');
    expect(extractResponseText({ response: { response: 'hello' } })).toBe('hello');
    expect(extractResponseText({ data: 'hello' })).toBe('hello');
  });

  it('reads message content from the real POST /chat/messages envelope', () => {
    // Shape recorded live in tasks/user-story-test-results.md (F3)
    const envelope = {
      success: true,
      message_id: '4aeb6129-2599-41d7-91e8-163d9681acaf',
      response: {
        success: true,
        message: {
          id: '4aeb6129-2599-41d7-91e8-163d9681acaf',
          content: RICH_RESPONSE,
          sender: 'assistant',
          quick_replies: [],
        },
      },
    };

    expect(extractResponseText(envelope)).toBe(RICH_RESPONSE);

    // The parser must see the content, not JSON envelope noise
    const { data, isFallback } = parseLLMResponse(extractResponseText(envelope));
    expect(isFallback).toBe(false);
    expect(data.recommendedForms).toContain('FL-300');
    expect(data.analysis).not.toMatch(/message_id|"success"/);
  });
});
