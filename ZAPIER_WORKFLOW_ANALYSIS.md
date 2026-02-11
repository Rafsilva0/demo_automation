# Zapier Workflow Analysis: SE Demo Automation

## Complete Workflow Breakdown (28 Steps)

### **Step 13: Salesforce Trigger**
- **Action**: `updated_field_on_record`
- **Object**: Opportunity
- **Field**: StageName
- **Trigger Value**: "0. Qualified"
- **API**: SalesforceCLIAPI@2.26.4

### **Step 14: Delay**
- **Action**: `delay_for`
- **Duration**: 5 minutes
- **Purpose**: Wait before processing to ensure Salesforce data is stable

### **Step 15: Get Opportunity Info**
- **Action**: `find_record`
- **Object**: Opportunity
- **Search Field**: Id (Opportunity ID)
- **Search Value**: `{{=gives['348216369']['objectId']}}`
- **Returns**: Full opportunity record

### **Step 16: Filter - New Contract Only**
- **Action**: `filter`
- **Condition**: `Type` equals "New Contract" (exact match)
- **Purpose**: Only proceed for new customer contracts

### **Step 17: Get Account Name**
- **Action**: `find_record`
- **Object**: Account
- **Search Field**: Id
- **Search Value**: `{{=gives['348216369']['AccountId']}}`
- **Returns**: Account.Name, Account.Description

### **Step 18: Get Pre-sales Consultant**
- **Action**: `find_record`
- **Object**: User
- **Search Field**: Id
- **Search Value**: `{{=gives['348216371']['PreSales_Consultant']['c']}}`
- **Returns**: User.Email, User.Name

### **Step 19: Find Slack User**
- **Action**: `user_by_email`
- **Email**: `{{=gives['348216374']['Email']}}`
- **Purpose**: Get SC's Slack user ID for notifications
- **Returns**: Slack user.id, user.profile.first_name

### **Step 20: Create Bot Handle (JavaScript)**
- **Action**: Code (JavaScript)
- **Input**: `account_name` from Salesforce
- **Code**:
```javascript
return {
  clean_name: inputData.account_name
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, '') // keep only lowercase letters, numbers, hyphens
    + '-ai-agent-demo'
};
```
- **Output**: `clean_name` (e.g., "acmecorp-ai-agent-demo")

### **Step 21: Clone Bot**
- **Action**: Custom webhook POST
- **URL**: `https://scteam-demo.ada.support/api/clone`
- **Payload**:
```json
{
  "clone_secret": "nRk3zkYVe>@Khm?Q2dY8axrR.5ucqPGF",
  "new_handle": "{{clean_name}}",
  "email": "scteam@ada.support",
  "user_full_name": "Ada SC Team",
  "user_password": "Adalovelace123!",
  "type": "client"
}
```

