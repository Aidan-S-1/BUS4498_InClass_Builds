# Score Each Registrant's Likelihood of Attending Task Specification

```yaml
# BASIC INFORMATION
task_id: "T3"
task_name: "Score Each Registrant's Likelihood of Attending"
task_owner: "HackTrack agent; the CPVC organizers who order food, drinks, and swag retain final decision authority"

# Agent Inference Configuration
Provider: Claude
Model: "claude-sonnet-5"
Role: Interpret supplied registrant evidence, select the next permitted subtask, and produce an evidence-backed attendance likelihood for each registrant.
Maximum inference requests per task run: "20"
On inference failure or exhausted limits: Record the unresolved status and hand the case to the CPVC organizer review queue.
```

## 1. Task Goal

- **Objective:** Produce an evidence-backed likelihood of attending for every registrant on the current list, labeled likely, uncertain, or unlikely, so that T4 can aggregate the scores into a forecast range without guessing about registrants whose evidence is missing, unclear, or conflicting.

## 2. Inbound Inputs

### Input 1

- **Input name:** Current registration list with contact counts
- **What it contains:** One record per registrant with a registrant ID, registration timestamp, solo or team signup, team name when given, any cancellation or change made through the registration form, and the number of confirmation messages the registrant has already received across all prior checkpoints for this event. A registrant whose contact count is missing from the record is treated as at the two-message limit until an organizer confirms the count; a missing count is never assumed to be zero.
- **Source:** T1: Retrieve Registration List, Contact Counts, Prior Attendance, and Current Scoring Guidance

### Input 2

- **Input name:** Prior attendance records
- **What it contains:** Check-in history from past CPVC events, matched to registrant IDs, showing which past events each registrant registered for and whether they checked in.
- **Source:** T1: Retrieve Registration List, Contact Counts, Prior Attendance, and Current Scoring Guidance

### Input 3

- **Input name:** Confirmation responses and registration signals
- **What it contains:** For each registrant, the confirmation status read from their reply (yes, maybe, no, or no reply), the reply text and time, how many days before the event they registered, and whether they have attended a past club event.
- **Source:** T2: Read Confirmation Responses and Registration Signals

### Input 4

- **Input name:** Logged confirmation responses from this run
- **What it contains:** Replies received after a confirmation request sent during this run, with each registrant's updated contact count. When present, the contact counts here supersede those in Input 1. This input is absent on the first scoring pass of a run.
- **Source:** T6: Log Confirmation Responses Received

### Input 5

- **Input name:** Current scoring weights and tolerance band
- **What it contains:** The weight given to each attendance signal, the label thresholds, and the tolerance band that sets how much forecast uncertainty is acceptable. These are the most recent organizer-approved values stored by T13 after a prior event, or the organizers' starting values when no approved update exists yet. They do not change during a run.
- **Source:** T1: Retrieve Registration List, Contact Counts, Prior Attendance, and Current Scoring Guidance

## 3. Tool Permissions and Boundaries

## 4. How the Agent Should Reason

### Scoring Rule

Every registrant's likelihood is computed on a 0 to 100 scale using the same additive rule, so that two runs with the same inputs produce the same score.

- **Baseline:** Every registrant starts at 40, the club's observed attendance-to-registration rate from the last build event.
- **Signals:** Each signal in Input 5 has a weight expressed in points. A signal that is present and favorable adds its full weight; a signal that is present and unfavorable subtracts its full weight; a signal that is unknown contributes 0 and is listed as unknown in the evidence summary. The agent never invents a partial adjustment for an unknown signal.
- **Starting weights (organizers may revise through T12 and H2):**
  - Confirmation reply: yes +30, maybe +5, no reply 0, no −30
  - Past club attendance: checked in at a prior event +15, registered before but did not check in −10, no matched history unknown (0)
  - Registration timing: registered 14 or more days before the event +10, registered 3 to 13 days before 0, registered within 2 days +5
  - Team signup: on a team where at least one other member is scored likely +10; solo or team with no such member 0
- **Overrides:** An explicit cancellation through the registration form, or a clear "no" reply that is the registrant's most recent signal, sets the score to 0 and the label to unlikely regardless of other signals. A "yes" reply followed by a later cancellation is a cancellation.
- **Bounds:** Scores are clamped to the 0 to 100 range after all signals are applied.
- **Label thresholds:** 70 or above is likely; 40 to 69 is uncertain; below 40 is unlikely.

### Permitted Subtask 1

- **Subtask name:** Apply Baseline Scoring
- **Subtask description:** Applies the scoring rule above, with the current weights, to a registrant's structured signals, such as registration timing, past attendance, and confirmation status, and produces a baseline score along with a note of which signals were present, unfavorable, or unknown.
- **Subtask boundary:** Use only the weights and thresholds in the current scoring guidance input. Do not change the weights, thresholds, or tolerance band, because proposing changes belongs to T12 and approving them belongs to H2.
- **Retry limits:** 0 retries. Run again for the same registrant only after new evidence arrives from T6.

### Permitted Subtask 2

