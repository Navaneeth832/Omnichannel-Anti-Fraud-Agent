# Threat Scoring Framework

## Purpose

This document defines the threat topology, risk calculation method, and scoring semantics used by the Omnichannel Anti-Fraud Agent (Dual MCP). The framework is optimized for scam scenarios where behavioral manipulation is combined with institutional impersonation and phishing infrastructure.

## Threat Topology

The agent scores each case on three dimensions:

| Dimension | Weight | Why It Matters |
| --- | --- | --- |
| Artificial Urgency | 25% | Scam actors compress decision time to bypass rational verification |
| Social Coercion | 25% | Fraud escalates when victims are isolated, intimidated, or forced into secrecy |
| Institutional Deviations | 50% | The strongest signal is whether the process violates how real institutions actually operate |

## Topology Rationale

The weighting is intentionally asymmetric. Many legitimate communications may sound urgent, and some institutions use strong language. What most reliably separates genuine process from fraud is deviation from official protocol. That is why institutional deviations receive half of the total score.

## Dimension Definitions

## 1. Artificial Urgency

Signals:

- Immediate payment demand
- Countdown language such as "within 10 minutes"
- Threat of account freeze or arrest unless action is instant
- Panic-inducing calls to action
- Refusal to allow independent verification

## 2. Social Coercion

Signals:

- Threats of arrest, imprisonment, or legal retaliation
- Orders not to contact family, employer, or bank
- Continuous-call pressure such as "stay on the line"
- Claims of surveillance or monitoring
- Emotional intimidation by authority impersonation

## 3. Institutional Deviations

Signals:

- Personal mobile number for official banking or police communication
- WhatsApp or SMS for legal summons, KYC enforcement, or arrests
- Request for transfer to a “safe” account
- Demand for secrecy around official process
- Non-official domains or typo-squatting
- Payment or credential collection through unverified channels

## Risk Calculation Logic

The final threat score is a weighted average:

```text
Threat Score =
  (Artificial Urgency x 0.25) +
  (Social Coercion x 0.25) +
  (Institutional Deviations x 0.50)
```

The score is normalized to a `0.0` to `1.0` range.

## Risk Bands

| Score Range | Risk Level | Meaning |
| --- | --- | --- |
| 0.00 - 0.30 | LOW | Benign or weakly suspicious evidence |
| 0.31 - 0.60 | MEDIUM | Suspicious, but not yet strongly confirmed |
| 0.61 - 0.80 | HIGH | Strong fraud indicators, user intervention recommended |
| 0.81 - 1.00 | CRITICAL | Immediate action required, guardian alert triggered |

## How MCP Evidence Affects Scores

| MCP Result | Score Effect |
| --- | --- |
| MongoDB confirms official procedure match | Can reduce institutional deviation |
| MongoDB reports protocol violation | Increases institutional deviation significantly |
| Elasticsearch finds exact official domain | Reduces phishing suspicion |
| Elasticsearch finds typo-squatting likelihood | Increases institutional deviation and can raise urgency confidence |

Important rule: behavioral risk can still be high even if a tool returns inconclusive. Lack of evidence is not evidence of safety.

## Worked Examples

## Example 1: Banking Impersonation with Typo-Squatting

Input:

> Your SBI account will be frozen in 10 minutes. Verify now at sbi-kvc-alert.in or your funds will be blocked.

| Dimension | Score | Why |
| --- | --- | --- |
| Artificial Urgency | 0.92 | Explicit 10-minute deadline and account-freeze threat |
| Social Coercion | 0.48 | Threat language present, but limited isolation tactics |
| Institutional Deviations | 0.95 | Suspicious domain and unofficial KYC process |

```text
(0.92 x 0.25) + (0.48 x 0.25) + (0.95 x 0.50)
= 0.23 + 0.12 + 0.475
= 0.825
```

Final score: `0.83`

Risk level: `CRITICAL`

## Example 2: Digital Arrest Scam

Input:

> This is cyber police. Do not disconnect this call. You are under digital arrest for money laundering. Transfer funds to the safe account for audit verification.

| Dimension | Score | Why |
| --- | --- | --- |
| Artificial Urgency | 0.88 | Immediate forced action |
| Social Coercion | 0.97 | Isolation, authority threat, continuous-call control |
| Institutional Deviations | 0.99 | Fake legal process and impossible procedure |

```text
(0.88 x 0.25) + (0.97 x 0.25) + (0.99 x 0.50)
= 0.22 + 0.2425 + 0.495
= 0.9575
```

Final score: `0.96`

Risk level: `CRITICAL`

## Example 3: Suspicious Email with No Verified Institution

Input:

> We noticed unusual activity. Please review your security settings soon.

| Dimension | Score | Why |
| --- | --- | --- |
| Artificial Urgency | 0.31 | Mild pressure only |
| Social Coercion | 0.08 | No intimidation or isolation |
| Institutional Deviations | 0.22 | Insufficient evidence of protocol abuse |

```text
(0.31 x 0.25) + (0.08 x 0.25) + (0.22 x 0.50)
= 0.0775 + 0.02 + 0.11
= 0.2075
```

Final score: `0.21`

Risk level: `LOW`

## Example 4: Phishing Domain with Brand Mimicry

Input:

> Update your bank profile at icicibnak-secure.com to avoid deactivation.

| Dimension | Score | Why |
| --- | --- | --- |
| Artificial Urgency | 0.75 | Threat of deactivation |
| Social Coercion | 0.22 | Little direct coercion |
| Institutional Deviations | 0.93 | Domain transposition strongly indicates typo-squatting |

```text
(0.75 x 0.25) + (0.22 x 0.25) + (0.93 x 0.50)
= 0.1875 + 0.055 + 0.465
= 0.7075
```

Final score: `0.71`

Risk level: `HIGH`

## Decision Thresholds

| Condition | Action |
| --- | --- |
| Score < 0.31 | Return report only |
| Score 0.31 to 0.60 | Return report with cautionary guidance |
| Score 0.61 to 0.80 | Recommend blocking response and verifying institution |
| Score >= 0.80 | Trigger guardian alert and persist blacklist candidate |

## Calibration Guidance

- Avoid assigning extreme scores without direct evidence
- Increase institutional deviation only when evidence indicates actual procedure abuse
- Use MCP outputs to justify high-confidence deviation scores
- Keep social coercion lower when the interaction is suspicious but non-threatening
- Prefer consistency in repeated scam patterns over ad hoc scoring

## Confidence and Limitations

Threat scoring is a practical risk signal, not a substitute for human investigation. Scores can be affected by OCR extraction errors, partial call transcripts, missing institutional rules in MongoDB, and incomplete official domain corpora in Elasticsearch. For that reason, the report should always include a reasoning summary and verification status, not only a number.
