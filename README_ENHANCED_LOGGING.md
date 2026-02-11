# Enhanced Step-by-Step Logging

## Overview

The provisioning tool now includes comprehensive step-by-step logging that shows users exactly what's happening at each phase and sub-step of the workflow. This makes it easy to track progress and debug issues.

## Logging Features

### 1. **Timestamps on All Messages**
Every log message includes a timestamp in `[HH:MM:SS]` format:
```
[14:23:45] 🚀 Starting Ada Agent Provisioning...
[14:23:46] ✅ Bot handle: pepsi-ai-agent-demo
```

### 2. **Hierarchical Logging**
Main phases are shown as headers, with sub-steps indented underneath:
```
📝 PHASE 1: Bot Handle Generation
[14:23:45] ✅ Bot handle: pepsi-ai-agent-demo

🔄 PHASE 2: Bot Cloning
[14:23:46]   └─ 2.1 Calling Ada clone API endpoint...
[14:23:46]   └─ Target bot handle: pepsi-ai-agent-demo
[14:23:47]   └─ Using scteam@ada.support credentials
[14:23:48] ✅ Bot cloned successfully
[14:23:48]   └─ 2.2 Waiting 30 seconds for Ada to provision the new bot...
```

### 3. **Color-Coded Status**
- 🟢 **Green**: Success messages (`✅`)
- 🟡 **Yellow**: Warnings (`⚠️`)
- 🔴 **Red**: Errors (`❌`)
- 🔵 **Cyan**: In-progress updates (`🎭`, `⏳`, `🤖`)

### 4. **Progress Indicators**
For long-running operations, you'll see:
- Iteration counters: `[15/70] Creating conversation...`
- Time estimates: `(this will take ~35s)`
- Completion percentages

## Detailed Phase Breakdown

### Phase 1: Bot Handle Generation
- **What it does**: Converts company name to a clean bot handle
- **Logging**: Shows the generated handle
- **Example**: `pepsi-ai-agent-demo`

### Phase 2: Bot Cloning
**Sub-steps:**
- `2.1` - Calling Ada clone API endpoint
- `2.2` - Waiting for bot provisioning (30 seconds)

**What to watch for:**
- HTTP 500 is expected and doesn't mean failure
- The 30-second wait is necessary for Ada's infrastructure

### Phase 3: API Key Retrieval (Playwright)
**Sub-steps:**
- `3.1` - Launching Chromium browser
- `3.2` - Navigating to login page
- `3.3` - Filling login credentials
- `3.4` - Navigating to /platform/apis
- `3.5` - Closing modal dialogs
- `3.6` - Clicking 'New API Key' button
- `3.7` - Filling API key name
- `3.8` - Clicking 'Generate key' button
- `3.9` - Waiting for key generation (5-15 seconds)
- `3.10` - Extracting API key using multiple strategies

**What to watch for:**
- Browser window will open (headless=False for debugging)
- Screenshot saved to `/tmp/ada_api_key_*.png` for debugging
- Multiple extraction methods tried (text search, DOM search, deep search)

### Phase 4: Knowledge Base Creation
**Sub-steps:**
- `4.1` - Creating knowledge source in Ada
- `4.2` - Generating AI company description
- `4.3` - Generating N knowledge articles using Claude AI (30-60 seconds)
- `4.4` - Uploading articles to Ada knowledge base

**What to watch for:**
- Article generation may take 30-60 seconds depending on count
- Sample article shown in logs for verification

### Phase 5: Question Generation
**Sub-steps:**
- `5.1` - Preparing context from knowledge articles
- `5.2` - Calling Claude AI to generate questions
- `5.3` - Parsing and cleaning Claude response

**What to watch for:**
- Shows context length (total characters from articles)
- Shows sample question for verification

### Phase 6: Beeceptor Endpoint Creation
**Sub-steps:**
- `6.1` - Generating mock API endpoint configurations
- `6.2` - Parsing Claude response and extracting rules
- `6.3` - Posting rule #1 to Beeceptor API (GET /status_check)
- `6.4` - Posting rule #2 to Beeceptor API (POST /account_update)