### **Step 22: Send Slack Notification - Workflow Started**
- **Action**: `private_channel_message`
- **Channel**: C0A1R66J7LG (#sc-demo-automation)
- **Message**:
```
Hi there, I've now started building a demo for {{Account.Name}}. The SC working on this is {{SC.FirstName}}.
Bot handle is:
{{clean_name}}.ada.support.

Please make sure to send me an API Key so I can continue with my build.
```

### **Step 23: Collect API Key (Human-in-Loop)**
- **Action**: `collect_data`
- **Type**: Slack interaction
- **Timeout**: 28 days
- **Message to SC**:
```
Hey this is the url to access your AI Agent for your upcoming demo: {{clean_name}}.ada.support.
Use these credentials to log in:
Email: scteam@ada.support
Password: Adalovelace123!
Can you give me an API key please?
```
- **Collects**: `api_key` (text input)
- **Recipients**: U0229073EP5 (Rafa) + SC's Slack ID

### **Step 24: Create Knowledge Source**
- **Action**: Custom webhook POST
- **URL**: `https://{{clean_name}}.ada.support/api/v2/knowledge/sources/`
- **Headers**:
  - `Authorization: Bearer {{api_key}}`
  - `Content-Type: application/json`
- **Payload**:
```json
{
  "id": "demosource",
  "name": "Demo Knowledge Source"
}
```

### **Step 25: Create Company Description (OpenAI)**
- **Action**: `send_prompt`
- **Model**: gpt-3.5-turbo-instruct
- **Temperature**: 0.7
- **Prompt**:
```
You are an expert at making a company description for: {{Account.Name}}.
Here is a man made description: {{Account.Description}}. Make sure to cross reference yours with this manual one. It may give insight into the company.
Return a brief description about what the company does, who they service and the products they sell.
```

### **Step 26: Create Knowledge Articles (OpenAI)**
- **Action**: `send_prompt`
- **Model**: gpt-3.5-turbo-instruct
- **Temperature**: 0.5
- **Prompt**: (See detailed prompt in code - generates 10 FAQ articles as JSON array)
- **Output Format**: JSON array with 10 objects, each having:
  - `id`: "1" to "10"
  - `name`: Question-style title
  - `content`: 120-200 word answer
  - `knowledge_source_id`: "demosource"

### **Step 27: Upload KB Articles (JavaScript + Fetch)**
- **Action**: Code (JavaScript with fetch)
- **Method**: POST
- **URL**: `https://{{clean_name}}.ada.support/api/v2/knowledge/bulk/articles/`
- **Headers**: `Authorization: Bearer {{api_key}}`
- **Body**: Parsed JSON from Step 26
- **Error Handling**: Throws error with status code if failed

### **Step 28: Build 70 Questions (OpenAI)**
- **Action**: `send_prompt`
- **Model**: gpt-3.5-turbo-instruct
- **Temperature**: 0.7
- **Input**: Uses knowledge articles from Step 26 as context
- **Output**: JSON object with flat structure:
```json
{
  "question_1": "How can I...",
  "question_2": "What is...",
  ...
  "question_70": "When do..."
}
```

### **Step 29: Convert 70 Questions to Line Items (JavaScript)**
- **Action**: Code (JavaScript)
- **Purpose**: Parse JSON object and convert to arrays for looping
- **Output**:
  - `question[]`: Array of 70 question strings
  - `question_number[]`: Array of numbers 1-70
- **Features**: Deduplication, numeric sorting, validation

### **Step 30: Build Endpoints (OpenAI)**
- **Action**: `send_prompt`
- **Model**: gpt-3.5-turbo-instruct
- **Temperature**: 0.7
- **Input**: Company description from Step 25
- **Output**: JSON with Beeceptor rule objects for 2 endpoints:
```json
{
  "result": {
    "use_case_1_rule": {
      "enabled": true,
      "mock": true,
      "delay": 0,
      "match": {
        "method": "GET",
        "value": "/{{clean_name}}/status_check",
        "operator": "SW"
      },
      "send": {
        "status": 200,
        "body": "{...escaped JSON...}",
        "headers": {"Content-Type": "application/json"},
        "templated": false
      }
    },
    "use_case_2_rule": {...}
  }
}
```

### **Step 31: Split Endpoints (JavaScript)**
- **Action**: Code (JavaScript)
- **Purpose**: Extract rule1 and rule2 from OpenAI response
- **Output**:
  - `rule1`: JSON string of first Beeceptor rule
  - `rule2`: JSON string of second Beeceptor rule

### **Step 32: Create Endpoint #1 Beeceptor**
- **Action**: Custom webhook POST
- **URL**: `https://api.beeceptor.com/api/v1/endpoints/ada-demo/rules`
- **Headers**:
  - `Authorization: 3db584716ce6764c1004850ee20e610e470aee7cTnwDhrdgQaknDva`
  - `Content-Type: application/json`
- **Body**: `{{rule1}}`

### **Step 33: Create Endpoint #2 Beeceptor**
- **Action**: Custom webhook POST
- **URL**: `https://api.beeceptor.com/api/v1/endpoints/ada-demo/rules`
- **Headers**: Same as Step 32
- **Body**: `{{rule2}}`

### **Step 34: Create Channel (JavaScript + Fetch)**
- **Action**: Code (JavaScript with fetch)
- **Method**: POST
- **URL**: `https://{{clean_name}}.ada.support/api/v2/channels/`
- **Headers**: `Authorization: Bearer {{api_key}}`
- **Payload**:
```json
{
  "name": "Raf_Channel",
  "description": "A custom messaging channel for my AI Agent",
  "modality": "messaging"
}
```
- **Output**: `channel_id`

### **Step 35: Loop 70 Times**
- **Action**: `loop_values_line_items`
- **Iteration**: 1 to 70
- **Loop Values**:
  - `Question`: `{{question[]}}`
  - `Question Number`: `{{question_number[]}}`

### **Step 36: Create Conversation (JavaScript + Fetch)**
- **Action**: Code (JavaScript with fetch) - runs 70 times
- **Method**: POST
- **URL**: `https://{{clean_name}}.ada.support/api/v2/conversations/`
- **Headers**: `Authorization: Bearer {{api_key}}`
- **Payload**:
```json
{
  "channel_id": "{{channel_id}}"
}
```
- **Output**: `conversation_id`, `end_user_id`

### **Step 37: Create Message (JavaScript + Fetch)**
- **Action**: Code (JavaScript with fetch) - runs 70 times
- **Method**: POST
- **URL**: `https://{{clean_name}}.ada.support/api/v2/conversations/{{conversation_id}}/messages/`
- **Headers**: `Authorization: Bearer {{api_key}}`
- **Payload**:
```json
{
  "author": {
    "id": "{{end_user_id}}",
    "role": "end_user"
  },
  "content": {
    "body": "{{Question}}",
    "type": "text"
  }
}
```
- **Validation**: Checks for valid 24-char hex IDs

### **Step 38: Filter - Continue After Last Loop**
- **Action**: `filter`
- **Condition**: `loop_iteration_is_last` equals true
- **Purpose**: Only continue to final steps after all 70 iterations complete

### **Step 39: Send DM to SC**
- **Action**: `direct_message`
- **Recipient**: SC's Slack user ID
- **Message**:
```
Hi there {{SC.FirstName}}, I've now completed the set up for your new ai agent:
{{clean_name}}.ada.support.

Your checklist now involves:
- Set up the handoff integrations required
- Set up the persona settings
- Brand your agent
- Set up the actions I created for you in Ada - go here: https://app.beeceptor.com/console/ada-demo
- Add a playbook
```

### **Step 40: Send Message to Channel**
- **Action**: `private_channel_message`
- **Channel**: C0A1R66J7LG (#sc-demo-automation)
- **Message**: Same as Step 39

---

## Critical Configuration Details

### Salesforce Fields Used:
- **Opportunity**:
  - `Id` (objectId in trigger)
  - `Type` (must equal "New Contract")
  - `AccountId`
  - `PreSales_Consultant__c` (custom field)

- **Account**:
  - `Id`
  - `Name`
  - `Description`

- **User**:
  - `Id`
  - `Email`
  - `Name`

### Ada API Endpoints:
1. **Clone Bot**: `POST https://scteam-demo.ada.support/api/clone`
2. **Knowledge Sources**: `POST https://{{handle}}.ada.support/api/v2/knowledge/sources/`
3. **Bulk Articles**: `POST https://{{handle}}.ada.support/api/v2/knowledge/bulk/articles/`
4. **Channels**: `POST https://{{handle}}.ada.support/api/v2/channels/`
5. **Conversations**: `POST https://{{handle}}.ada.support/api/v2/conversations/`
6. **Messages**: `POST https://{{handle}}.ada.support/api/v2/conversations/{id}/messages/`

### Beeceptor Configuration:
- **Endpoint**: `ada-demo`
- **API Base**: `https://api.beeceptor.com/api/v1/endpoints/ada-demo/rules`
- **Auth Token**: `3db584716ce6764c1004850ee20e610e470aee7cTnwDhrdgQaknDva`

### Slack:
- **Channel ID**: C0A1R66J7LG (#sc-demo-automation)
- **Bot Username**: "SC Demo Automation"
- **Auth**: 66050dcf79427442d6b2cf606a8e422a5483704e5e8b860c494bac5976165c75

### OpenAI Configuration:
- **Model**: gpt-3.5-turbo-instruct
- **Temperatures**:
  - Company Description: 0.7
  - Knowledge Articles: 0.5
  - TK Questions: 0.7
  - Endpoints: 0.7

---

## Key Workflow Characteristics

1. **Human-in-Loop**: Step 23 requires manual API key input from SC
2. **Parallel Processing**: 70 conversations + messages created in loop
3. **Error Handling**: JavaScript steps include validation and error messages
4. **Idempotency**: Knowledge source uses fixed ID "demosource"
5. **Delays**: 5-minute initial delay, 3-minute queue delay in original workflow (removed in this version)
