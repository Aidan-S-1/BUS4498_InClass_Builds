# Workflow of Tasks

## 1. Workflow Overview
### 1.1 Workflow Goal
This workflow supports the system goal defined in `my_first_agent/README.md`.

### 1.2 Workflow Trigger

One run begins when a scheduled planning checkpoint is reached: 14 days, 7 days, and 2 days before the hackathon, plus a final checkpoint when check-in closes on event day. Each checkpoint is one run. The three pre-event checkpoints each produce one forecast; the event-day checkpoint evaluates the final published forecast against actual check-in attendance.

### 1.3 Completion Condition at Runtime

A pre-event run is finished when a final planning decision, meaning a forecast attendance range and the food, drink, and swag quantities it implies, has been recorded in the forecast record along with the inputs behind it, whether that decision came from the system's published forecast or from organizer review; and when any confirmation messages sent during the run have been logged against each registrant's contact count.

The event-day run is finished when the gap between the final planning decision and the actual check-in count has been recorded, and when any proposed revision to the scoring weights or tolerance band has either been approved and stored for the next event or rejected and logged.

### 1.4 General Workflow

A pre-event run starts at a planning checkpoint. The system retrieves the current registration list, each registrant's current contact count, and attendance records from prior CPVC events, then reads each registrant's confirmation responses and registration signals, such as how early they registered and whether they have attended a past club event. From those signals it scores each registrant's likelihood of attending and aggregates the individual scores into a forecast range. If the confidence in that range is within tolerance, the system publishes the forecast and the food, drink, and swag quantities it implies to the organizers' channel. Either way, the run ends by recording a final planning decision: the published forecast when confidence was within tolerance, or the quantities the organizers chose during review when it was not.

Two things interrupt that path. When too many registrants remain unconfirmed for the forecast to be trusted, the system checks each registrant's contact count before doing anything. If a registrant is already at the two-message limit, no further message is sent, because the goal boundary forbids it; instead the forecast is flagged as low confidence and routed to organizer review, where a person decides what to order and that decision is recorded as the final planning decision for the checkpoint. If the limit has not been reached, the system sends a confirmation request to the unconfirmed registrants, logs the responses that come back, and rescores, which is the one loop in the workflow.

The event-day run is different. Confirmation replies are still predictions of attendance, so the forecast is not evaluated against them. Instead, once check-in closes, the system compares the final planning decision from the 2-day checkpoint against the actual check-in count and records the gap. If the gap is outside the tolerance band, the system proposes revised scoring weights and a revised tolerance band, but does not apply them. The organizers review the proposal, because a single unusual event should not automatically change how future events are forecast. Only an approved revision is stored, and it is retrieved by T1 at the start of the next event's first checkpoint rather than feeding back into the current run.

### 1.5 Workflow Diagram

```mermaid
flowchart TD
    S0([Run starts: planning checkpoint reached]) --> D0{"Event-day checkpoint?"}
    D0 -->|No, pre-event checkpoint| T1["T1: Retrieve Registration List, Contact Counts, Prior Attendance, and Current Scoring Guidance"]
    T1 --> T2["T2: Read Confirmation Responses and Registration Signals"]
    T2 --> T3["T3: Score Each Registrant's Likelihood of Attending"]
    T3 --> T4["T4: Aggregate Scores Into a Forecast Range"]
    T4 --> D1{"Forecast confidence within tolerance?"}
    D1 -->|No| D2{"Two-message contact limit reached?"}
    D2 -->|No| T5["T5: Send Confirmation Request to Unconfirmed Registrants"]
    T5 --> T6["T6: Log Confirmation Responses Received"]
    T6 --> T3
    D2 -->|Yes, boundary blocks further contact| T7["T7: Flag Forecast as Low Confidence and Route to Review"]
    T7 --> H1["H1: Organizers Review and Decide Order Quantities"]
    D1 -->|Yes| T8["T8: Publish Forecast and Order Recommendation to Organizers"]
    H1 --> T9["T9: Record Final Planning Decision, Forecast, Inputs, and Responses"]
    T8 --> T9
    T9 --> C1([C1: Pre-Event Run Complete])

    D0 -->|Yes, check-in has closed| T10["T10: Compare Final Planning Decision Against Actual Check-In Count"]
    T10 --> T11["T11: Record Actual Attendance and Forecast Gap"]
    T11 --> D3{"Forecast gap outside the tolerance band?"}
    D3 -->|No| C2([C2: Event-Day Run Complete])
    D3 -->|Yes| T12["T12: Propose Revised Scoring Weights and Tolerance Band"]
    T12 --> H2["H2: Organizers Approve or Reject Proposed Revision"]
    H2 -->|Rejected| T14["T14: Log Rejected Proposal and Reason"]
    H2 -->|Approved| T13["T13: Store Approved Guidance for Retrieval at Next Event's First Checkpoint"]
    T13 --> C2
    T14 --> C2
```