**What to watch for:**
- Shows Beeceptor console URL at end

### Phase 7: Conversations Creation
**Sub-steps:**
- `7.1` - Creating messaging channel in Ada
- `7.2` - Creating N conversations (with time estimate)

**What to watch for:**
- Each conversation logged: `[15/70] Creating conversation: "How do I..."`
- Progress updates every 10 conversations
- Total time estimate shown upfront

## Sample Output

Here's what a complete provisioning run looks like:

```
================================================================================
🚀 ADA AGENT PROVISIONING
================================================================================

Company: Pepsi
Started: 2026-02-10 14:23:45

[14:23:45] ✓ Anthropic API key: sk-ant-api03-r...
================================================================================
📝 PHASE 1: Bot Handle Generation
================================================================================

[14:23:45] ✅ Bot handle: pepsi-ai-agent-demo

================================================================================
🔄 PHASE 2: Bot Cloning
================================================================================

[14:23:46]   └─ 2.1 Calling Ada clone API endpoint...
[14:23:46]   └─ Target bot handle: pepsi-ai-agent-demo
[14:23:46]   └─ Using scteam@ada.support credentials
[14:23:48] ✅ Bot cloned successfully
[14:23:48]   └─ 2.2 Waiting 30 seconds for Ada to provision the new bot...
[14:24:18]   └─ This allows Ada's infrastructure to complete the cloning process

================================================================================
🎭 PHASE 3: API Key Retrieval
================================================================================

[14:24:18]   └─ 3.1 Launching Chromium browser (headless=False for debugging)...
[14:24:19]   └─ This will open a visible browser window
[14:24:20]   └─ 3.2 Navigating to login page: pepsi-ai-agent-demo.ada.support
[14:24:22]   └─ 3.3 Filling login credentials and submitting form...
[14:24:25]   └─ 3.4 Navigating to /platform/apis page...
[14:24:27]   └─ 3.5 Closing any modal dialogs...
[14:24:27]   └─ No modals to close
[14:24:27]   └─ 3.6 Clicking 'New API Key' button...
[14:24:28]   └─ 3.7 Filling API key name: 'automation-key'
[14:24:29]   └─ 3.8 Clicking 'Generate key' button...
[14:24:29]   └─ 3.9 Waiting for API key to be generated (may take 5-15 seconds)...
[14:24:35] ✓ API key modal appeared successfully
[14:24:37]   └─ Debug screenshot saved: /tmp/ada_api_key_pepsi-ai-agent-demo.png
[14:24:37]   └─ 3.10 Extracting API key from page using multiple strategies...
[14:24:37]   └─ Method 1: Searching page text for hex pattern...
[14:24:37] ✅ API key retrieved successfully: abc95e63628c...ed20
[14:24:37]   └─ Full key length: 32 characters

================================================================================
📚 PHASE 4: Knowledge Base Creation
================================================================================

[14:24:38]   └─ 4.1 Creating knowledge source in Ada...
[14:24:39] ✅ Knowledge source created
[14:24:39]   └─ 4.2 Generating AI company description for Pepsi...
[14:24:45] ✅ Company description generated (247 chars)
[14:24:45]   └─ 4.3 Generating 10 knowledge articles using Claude AI...
[14:24:45]   └─ This may take 30-60 seconds depending on the number of articles...
[14:25:32] ✅ Generated 10 articles
[14:25:32]   └─ 4.4 Uploading 10 articles to Ada knowledge base...
[14:25:32]   └─ Using bulk upload API endpoint...
[14:25:34] ✅ Uploaded 10 articles

================================================================================
❓ PHASE 5: Question Generation
================================================================================

[14:25:34]   └─ 5.1 Preparing context from 10 knowledge articles...
[14:25:34]   └─ Context length: 1847 characters
[14:25:34]   └─ 5.2 Calling Claude AI to generate 70 questions...
[14:25:34]   └─ Using temperature=0.7 for creative variation
[14:26:18]   └─ 5.3 Parsing and cleaning Claude response...
[14:26:18] ✅ Generated 70 questions
[14:26:18]   └─ Sample: "How do I set up automatic bill pay for my Pepsi account?"

================================================================================
📡 PHASE 6: Beeceptor Endpoint Creation
================================================================================

[14:26:18]   └─ 6.1 Generating mock API endpoint configurations using Claude AI...
[14:26:18]   └─ Creating 2 mock endpoints for: pepsi-ai-agent-demo
[14:26:25]   └─ 6.2 Parsing Claude response and extracting rules...
[14:26:25]   └─ 6.3 Posting rule #1 to Beeceptor API (GET /status_check)...
[14:26:26]   └─ 6.4 Posting rule #2 to Beeceptor API (POST /account_update)...
[14:26:27] ✅ Created 2 Beeceptor endpoints
[14:26:27]   └─ View at: https://app.beeceptor.com/console/ada-demo

================================================================================
💬 PHASE 7: Conversations Creation
================================================================================

[14:26:27]   └─ 7.1 Creating messaging channel in Ada...
[14:26:28] ✅ Channel created: 674a9e1f8c3b2d001a5e7f42
[14:26:28]   └─ 7.2 Creating 70 conversations (this will take ~35s)...
[14:26:28]   └─ Each conversation = 1 new conversation + 1 end-user message
[14:26:29]   └─ [1/70] Creating conversation: "How do I set up automatic..."
[14:26:30]   └─ [2/70] Creating conversation: "What payment methods does..."
[14:26:31]   └─ [3/70] Creating conversation: "Can I update my account..."
...
[14:26:59]   └─ [70/70] Creating conversation: "How do I contact customer..."
[14:27:03] ✅ Created 70 conversations

================================================================================
🎉 PROVISIONING COMPLETE!
================================================================================
📋 Summary:
   • Company: Pepsi
   • Bot Handle: pepsi-ai-agent-demo
   • Bot URL: https://pepsi-ai-agent-demo.ada.support
   • API Key: abc95e63628c...ed20
   • Knowledge Articles: 10
   • Questions Generated: 70
   • Conversations Created: 70/70
   • Channel ID: 674a9e1f8c3b2d001a5e7f42
   • Duration: 198.5 seconds
   • Beeceptor: https://app.beeceptor.com/console/ada-demo

================================================================================
```

