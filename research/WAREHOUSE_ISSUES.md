# Warehouse friction research and feature boundary

Reviewed 2026-09-21. This note informed the Warehouse Friction screen. It is not a prevalence study for a particular site and supplies **no default benchmark values** to the app.

## Why these issues are in the screen

| Common operational issue | Evidence | Product treatment |
|---|---|---|
| Congestion, space pressure and travel/waiting time | The 2025 Warehouse/DC Operations Survey reports inventory challenges, identifies receiving as the most congested area among its respondents, and records space pressure during peak. | Enter a local average delay per picked order. The model adds it to pick service time and reruns all staffing allocations. No survey percentage is used as an input. |
| Replenishment and inventory exceptions | The same survey describes persistent inventory challenges and continued manual data collection. | Enter an observed exception rate and recovery time. Their product is an expected added pick-time assumption; it does not claim a causal root cause or measured accuracy rate. |
| Packing rework | Value-added labelling, packaging and serial-control work appear in the survey. Rework is operationally distinct from normal packing. | Enter a local rework rate and duration. The model adds the expected time to packing and labels the result as an assumption. |
| Manual handling and repetitive work | OSHA identifies lifting/lowering, bending, reaching, pushing/pulling, awkward posture and repetition as warehouse ergonomic risk factors. | A qualitative safety prompt only. The app does not translate injury risk into capacity, cost or a productivity target. |
| Powered equipment, aisles, storage and floor conditions | OSHA identifies powered industrial trucks, material handling, storage, slips/trips/falls and aisle clearance as warehouse hazards. | Qualitative prompts for traffic separation, access routes and local inspection. This is not a compliance determination or a substitute for a site hazard assessment. |

## Sources and limits

- [OSHA — Warehousing overview](https://www.osha.gov/warehousing/), accessed 2026-09-21. OSHA identifies material handling, ergonomics, powered industrial trucks, slips/trips/falls and robotics as hazards in warehouse work.
- [OSHA — Warehousing hazards and solutions](https://www.osha.gov/warehousing/hazards-solutions), accessed 2026-09-21. Used for the ergonomic, vehicle/pedestrian, aisle and storage review prompts.
- [2025 Warehouse/DC Operations Survey](https://www.scmr.com/article/2025-warehouse-dc-operations-survey-tech-adoption-marches-on), Supply Chain Management Review, November 2025. The article describes a 101-response industry survey. It is useful context for congestion, inventory and labor/data concerns, not a statistically representative global benchmark and not evidence about this user's operation.

The tool intentionally excludes worker injury likelihood, legal compliance, incident costs, inventory accuracy prediction, slotting optimization, equipment reliability, waves, shared workers and causal intervention recommendations. Validate any input with local WMS, exception, replenishment, safety and roster data before using a scenario to inform a trial.