- **Subtask name:** Interpret Unclear Replies
- **Subtask description:** Examines a free-text reply that does not map cleanly to yes or no, such as "maybe," "running late," or "coming if my team does," and maps it to one of the four confirmation states (yes, maybe, no, or unknown) with the reply wording that supports the mapping.
- **Subtask boundary:** Interpret only the registrant's own reply. Do not contact the registrant, since sending messages belongs to T5, and do not guess at personal circumstances the reply does not state.
- **Retry limits:** 1 additional attempt per reply. If the reply is still unclear after the second attempt, record the confirmation signal as unknown (contributing 0) and continue scoring; this is not an escalation. Escalate only if the reply raises something other than attendance, such as a question, complaint, or accessibility request.

### Permitted Subtask 3

- **Subtask name:** Examine Missing History
- **Subtask description:** For first-time registrants or registrants with no matched attendance record, looks for other supplied evidence, such as early registration or signing up with a team whose members attended before, and produces a documented fallback basis or marks the history signal as unknown.
- **Subtask boundary:** Use only the supplied inputs. Do not search outside sources such as social media or other club rosters, and do not treat a lack of history as evidence the registrant will not attend.
- **Retry limits:** 0 retries.

### Permitted Subtask 4

- **Subtask name:** Resolve Conflicting Signals
- **Subtask description:** Examines signals that disagree, such as a "yes" reply followed by a cancellation, two registrations that may belong to the same person, or a team signup where one member declined, and produces a reconciled signal based on the most recent and direct evidence, or a flagged conflict.
- **Subtask boundary:** Reconcile only within the score notes. Do not merge, edit, or delete registration records. Send uncertain identity matches to the organizers instead of deciding them.
- **Retry limits:** 1 additional attempt per conflict. No more than two distinct conflicts per registrant before handing that registrant to the organizers.

### Permitted Subtask 5

- **Subtask name:** Identify Confirmation Candidates
- **Subtask description:** Finds the unconfirmed registrants whose uncertainty most affects the forecast and produces a list of them with each one's current contact count, taken from Input 4 when present and otherwise from Input 1.
- **Subtask boundary:** Do not send any message. Leave off anyone whose contact count is two or more, and anyone whose contact count is missing, because the system goal limits contact to two messages per participant and a missing count cannot be assumed to be below the limit.
- **Retry limits:** Perform once per scoring pass.

### Permitted Subtask 6

- **Subtask name:** Finalize Registrant Score
- **Subtask description:** Combines the findings for a registrant into a final score under the scoring rule and a likely, uncertain, or unlikely label from the thresholds, citing the signals behind it.
- **Subtask boundary:** Do not use an unexplained number. Do not aggregate scores into a forecast or recommend order quantities, because that work belongs to T4 and T8.
- **Retry limits:** Revise once only when another permitted subtask produces new material evidence for that registrant.

- **Decision guidance:** After each subtask, use its findings to select the permitted subtask most likely to resolve the most important remaining uncertainty. Do not follow a fixed sequence. If no permitted subtask can make useful progress on a registrant, mark that registrant undetermined and hand that registrant to a person, then continue with the remaining registrants.

## 5. When to Stop or Hand Off to a Human

- **Stop successfully when:** Every registrant on the current list has either a final score and label that cites at least one supplied signal, or has been marked undetermined and escalated; every unknown signal is labeled as unknown; and no unresolved conflict or identity question affects any registrant who was given a score.
- **Hand off the whole task when:** The registration list, attendance records, or scoring guidance are missing, stale, or unreadable, because no registrant can be scored without them.
- **Hand off an individual registrant when:** A possible duplicate registration cannot be matched with confidence; the conflict limit for that registrant has been reached; the registrant's reply raises something other than attendance, such as a question, complaint, or accessibility request; or finishing that registrant's score would require contacting them or sharing an individual response outside the organizing team. The registrant is marked undetermined, and scoring continues for everyone else.
- **Hand off to:** The CPVC organizer review queue, the same queue the organizers use in H1: Organizers Review and Decide Order Quantities.

Completed scores proceed to T4 even while individual registrants await review. T4 receives the undetermined count so it can widen the forecast range accordingly. Stop at the first applicable budget limit or whole-task handoff condition.

## 6. Outbound Deliverable

- **Status:** Completed, completed with individual escalations, or escalated as a whole task to the CPVC organizer review queue.
- **Result or recommendation:** A 0 to 100 score and a likely, uncertain, or unlikely label for each scored registrant, plus the list of confirmation candidates who are still under the two-message limit. For any registrant escalated before reaching a supported score, write undetermined.
- **Evidence summary:** The signals behind each score, including registration timing, past attendance, confirmation reply, any override applied, and any reconciled conflict, with each unknown signal listed as unknown. Individual responses stay within the organizing team.
- **Subtasks performed:** Permitted subtasks completed, including repeated attempts.
- **Unresolved issues:** Registrants marked undetermined and why; use none only if no unresolved issue remains.
- **Handoff note:** Reason for stopping, the affected registrants, the exact open questions, and what the organizers need to decide or confirm; write "Not applicable" when no registrant was escalated.
- **Next task or recipient:** Send all completed scores and the undetermined count to T4: Aggregate Scores Into a Forecast Range. Undetermined registrants go to the CPVC organizer review queue.