## Debugging Tips

### 1. **Check Timestamps**
If a phase takes much longer than expected, check the timestamps to identify where the delay occurred.

### 2. **Screenshot Analysis**
When Playwright fails to extract the API key, check the screenshot:
```bash
open /tmp/ada_api_key_<bot-handle>.png
```

### 3. **Progress Tracking**
For long-running operations (articles, questions, conversations), you'll see:
- Initial estimate: `(this will take ~35s)`
- Periodic updates: `[10/70] conversations created`
- Final count: `Created 70 conversations`

### 4. **Error Messages**
All errors include:
- Timestamp of when it occurred
- Phase and sub-step where it failed
- Specific error message
- Suggestions for next steps

## Web UI Integration

The enhanced logging also works through the web UI. When you submit a provisioning job through the browser, the detailed logs are:

1. **Stored server-side** in the job status
2. **Polled by the frontend** every 2 seconds
3. **Displayed in real-time** in the status card

This means you can monitor progress in the browser just like you would in the terminal.

## Performance Notes

The enhanced logging adds minimal overhead:
- **~1ms per log statement** (negligible)
- **No impact on Claude API calls** (logging happens after)
- **No impact on Ada API calls** (logging happens around them)

Total execution time remains the same as before.

## Future Enhancements

Potential improvements to logging:
- [ ] Log levels (DEBUG, INFO, WARN, ERROR)
- [ ] Structured logging (JSON format for parsing)
- [ ] Log file output (not just console)
- [ ] Progress bars instead of text updates
- [ ] Slack notifications at each phase
- [ ] Email reports with logs attached
