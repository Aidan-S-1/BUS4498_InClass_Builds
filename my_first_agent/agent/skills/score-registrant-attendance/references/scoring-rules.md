# Scoring rules for registrant attendance likelihood

SYNTHETIC teaching reference for the HackTrack workflow (BUS 4498, Cal Poly Vibe Coding Club hackathon). These are the organizers' *starting* weights and decision rules. They are the defaults the Skill uses when no updated weights are supplied. Only an organizer-approved revision (proposed by T12, approved in H2, stored by T13) may change them; this Skill applies them and never edits them.

## 1. Baseline score and default weights

Every registrant starts at a baseline of **40 points**, which matches the roughly 40% attendance-to-registration rate at CPVC's last build event. Each signal below adds or subtracts points. The final score is clamped to 0–100.

| Signal | Value observed | Points | Why |
| --- | --- | ---: | --- |
| Confirmation reply | yes | +35 | The most direct statement of intent |
| Confirmation reply | maybe | +10 | Some intent, still unsure |
| Confirmation reply | no reply | 0 | No evidence either way |
| Confirmation reply | no | set score to 5 | A clear decline overrides other signals |
| Past attendance | checked in at at least one prior CPVC event | +15 | Past behavior is the strongest predictor of turnout |
| Past attendance | registered for a prior event but never checked in | −15 | Past no-shows tend to repeat |
| Past attendance | no matched history (first-time registrant) | 0 | Unknown is not evidence of not attending |
| Registration timing | registered within 3 days of the event | +10 | Late sign-ups usually have concrete plans |
| Registration timing | registered 4–14 days before | 0 | Neutral |
| Registration timing | registered more than 14 days before | −5 | Early sign-ups more often forget or change plans |
| Team signup | signed up with a named team | +10 | Teammates hold each other accountable |
| Team signup | solo | 0 | Neutral |
| Cancellation | cancelled or withdrew through the registration form | set score to 0 | A cancellation is final for scoring purposes |

An override ("set score to") is applied after all additive points and wins over them. If both a decline and a cancellation are present, use 0.

## 2. Labels

| Final score | Label |
| ---: | --- |
| 65–100 | likely |
| 35–64 | uncertain |
| 0–34 | unlikely |

A registrant escalated to the organizers before a supported score is reached is labeled **undetermined**, not one of the three labels above.

## 3. Rules for interpreting unclear replies

Apply these when a free-text reply does not map cleanly to yes, maybe, or no.

- Read only the registrant's own words. Do not infer personal circumstances the reply does not state.
- Map common phrasings: "I'll be there", "count me in", "see you Saturday" → yes. "Probably", "planning to", "should be able to" → maybe. "Can't make it", "won't be there", "have to skip" → no. "Running late" or "coming after class" → yes (attending, just later). "Coming if my team does" or "depends on X" → maybe, and note the dependency.
- A reply that is still unclear after one additional reading attempt is recorded as **unknown** and scored as no reply (0 points).
- Quote the reply wording in the evidence column so an organizer can check the interpretation. Do not paraphrase in a way that changes meaning.
- A reply that raises something other than attendance, such as a question, complaint, or accessibility request, is a **handoff condition**. Score the registrant on the attendance part only if it is unambiguous; otherwise mark undetermined and hand the reply to the organizers.

## 4. Rules for missing attendance history

- First-time registrants and registrants with no matched record get 0 history points and the history signal is marked **unknown**.
- Look for fallback evidence in the supplied inputs only: signing up with a team whose other members attended before, or a confirmation reply. Do not search social media, other club rosters, or any outside source.
- Never treat a lack of history as evidence the registrant will not attend.

## 5. Rules for conflicting signals

- Prefer the most recent and most direct evidence. A cancellation dated after a "yes" reply wins; a "yes" reply dated after a "maybe" wins.
- Two registrations that may belong to the same person (same name with different IDs, same email with different names) are an **identity question**. Do not merge, edit, or delete records. Score each record on its own evidence, flag both as a possible duplicate, and send the question to the organizers.
- A team signup where one member declined does not change the other members' scores; note the dependency in their evidence.
- A conflict that cannot be reconciled after one additional attempt is a **flagged conflict**. No more than two distinct conflicts per registrant; after that, hand the registrant to the organizers as undetermined.

## 6. Rules for choosing confirmation candidates

- Candidates are registrants labeled **uncertain** whose confirmation status is no reply or unknown.
- Exclude anyone whose contact count is already 2, because the system goal limits contact to two messages per participant.
- Exclude anyone whose contact count is **missing**. A missing count is treated as at the limit until an organizer confirms it; it is never assumed to be zero.
- Rank candidates by how close their score is to the 50-point midpoint (closest first), because those registrants swing the forecast the most.
- List candidates only. Sending the message belongs to T5.

## 7. Retry and effort limits

- Baseline scoring: 0 retries. Rescore a registrant only after new evidence arrives from T6.
- Unclear replies: 1 additional attempt per reply, then unknown.
- Missing history: 0 retries.
- Conflicting signals: 1 additional attempt per conflict, at most two distinct conflicts per registrant.
- Confirmation candidates: once per scoring pass.
- Final score: revise once, only when another step produces new material evidence.
- Whole task: at most 20 inference requests per run. When the limit is reached, record the unresolved status for the remaining registrants and hand them to the CPVC organizer review queue.
