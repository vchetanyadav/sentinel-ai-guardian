# Sentinel Run Archive

Sample run fixtures from Sentinel's incident response loop. The Next.js dashboard 
uses these as replay sources so judges can scrub through an incident timeline.

## run_20260526-151529.json — Resolved (demo fixture)

**Incident:** RefundBot accuracy regression due to over-approving refunds in v14  
**Severity:** high  
**Outcome:** resolved  

Sentinel's actions:

1. **Detected Regression**: Evaluated metrics against the 24-hour baseline and 
   confirmed a severe degradation in the evaluation pass rate.
2. **Diagnosed Root Cause**: Identified that a recently deployed prompt version 
   (`v14`) introduced a "generous goodwill program" which caused RefundBot to 
   indiscriminately approve all refunds.
3. **Verified Hypothesis**: Ran dataset evaluations showing `v14` plummeted to 
   33% accuracy, whereas the previous `v13` prompt maintained 73% accuracy.
4. **Opened Incident & Requested Approval**: Opened high-severity incident 
   `INC-1779772709` and halted execution until human approval was granted.
5. **Executed Remediation**: Upon receiving human approval, deployed prompt 
   version `v13` to production.
6. **Verified Fix**: Performed a final dataset evaluation, confirming the 73% 
   accuracy was restored. Incident marked `resolved`.