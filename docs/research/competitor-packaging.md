# Competitor packaging benchmark

Resolves the wayfinder ticket **Competitor packaging benchmark** (#21) on the map **Wayfinder: Teams and pricing tiers** (#19).

How comparable task tools split free and paid tiers for individuals and small teams (2–15 people). All sources accessed 2026-09-24 from official pricing pages and help docs unless marked otherwise. Prices are USD per user per month unless stated.

## Comparison

| Product | Free tier limits | Entry paid | Next tier | Metric | Regional / INR pricing |
| --- | --- | --- | --- | --- | --- |
| Linear | Unlimited members, 2 teams, 250 issues, 10 MB uploads, Microsoft Teams integration only, API included | Basic $10 (annual) | Business $16 (annual): unlimited/private teams, guests, Insights, Asks, Zendesk/Intercom | Per seat (all non-suspended users, any role); AI credits separate | None stated |
| Trello | 10 collaborators and 10 boards per Workspace, unlimited cards, unlimited storage (10 MB/file), 250 automation runs/month, basic card view | Standard $6 monthly / $5 annual: unlimited boards, custom fields, 250 MB files, 1,000 runs | Premium $12.50 / $10: calendar, timeline, table, dashboard, map views, unlimited automation, admin controls | Per seat | USD only; Atlassian cannot quote or invoice Trello in other currencies |
| Asana | Personal: up to 2 users, unlimited projects and tasks, unlimited storage (100 MB/file), 100+ integrations | Starter $10.99 annual / $13.49 monthly: timeline/Gantt, reporting dashboards | Advanced $24.99 / $30.49: goals, portfolios, resource management | Per seat | USD/EUR/GBP by country; local billing in MXN, BRL, CAD, KRW; no INR |
| ClickUp | Unlimited members and tasks, 60 MB total storage, 5 Spaces, 5 automation rules / 100 runs per month, basic custom fields, limited AI trial | Unlimited $10 monthly / $7 annual: unlimited storage, Gantt, integrations | Business $19 / $12: advanced dashboards, 5K automations/month | Per seat; AI add-ons $9 (Brain AI) or $28 (Everything AI) per user/month | USD only with local-currency display (partly unverified) |
| Jira | 10 users, 2 GB storage, community support; automation limit stated inconsistently (100 rule runs vs 150 steps) | Standard: 250 GB, business-hours support, advanced permissions, audit logs, 400 automation steps/user/month | Premium: unlimited storage, 24/7 support, 99.9% SLA, Advanced Roadmaps, sandboxes, 750 steps | Per seat; monthly bills peak users, annual bills user tiers | USD/AUD/JPY only; Indian tax applies unless PAN/CIN/tax registration supplied |
| Todoist | Beginner: 5 personal projects, 3 filters, 1 week of activity history, 5 MB uploads; no team features | Pro $7 monthly / $60 yearly (since 2025-12-10): 300 projects, 150 filters, full history, 100 MB uploads, calendar layout, AI Task Assist | Business $10 monthly / $96 yearly per member (was $8 / $72): up to 500 team projects, roles, team activity log | Individual flat plan, then per member | Localized pricing in India and 7 other markets; India Pro ₹330/month or ₹3,165/year; INR checkout supported |
| Height | Shut down 2025-09-24 (announced March 2025); no official successor | — | — | — | — |

Jira list prices could not be read on the date of access (the page is JS-rendered). From prior knowledge, **unverified**: Standard ≈ $7.53 and Premium ≈ $13.53 per user/month.

## Patterns for teams of 2–15

1. **Per seat is universal.** No one charges a flat team price, and none use usage-based pricing apart from AI credits and automation runs.
2. **The free tier limits collaboration in one of three ways:** a seat cap (Asana 2, Jira 10, Trello 10 per Workspace), a volume cap with unlimited seats (Linear 250 issues, ClickUp 60 MB storage), or free for individuals only (Todoist's free tier has no team features).
3. **Entry paid tier is about $5–11 per seat per month** on annual billing. The next tier costs roughly 1.6–2.3× the entry price.
4. **Annual billing is discounted by about 17–37%.** Linear and ClickUp headline the annual price.
5. **Metered upgrade levers:** automation runs, storage and file size, and history retention.
6. **Views beyond list and board are the usual paid headline:** timeline, Gantt, dashboards, reporting.
7. **SSO/SAML, SCIM, audit logs and SLAs sit in the top tiers,** beyond what a team of 2–15 buys.
8. **AI is moving to separate add-ons or credits** (ClickUp, Linear) rather than being bundled into seats.
9. **Local-currency pricing is rare.** Only Todoist has real India pricing: Pro at ₹330/month, well below its $7 global price.
10. **Indian tax handling (GST, PAN) needs explicit treatment.** Atlassian documents it.

The shape these tools suggest for DayStack is free for a single Member, then per-seat pricing once Projects are shared by a Team.

## Unverified or gaps

- Jira list prices (see above) and the free-tier automation limit: the two official Atlassian pages disagree.
- Linear's monthly-billing prices are not shown on its pricing page.
- Todoist's INR Business price was not found. Its India Pro table was labelled oddly (INR shown under "global rate"), so re-check it by hand.
- ClickUp's USD-only billing rests on a search snippet because its help page returned 403.
- Asana's free-tier automation limits are not stated.
- Geolocated INR display could not be tested for any vendor.
- No PPP discounts found for Trello or Asana.

## Sources

- https://linear.app/pricing
- https://linear.app/docs/billing-and-plans
- https://trello.com/pricing
- https://www.atlassian.com/licensing/purchase-licensing
- https://asana.com/pricing
- https://asana.com/guide/help/faq/payments-mxn-brl
- https://help.asana.com/s/article/payments-in-cad-and-krw-currency
- https://clickup.com/pricing
- https://support.atlassian.com/jira-cloud-administration/docs/explore-jira-cloud-plans/
- https://www.atlassian.com/software/jira/guides/more/jira-editions
- https://www.todoist.com/pricing
- https://www.todoist.com/help/articles/todoist-pro-pricing-update-in-2025-bxBvHZuJZ
- https://www.todoist.com/help/articles/todoist-business-plan-pricing-update-dF5in65YM
- https://www.todoist.com/help/articles/supported-payment-methods-and-currencies-XJzvAe
- https://x.com/height_app/status/1903820182557999555
