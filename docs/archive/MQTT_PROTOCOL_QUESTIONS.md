# MQTT Protocol Questions for Collaborating Company

## 📬 Contact Information
**To**: [Robot/Fryer Control Team]
**From**: AI Development Team (Jetson Integration)
**Date**: 2025-10-31
**Subject**: MQTT Protocol Specification for Stir-Fry Monitoring Integration

---

## 🎯 Background

We are integrating AI-based stir-fry monitoring on Jetson Orin Nano. We received your C# MQTT example code and understand the basic structure:
- MQTT Broker: Port 1883
- QoS: 2 (Exactly Once)
- Format: JSON
- Topics: `AI/FryInfo`, `HR/Status`, etc.

We need clarification on the exact message format to complete our implementation.

---

## ❓ Questions

### 1. MQTT Topic Names

**Q1.1**: What **exact topic name** will you publish **fryer recipe data** (food type, target temp, cooking time)?
- [ ] `HR/FryRecipe`
- [ ] `HR/Recipe`
- [ ] `HR/Status` (combined with status)
- [ ] Other: _______________

**Q1.2**: What **exact topic name** will you publish **real-time fryer status** (current temp, cooking state)?
- [ ] `HR/FryStatus`
- [ ] `HR/Status`
- [ ] `HR/Fryer`
- [ ] Other: _______________

**Q1.3**: Are recipe and status sent on **separate topics** or **same topic**?
- [ ] Separate topics (recipe on one, status on another)
- [ ] Same topic (all data in one message)

**Q1.4**: Should we subscribe to any other topics? If yes, which ones?
```
[ ] HR/_______________
[ ] HR/_______________
[ ] Other: _______________
```

---

### 2. Message Format & Field Names

**Q2.1**: What is the **exact JSON structure** for recipe messages?

Please provide a **real example** with actual field names:

```json
{
  "???" : {
    "???": "볶음밥",        ← Food type field name?
    "???": 180,            ← Target temperature field name?
    "???": 5               ← Cooking time field name?
  }
}
```

**Our guess** (please correct):
```json
{
  "FryRecipe": {
    "food_type": "볶음밥",
    "target_temp": 180,
    "cook_time": 5
  }
}
```

**Q2.2**: What is the **exact JSON structure** for status messages?

Please provide a **real example**:

```json
{
  "???" : {
    "???": 175,            ← Current temperature field name?
    "???": "cooking",      ← State field name?
    "???": 120             ← Elapsed time field name? (seconds)
  }
}
```

**Our guess** (please correct):
```json
{
  "FryStatus": {
    "current_temp": 175,
    "state": "cooking",
    "elapsed_time": 120
  }
}
```

**Q2.3**: What are the possible **state values**?
- [ ] `"idle"` - Not cooking
- [ ] `"preheating"` - Heating up
- [ ] `"cooking"` - Currently cooking
- [ ] `"done"` - Cooking finished
- [ ] Other: _______________

**Q2.4**: Are there any **additional fields** we should know about?
```
[ ] Food color
[ ] Stirring speed
[ ] Time remaining
[ ] Other: _______________
```

---

### 3. Message Frequency & Timing

**Q3.1**: How often will you publish **status updates** (temperature, state)?
- [ ] Every 1 second
- [ ] Every 5 seconds
- [ ] Every 10 seconds
- [ ] Only when values change
- [ ] Other: _______________

**Q3.2**: When will **recipe messages** be sent?
- [ ] Once at the start of cooking
- [ ] Before cooking starts (preparation phase)
- [ ] Repeated during cooking
- [ ] Other: _______________

**Q3.3**: Will you send a message when cooking **finishes**?
- [ ] Yes, state changes to "done"
- [ ] Yes, separate finish message
- [ ] No, we should detect timeout
- [ ] Other: _______________

---

### 4. What AI Should Send Back

**Q4.1**: What should we publish on `AI/FryInfo` topic?

What information do you need?
- [ ] Snapshot count (number of images captured)
- [ ] Recording duration (seconds)
- [ ] AI monitoring status ("monitoring", "idle", "error")
- [ ] Device information (Jetson ID, IP address)
- [ ] Other: _______________

**Q4.2**: What **message format** do you expect from us?

Please provide an **example** of what you want:

```json
{
  "FryInfo": {
    "???": ???,
    "???": ???
  }
}
```

**Our suggestion**:
```json
{
  "FryInfo": {
    "snapshot_count": 25,
    "duration_seconds": 150,
    "ai_status": "monitoring",
    "device_id": "Jetson1",
    "timestamp": "2025-10-31T14:35:22"
  }
}
```

**Q4.3**: How often should we publish AI status?
- [ ] Every snapshot (every 10 seconds)
- [ ] Every minute
- [ ] Only at start/end of cooking
- [ ] Other: _______________

---

### 5. Error Handling & Edge Cases

**Q5.1**: What should we do if **MQTT connection is lost** during cooking?
- [ ] Continue capturing locally, resume publishing when reconnected
- [ ] Stop capturing and wait for reconnection
- [ ] Send alert message
- [ ] Other: _______________

**Q5.2**: What if we **miss a message** (network issue)?
- [ ] Messages have retain flag, we'll get last message on reconnect
- [ ] You'll resend important messages
- [ ] We should request resend
- [ ] Other: _______________

**Q5.3**: What if **multiple cooking sessions** happen simultaneously?
- [ ] Not possible (one fryer at a time)
- [ ] Each session has unique ID in message
- [ ] We handle multiple sessions separately
- [ ] Other: _______________

---

### 6. Testing & Integration

**Q6.1**: Can you provide **3-5 sample messages** we can use for testing?

Example 1 (Recipe start):
```json


```

Example 2 (Status during cooking):
```json


```

Example 3 (Cooking finished):
```json


```

**Q6.2**: What is the **MQTT broker IP address** for testing?
- IP: _______________
- Port: 1883 (confirmed?)
- Username/Password required?: [ ] Yes [ ] No

**Q6.3**: When can we do **integration testing** with the real system?
- Available date/time: _______________

---

### 7. Data Specifications

**Q7.1**: Temperature format:
- [ ] Celsius only
- [ ] Fahrenheit only
- [ ] Both (specify field)
- Units in message?: [ ] Yes [ ] No

**Q7.2**: Time format:
- [ ] Seconds (integer)
- [ ] Minutes (integer)
- [ ] HH:MM:SS (string)
- [ ] ISO timestamp
- Other: _______________

**Q7.3**: Food type:
- [ ] Korean text (UTF-8): "볶음밥", "야채볶음"
- [ ] English: "fried_rice", "vegetables"
- [ ] Code number: 1, 2, 3
- List of possible values: _______________

---

## 📊 Summary of Our Understanding

**What we will do:**
1. Subscribe to `HR/???` (recipe topic - **please confirm**)
2. Subscribe to `HR/???` (status topic - **please confirm**)
3. Capture camera snapshot every 10 seconds when `state == "cooking"`
4. Save images + MQTT data to `/data/stirfry_sessions/`
5. Publish AI status to `AI/FryInfo` every 10 seconds
6. Stop capturing when `state == "done"` or timeout

**Is this correct?** [ ] Yes [ ] No

**If no, what should we change?**
```




```

---

## 📞 Response

Please reply with:
1. Answers to questions above
2. 3-5 sample JSON messages (copy-paste actual messages)
3. MQTT broker IP for testing
4. Any additional requirements we missed

**Contact:**
- Name: _______________
- Email: _______________
- Phone: _______________

**Thank you for your cooperation!**

---

*This document will help us complete the integration within 2-3 days after receiving your response.*
