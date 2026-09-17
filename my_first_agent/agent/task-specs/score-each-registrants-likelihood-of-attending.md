# Score Each Registrant's Likelihood of Attending Task Specification

```yaml
# BASIC INFORMATION
task_id: "T3"
task_name: "Score Each Registrant's Likelihood of Attending"
task_owner: "HackTrack agent; the CPVC organizers who order food, drinks, and swag retain final decision authority"

# Agent Inference Configuration
Provider: Claude
Model: "claude-sonnet-4-5"
Role: Interpret supplied registrant evidence, select the next permitted subtask, and produce an evidence-backed attendance likelihood for each registrant.
Maximum inference requests per task run: "20"
On inference failure or exhausted limits: Record the unresolved status and hand the case to the CPVC organizer review queue.
```

## 1. Task Goal

- **Objective:** Produce an evidence-backed likelihood of attending for every registrant on the current list, labeled likely, uncertain, or unlikely, so that T4 can aggregate the scores into a forecast range without guessing about registrants whose evidence is missing, unclear, or conflicting.

## 2. Inbound Inputs

### Input 1

- **Input name:** Current registration list
- **What it contains:** One record per registrant with a registrant ID, registration timestamp, solo or team signup, team name when given, and any cancellation or change made through the registration form.
- **Source:** T1: Retrieve Registration List and Prior Attendance Records

### Input 2

- **Input name:** Prior attendance records
- **What it contains:** Check-in history from past CPVC events, matched to registrant IDs, showing which past events each registrant registered for and whether they checked in.
- **Source:** T1: Retrieve Registration List and Prior Attendance Records

### Input 3

- **Input name:** Confirmation responses and registration signals
- **What it contains:** For each registrant, the confirmation status read from their reply (yes, maybe, no, or no reply), the reply text and time, how many days before the event they registered, and whether they have attended a past club event.
- **Source:** T2: Read Confirmation Responses and Registration Signals

### Input 4

- **Input name:** Logged confirmation responses from this run
- **What it contains:** Replies received after a confirmation request sent during this run, with each registrant's updated contact count. This input is absent on the first scoring pass of a run.
- **Source:** T6: Log Confirmation Responses Received

### Input 5

- **Input name:** Current scoring weights and tolerance band
- **What it contains:** The weight given to each attendance signal and the tolerance band that sets how much forecast uncertainty is acceptable.
- **Source:** T11: Update Scoring Weights and Tolerance Band, from an earlier checkpoint or event; the organizers' starting weights when no update exists yet

## 3. Tool Permissions and Boundaries

## 4. How the Agent Should Reason

### Permitted Subtask 1

- **Subtask name:** Apply Baseline Scoring
- **Subtask description:** Applies the current scoring weights to a registrant's structured signals, such as registration timing, past attendance, and confirmation status, and produces a baseline likelihood along with a note of which signals were present or missing.
- **Subtask boundary:** Use only the weights in the current scoring weights input. Do not change the weights or the tolerance band, because that work belongs to T11.
- **Retry limits:** 0 retries. Run again for the same registrant only after new evidence arrives from T6.

### Permitted Subtask 2

- **Subtask name:** Interpret Unclear Replies
- **Subtask description:** Examines a free-text reply that does not map cleanly to yes or no, such as "maybe," "running late," or "coming if my team does," and produces an adjusted attendance signal with the reply wording that supports it.
- **Subtask boundary:** Interpret only the registrant's own reply. Do not contact the registrant, since sending messages belongs to T5, and do not guess at personal circumstances the reply does not state.
- **Retry limits:** 1 additional attempt per reply. If the reply is still unclear, record the signal as unknown.

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
- **Subtask description:** Finds the unconfirmed registrants whose uncertainty most affects the forecast and produces a list of them with each one's current contact count.
- **Subtask boundary:** Do not send any message. Leave off anyone who has already received two confirmation messages, because the system goal limits contact to two messages per participant.
- **Retry limits:** Perform once per scoring pass.

### Permitted Subtask 6

- **Subtask name:** Finalize Registrant Score
- **Subtask description:** Combines the findings for a registrant into a final likelihood and a likely, uncertain, or unlikely label, citing the signals behind it.
- **Subtask boundary:** Do not use an unexplained number. Do not aggregate scores into a forecast or recommend order quantities, because that work belongs to T4 and T8.
- **Retry limits:** Revise once only when another permitted subtask produces new material evidence for that registrant.

- **Decision guidance:** After each subtask, use its findings to select the permitted subtask most likely to resolve the most important remaining uncertainty. Do not follow a fixed sequence. If no permitted subtask can make useful progress, stop and hand the case to a person.

## 5. When to Stop or Hand Off to a Human

- **Stop successfully when:** Every registrant on the current list has a final likelihood and label that cites at least one supplied signal, every unknown signal is labeled as unknown, and no unresolved conflict or identity question affects any registrant's score.
- **Hand off early when:** The registration list, attendance records, or scoring weights are missing, stale, or unreadable; a possible duplicate registration cannot be matched with confidence; the interpretation or conflict limits have been reached; a reply raises something other than attendance, such as a question, complaint, or accessibility request; or finishing a score would require contacting a registrant or sharing an individual response outside the organizing team.
- **Hand off to:** The CPVC organizer review queue, the same queue the organizers use in H1: Organizers Review and Decide Order Quantities.

Stop at the first applicable budget limit or handoff condition. While awaiting review, take no further autonomous action.

## 6. Outbound Deliverable

- **Status:** Completed or escalated to the CPVC organizer review queue.
- **Result or recommendation:** A likelihood of attending and a likely, uncertain, or unlikely label for each registrant, plus the list of confirmation candidates who are still under the two-message limit. For any registrant escalated before reaching a supported score, write undetermined.
- **Evidence summary:** The signals behind each score, including registration timing, past attendance, confirmation reply, and any reconciled conflict. Individual responses stay within the organizing team.
- **Subtasks performed:** Permitted subtasks completed, including repeated attempts.
- **Unresolved issues:** Registrants whose evidence is still missing, unclear, or conflicting; use none only if no unresolved issue remains.
- **Handoff note:** Reason for stopping, the affected registrants, the exact open questions, and what the organizers need to decide or confirm; write "Not applicable" for a completed task.
- **Next task or recipient:** Send completed scores to T4: Aggregate Scores Into a Forecast Range. Unresolved cases go to the CPVC organizer review queue.
