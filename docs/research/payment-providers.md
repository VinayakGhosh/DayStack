# Payment provider options for an India-registered SaaS selling globally

- **Accessed:** 2026-09-24 (all sources)
- **Status:** Research draft for GitHub issue #22. This is not tax or legal advice. Items marked **[CA]** need a Chartered Accountant or lawyer to confirm. Items marked **[unverified]** could not be confirmed against a primary source.
- **Question:** Which payment provider fits a SaaS business registered in India that sells subscriptions (likely per-seat or per-Team) to individuals and small software teams worldwide from launch? The candidates are merchant-of-record (MoR) providers (Paddle, Lemon Squeezy, Stripe Managed Payments, Polar, Dodo Payments, Creem, FastSpring) and direct acquirers (Razorpay, Stripe India).

## TL;DR

- **Only an MoR removes the foreign VAT and sales tax burden.** With a direct acquirer (Razorpay or Stripe India), DayStack is the seller everywhere. For example, EU B2C digital sales from a non-EU business have **no threshold**: DayStack would have to register for non-Union OSS and file quarterly, including nil returns [22]. Stripe Tax cannot be used by an India-based business [9].
- **Stripe India is invite-only** [7][8]. **Stripe Managed Payments (Stripe's MoR) does not list India** as a supported business location [6]. So neither Stripe route is reliably open to us today.
- **Lemon Squeezy is winding into Stripe Managed Payments** [4][5]. Indian sellers without a pre-approved Stripe account can only take payouts through PayPal [26]. It is not a good launch choice.
- **Paddle** accepts Indian sellers [11] and charges 5% + 50¢ all-in [1]. It collects 18% GST from Indian B2C buyers [12], supports proration to the minute and quantity-based seats [15], and has a customer portal [16]. It **does not pay out in INR**: payouts arrive in USD, EUR or GBP by wire or Payoneer, monthly, with a $100 minimum [13][14].
- **Polar** accepts Indian sellers through Stripe Connect Express payouts [18]. It has first-class **seat-based billing** with a portal and seat webhooks [20]. Fees are 5% + 50¢ plus 1.5% for non-US cards on the entry plan, plus Stripe payout fees [19]. **Dodo Payments** (India-friendly, INR not a payout currency) costs 4% + 40¢ plus 1.5% international plus 0.5% for subscriptions [21][27].
- **Razorpay** is the cheapest direct route for Indian customers: 2% domestic, up to 3% on international cards, plus 0.9% for card subscriptions, all + 18% GST on fees [3]. It settles in INR and auto-generates e-FIRAs [28]. But DayStack would own every foreign tax obligation.
- **RBI e-mandate rules** (new consolidated Framework, 21 Apr 2026) apply to Indian cards, UPI and PPIs, including cross-border ones. They require AFA at registration, pre-debit notice ≥24h, and AFA again above **Rs 15,000** per charge [23]. Every provider inherits this. Pick one that handles Indian card and UPI mandates.
- **Recommendation:** launch on an MoR. **Paddle** is the conservative default. **Polar** is the best seat-billing developer experience if its maturity is acceptable. Get CA sign-off on the MoR payout = export-of-services + LUT position before go-live.

## Comparison table

| Provider | Model | India entity as seller? | Subscriptions / per-seat | Tax handling | Fees (headline) | Payout currency to India | FIRA / e-BRC | Portal / proration / webhooks |
|---|---|---|---|---|---|---|---|---|
| **Paddle** | MoR | Yes (India not on unsupported list) [11] | Yes; quantity changes prorated [15] | Paddle collects and remits VAT/sales tax; India 18% GST B2C [12] | 5% + 50¢ all-in; custom below $10 [1] | USD/EUR/GBP etc., **no INR**; wire or Payoneer; $15 SWIFT may apply [13][14] | Bank issues FIRA/e-FIRA on the inward wire; nothing documented by Paddle [13] **[unverified]** | Portal yes [16]; 5 proration modes [15]; webhooks yes |
| **Lemon Squeezy** | MoR (Stripe-owned) | Yes, but bank payouts need a pre-approved Stripe account, else PayPal only [26] | Yes; quantity + proration [31] | LS collects and remits | 5% base, +1.5% non-US, +0.5% subs, +1.5% PayPal; PayPal intl payout 3% capped at $30 [2][25] | USD via PayPal (for most Indian sellers) [26] | PayPal inward remittance; FIRA handling unclear **[unverified]** | Portal yes [31]; proration yes; webhooks yes |
| **Stripe Managed Payments** | MoR | **No**: India not in supported business locations [6] | Via Stripe Billing, Checkout / Payment Links only [5] | Stripe as MoR, 80+ countries [5] | Not on the fetched pages **[unverified]** | n/a | n/a | Stripe Billing portal; limited: no subscriptions outside Checkout [5] |
| **Polar** | MoR (US) | Yes, payouts via Stripe Connect Express even though Stripe standalone is invite-only [18] | **Native seat-based pricing**, prorated seat add/remove [20] | Polar collects and remits | 5% + 50¢ (Starter) down to 3.4% + 30¢; +1.5% non-US cards; $15/dispute; payout $2/mo + 0.25% + 25¢, cross-border up to 1% [19] | Stripe cross-border payout (INR expected) **[unverified]** | Unclear who issues the purpose code / FIRA **[unverified]** | Portal with seat management; `seat.claimed`/`seat.revoked` webhooks [20] |
| **Dodo Payments** | MoR | Yes (India on accepted list) [27] | Subscriptions, seats, usage [21] **[partly unverified]** | Dodo collects; calculates GST for Indian merchants [21] | 4% + 40¢ US; +1.5% intl; +0.5% subs; India domestic 4% + 15¢; $5 on payouts < $1,000; $25 USD SWIFT for non-US [27] | USD/GBP/EUR; **INR no longer a payout wallet** [21] | Not documented **[unverified]** | Docs mention webhooks; portal and proration not confirmed **[unverified]** |
| **Creem** | MoR | Not stated [29] **[unverified]** | Subscriptions | 50+ countries [29] | 3.9% + 40¢, no intl card fee [29] | Bank or USDC [29] | Not documented | Not assessed |
| **FastSpring** | MoR | "Anywhere in the world" per marketing [30] | Yes | Full MoR | Quote-based; not published [30] | Not assessed | Not documented | Not assessed |
| **Razorpay** | Direct (PA) | Yes, native | Plans with `quantity`, prorated immediate or cycle-end updates; intl cards supported [32][33] | **DayStack** charges Indian GST and owns all foreign tax | 2% domestic; up to 3% intl cards; +0.9% card subscriptions; 18% GST on fees [3] | INR only [33] | e-FIRA auto-generated per settled intl payment (Razorpay blog, first-party marketing) [28] | Hosted pages; no Stripe-style portal **[unverified]**; webhooks yes |
| **Stripe India** | Direct | **Invite-only** [7][8] | Stripe Billing (best in class) | **DayStack** owns all tax; Stripe Tax not available to IN-based businesses [9] | 2% domestic; 3% intl; 4.3% intl with non-INR presentment; +2% FX; Billing 0.7% [10] | INR only [34] | SCB payment advice → bank FIRC [7][35] | Full portal, proration, webhooks; Indian mandates only via Subscriptions [24] |

## MoR vs direct acquiring: implications for an Indian entity

### Who is the seller?

- **MoR:** the provider is the legal seller to the end customer. DayStack makes one supply to the MoR entity (Paddle, Polar and Dodo entities are outside India) and receives a net payout in foreign currency.
- **Direct:** DayStack sells to each end customer. It invoices, collects tax and carries consumer-law and chargeback liability in every market.

### GST on domestic Indian customers

- **Direct:** DayStack charges 18% GST on Indian sales. A domestic customer is not an export under IGST s.2(6) [36].
- **MoR:** a foreign MoR supplying Online Information Database Access and Retrieval (OIDAR) services is liable for IGST on supplies to *non-taxable online recipients* in India (IGST s.14(1)). A foreign intermediary that collects payment or sets terms is deemed the supplier (s.14 proviso) [37]. Paddle publishes India as 18% GST, B2C [12]. Indian **B2B** buyers of a foreign MoR would normally self-assess under reverse charge (s.2(16) excludes business recipients) [37] **[CA]**. This may be friction for Indian team customers who expect an Indian GSTIN invoice.

### Export of services, place of supply and LUT

- **The s.2(6) test has five conditions:** supplier in India; recipient outside India; place of supply outside India; payment in convertible foreign exchange (or INR where RBI permits); not merely establishments of a distinct person [36].
- **Place of supply:** the default is the location of the recipient (IGST s.13(2)) [38]. The **intermediary rule s.13(8)(b) was omitted by the Finance Act 2026 (No. 4 of 2026, 30 Mar 2026)** [38]. That removes a past argument that platform-type suppliers are taxed in India.
- **Zero-rating:** exports are zero-rated (IGST s.16). The supplier can export under **bond or LUT without paying IGST** and claim refund of unused ITC, or pay IGST and claim a refund [39][40].
- **LUT form:** the LUT is furnished in FORM GST RFD-11 before export (CGST Rule 96A(1)).
- **LUT deadline:** if payment isn't received in foreign exchange within 15 days after one year from invoice (or the FEMA period, including RBI extensions, if later), the tax becomes payable with interest (Rule 96A(1)(b)) [41].
- **Open MoR questions [CA]:**
  - Is the MoR payout an export of services by DayStack to the MoR entity, even for sales where the end customer is in India? The MoR's recipient location is outside India, which suggests yes, but confirm it.
  - Does GST registration become mandatory before the Rs 20 lakh threshold, given exports are inter-state supplies?
  - Is the MoR's margin a separate imported service taxable under reverse charge, or simply a lower buy price in a buy-sell model?
- **Direct model:** each foreign-customer payment must individually meet s.2(6). Indian customers are domestic, taxable supplies.

### Foreign VAT and sales tax registrations (direct model only)

- **EU:** there is no threshold for non-EU businesses selling B2C electronic services. The seller registers in one member state under non-Union OSS and files quarterly returns, including nil returns [22].
- **UK, US states, Australia and others:** similar regimes exist. They were not individually researched here **[unverified]**.
- **Stripe Tax:** it lists India as "Not supported" as a business location [9], so an India-based Stripe account cannot use it to automate this.
- **Workload:** in practice, direct acquiring for a global B2C/B2B mix means a tax-compliance workstream from day one.

### FIRA/FIRC, e-BRC and FEMA realisation

- **FIRC / e-FIRA:** these are the bank's evidence of inward foreign-exchange remittance. AD banks report e-FIRCs to EDPMS [42].
  - Stripe India: Standard Chartered emails "payment advice", which you take to your bank for a FIRC [7][35].
  - Razorpay: says it auto-generates an e-FIRA per settled international payment [28] (first-party marketing, not docs).
  - MoR wires (Paddle, Dodo, Polar/Stripe Connect): the receiving Indian bank issues the FIRA/e-FIRA on the inward remittance **[unverified per provider]**.
- **e-BRC:** DGFT now lets exporters self-generate e-BRCs from bank Inward Remittance Messages (IRMs). For services, one IRM gives one e-BRC. Trade Notice 02/2025-26 added a "Mode of Export of Services" field [43]. Fewer, larger MoR payouts mean far fewer e-BRCs than per-transaction direct acquiring.
- **Realisation period (changing now):**
  - The current Master Direction still states 9 months [42]. A Nov 2025 amendment (FEMA 23(R)/(7)/2025-RB) reportedly extended this to 15 months, and a 2026 amendment reportedly reverted part of it (secondary sources only [44]).
  - **New FEMA (Export and Import of Goods and Services) Regulations, 2026 take effect 1 Oct 2026** [45]. They set **15 months from invoice** for services (18 months for INR-invoiced) and require service-export declarations **within 30 days from the end of the month of invoice**, with monthly consolidation. Simplified EDPMS closure applies for transactions up to Rs 10 lakh [45].
  - **[CA]:** how these apply to an MoR payout, and whether the MoR's deduction of its fee counts as short-realisation needing reporting. The 2026 regulations say nothing explicit about intermediaries or fee deductions [45].
- **Payment aggregators:** RBI permits online payment gateways and PA-CBs for export receipts, capped at Rs 25 lakh per unit of service [42][46]. This is not a constraint for DayStack's price points.

### RBI e-mandate for Indian cards and UPI

- **Framework:** Digital Payments – E-mandate Framework, 2026 (RBI/DPSS/2026-27/396, 21 Apr 2026). It applies to cards, PPIs and UPI, domestic and **cross-border**, and repeals the 2019–2024 circulars [23].
  - One-time registration with AFA; the first transaction needs AFA [23].
  - Pre-transaction notice from the issuer **≥24 hours** before debit, with an opt-out [23].
  - Subsequent debits up to **Rs 15,000** without AFA. Insurance, mutual funds and credit-card bill payments go up to Rs 1,00,000 (not relevant to SaaS) [23].
- **Stripe's implementation:**
  - It covers any off-session charge on an Indian card, including charges by non-Indian Stripe accounts. Card charges are delayed **26 hours** and the PaymentIntent sits in `processing` meanwhile [24].
  - Mandates are only created via Subscriptions, not raw PaymentIntents or SetupIntents. They can't be updated. For non-INR subscriptions, an Indian card must be attached at creation [24].
- **Dodo:** creates a Rs 15,000 on-demand UPI mandate for smaller charges, with a 48-hour debit delay [21].
- **Paddle:** lists UPI Autopay [17]. Indian-card mandate handling is not documented on the page fetched **[unverified]**.
- **Product implications:**
  - Mid-cycle seat increases on Indian cards may fail or need re-authentication if they exceed the mandate or Rs 15,000.
  - Renewals collect about a day late.
  - Razorpay doesn't allow subscription updates on UPI or eMandate-authorised subscriptions, and only the offer can be changed on domestic-card subscriptions [32].

### Invoicing

- **MoR:** the MoR issues tax invoices to customers. DayStack issues one export invoice per payout (or per the MoR's self-billing statement) to the MoR entity **[CA: invoice form and timing under Rule 46 and the 2026 FEMA declaration]**.
- **Direct:** DayStack issues GST-compliant invoices domestically and export invoices ("supply meant for export under LUT") to foreign customers, plus any foreign-VAT invoices.

## Per-provider notes

- **Paddle:**
  - Established MoR. India is a supported seller country [11]. 5% + 50¢ covers tax, fraud, billing support and dunning [1].
  - Payouts are monthly: the balance converts on the 1st and is sent by the 15th. The minimum is $100. Methods are wire or Payoneer [13]. There are 13 payout currencies, excluding INR [14].
  - Paddle Billing proration modes: `prorated_immediately`, `prorated_next_billing_period`, `full_immediately`, `full_next_billing_period`, `do_not_bill`. They apply to quantity changes [15].
  - Customer portal with authenticated sessions via API [16].
- **Lemon Squeezy:**
  - Stripe acquired it in 2024. A Jan 2026 update says it is transitioning to Stripe Managed Payments, with slower support and product updates [4].
  - Indian sellers need Stripe pre-approval for bank payouts, else PayPal only [26].
  - Stacked fees for an Indian seller with mostly non-US subscription customers come to about 7% + 50¢ + PayPal payout 3% (cap $30) [25]. Avoid.
- **Stripe Managed Payments:**
  - MoR, digital products only; SaaS fits [6]. Requires Checkout or Payment Links, and subscriptions cannot be created outside Checkout [5].
  - **India not supported** as a business location [6]. Re-check later; LS says expansion is planned in 2026 [4].
- **Polar:**
  - US MoR aimed at developers. Explicitly supports sellers in invite-only Stripe countries via Connect Express payouts [18].
  - Native seat-based products: the billing manager buys N seats and assigns them in the portal. Seats are prorated both ways, with seat webhooks [20]. This maps closely to DayStack's Team concept.
  - Fees are tiered, plus the international card surcharge and Stripe payout costs [19].
  - Younger company; evaluate longevity and Indian-card mandate support **[unverified]**.
- **Dodo Payments:**
  - India is an accepted merchant country [27]. Calculates GST for Indian merchants. Supports Indian cards, RuPay and UPI subscriptions with RBI mandates [21].
  - INR was dropped as a payout wallet; payouts are in USD, GBP or EUR [21].
  - Pricing and many claims come from Dodo's own marketing and blog; the blog was used only for discovery.
- **Creem:** 3.9% + 40¢, tax in 50+ countries, bank or USDC payouts [29]. Seller-country eligibility is unpublished **[unverified]**.
- **FastSpring:** long-standing MoR, quote-based pricing [30]. Not evaluated further; likely costlier for a small launch **[unverified]**.
- **Razorpay:**
  - Native Indian PA. Onboarding needs PAN, GSTIN (if registered), address proof and video KYC [33].
  - International cards settle in INR [33], T+7 default per Razorpay's blog [28].
  - Subscriptions support `quantity` (e.g. number of users). Updates are prorated per day when immediate, with credit notes on downgrade [32].
  - DayStack would be seller of record everywhere.
- **Stripe India:**
  - Invite-only; must be a registered business (not an individual) and opt into exports with an RBI purpose code (e.g. P0802/P0807). IEC is optional for services unless accepting Amex international [7].
  - Name and billing address are required on every export charge [7]. Payouts are INR only [34]. No Stripe Tax for IN-based businesses [9].

## Developer experience (FastAPI + React)

- **Stripe Billing** (if ever available) is the reference: proration, quantity, portal, rich webhooks, Python SDK. India constrains mandates [24].
- **Paddle Billing:** REST API plus webhooks, Paddle.js overlay/inline checkout, full proration control [15], hosted portal [16]. Seats are modelled as item `quantity`; DayStack owns seat assignment.
- **Polar:** seat assignment and portal are built in, and webhooks keep entitlements in sync [20]. This means the least custom Team billing UI.
- **Lemon Squeezy:** quantity and proration via API, hosted portal [31]. Its product future is uncertain [4].
- **Razorpay:** Subscriptions API with quantity and proration [32]. Update limits for UPI and eMandate [32]. Less polished portal and tax tooling.
- **Common pattern:** treat provider webhooks as the source of truth for subscription state in `task_workspace`. Keep Team seat counts server-side. Never trust client-side redirects.

## Recommendation

**Use an MoR at launch; shortlist Paddle and Polar.**

- **Paddle:** the lowest-risk default. It is mature, India-supported, predictable at 5% + 50¢, and has solid proration and portal features.
- **Polar:** stronger if Team per-seat billing and time-to-ship matter most, and its younger track record and India payout path check out.
- **Avoid:** Lemon Squeezy (transition, PayPal-only payouts for Indian sellers).
- **Wait:** Stripe Managed Payments (no India) and Stripe India (invite-only).
- **Razorpay:** revisit only if Indian customers dominate revenue, or if an MoR's all-in fee exceeds the cost of running OSS and state-tax compliance in-house.

**Caveats:**

- MoR fees are 5–8% effective versus about 3% direct.
- Payouts are monthly or twice-monthly in USD, EUR or GBP, not INR. Budget for bank FX spread and SWIFT charges.
- Indian B2B customers get a foreign invoice.
- Indian-card renewals are subject to mandate delays.

## Open questions and suggested decisions

1. **[CA]** Confirm that MoR payouts qualify as export of services under IGST s.2(6)/s.13(2), including for end customers located in India. Confirm LUT filing (RFD-11) and whether GST registration is needed before the threshold.
2. **[CA]** Is the MoR's commission a separate import of services (reverse-charge GST) or a lower purchase price? What is the TDS position (not expected for inbound receipts) **[unverified]**?
3. **[CA]** FEMA: how do the 2026 Export Regulations (from 1 Oct 2026) apply to MoR payouts? Covers the 30-day service declaration, the 15-month realisation, and reporting of fees netted by the MoR.
4. **[CA]** Equalisation levy: per the Income Tax Department it no longer applies from 1 Apr 2025 [47]. Confirm there's no residual exposure.
5. **Decision:** is per-seat or per-Team pricing required at launch? If per-seat with self-serve seat assignment, Polar's native seats reduce build effort. If flat per-Team, Paddle is simpler.
6. **Decision:** do we need INR pricing and UPI for Indian customers at launch? If yes, confirm Paddle's or Polar's Indian-card and UPI mandate support in writing.
7. **Action:** request quotes and written answers from Paddle and Polar on: India payout currency and bank charges, the purpose code used on the wire, FIRA/e-BRC evidence per payout, and Indian e-mandate handling.
8. **Action:** re-check Stripe Managed Payments' India eligibility at the next milestone [6].

## Sources

1. Paddle, Pricing — https://www.paddle.com/pricing
2. Lemon Squeezy, Pricing — https://www.lemonsqueezy.com/pricing
3. Razorpay, Pricing (India) — https://razorpay.com/pricing/
4. Lemon Squeezy blog, "2026 Update: Lemon Squeezy + Stripe Managed Payments" (28 Jan 2026) — https://www.lemonsqueezy.com/blog/2026-update
5. Stripe Docs, Managed Payments — https://docs.stripe.com/payments/managed-payments
6. Stripe Docs, Managed Payments eligibility — https://docs.stripe.com/payments/managed-payments/eligibility
7. Stripe Docs, Accept international payments from India — https://docs.stripe.com/india-accept-international-payments
8. Stripe Support, India FAQ — https://support.stripe.com/questions/india-faq
9. Stripe Docs, Countries supported by Stripe Tax — https://docs.stripe.com/tax/supported-countries
10. Stripe, India pricing — https://stripe.com/in/pricing
11. Paddle Help, Which countries are supported by Paddle? — https://www.paddle.com/help/start/intro-to-paddle/which-countries-are-supported-by-paddle
12. Paddle Help, Which countries does Paddle charge sales tax or VAT for? — https://www.paddle.com/help/sell/tax/which-countries-does-paddle-charge-sales-tax-or-vat-for
13. Paddle Help, When and how do I get paid? — https://www.paddle.com/help/manage/get-paid/when-and-how-do-i-get-paid
14. Paddle Help, Can I be paid in my local currency? — https://www.paddle.com/help/manage/get-paid/can-i-be-paid-in-my-local-currency
15. Paddle Developer, Proration — https://developer.paddle.com/concepts/subscriptions/proration
16. Paddle Developer, Customer portal — https://developer.paddle.com/concepts/customer-portal
17. Paddle Help, Which payment methods do you support? — https://www.paddle.com/help/start/intro-to-paddle/which-payment-methods-do-you-support
18. Polar Docs, Supported countries — https://polar.sh/docs/merchant-of-record/supported-countries
19. Polar, Pricing — https://polar.sh/resources/pricing
20. Polar Docs, Seat-based pricing — https://polar.sh/docs/features/seat-based-pricing
21. Dodo Payments Docs, FAQ — https://docs.dodopayments.com/miscellaneous/faq
22. European Commission, VAT One Stop Shop – declare and pay — https://vat-one-stop-shop.ec.europa.eu/one-stop-shop/declare-and-pay-oss_en
23. RBI, Digital Payments – E-mandate Framework, 2026 (RBI/DPSS/2026-27/396, 21 Apr 2026) — https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13374
24. Stripe Docs, India recurring payments — https://docs.stripe.com/india-recurring-payments
25. Lemon Squeezy Docs, Fees — https://docs.lemonsqueezy.com/help/getting-started/fees
26. Lemon Squeezy Docs, Supported countries — https://docs.lemonsqueezy.com/help/getting-started/supported-countries
27. Dodo Payments, Pricing — https://dodopayments.com/pricing ; Accepted countries — https://docs.dodopayments.com/miscellaneous/accepted-countries-and-territories
28. Razorpay blog (first-party marketing, not docs), e-FIRA — https://razorpay.com/blog/e-fira/
29. Creem, Pricing — https://www.creem.io/pricing
30. FastSpring, Pricing — https://fastspring.com/pricing/
31. Lemon Squeezy Docs, Customer portal / Subscriptions — https://docs.lemonsqueezy.com/help/online-store/customer-portal ; https://docs.lemonsqueezy.com/guides/developer-guide/managing-subscriptions
32. Razorpay Docs, Update a Subscription — https://razorpay.com/docs/payments/subscriptions/update/
33. Razorpay Docs, International payments — https://razorpay.com/docs/payments/international-payments/
34. Stripe Support, Payout currency for Stripe accounts in India — https://support.stripe.com/questions/payout-currency-for-stripe-accounts-in-india
35. Stripe Support, FIRC/payment advice for international transactions in India — https://support.stripe.com/questions/firc-for-international-transactions-in-india
36. CBIC, IGST Act s.2 (definitions, incl. 2(6), 2(16), 2(17)) — https://taxinformation.cbic.gov.in/content/html/tax_repository/gst/acts/2017_IGST_Act/active/chapteri/section2_v1.00.html (text found via search; site certificate prevented direct fetch)
37. CBIC, IGST Act s.14 (OIDAR) — https://taxinformation.cbic.gov.in/content/html/tax_repository/gst/acts/2017_IGST_Act/active/chapterv/section14_v1.00.html
38. CBIC, IGST Act s.13 (place of supply; s.13(8)(b) omitted by Finance Act 2026) — https://taxinformation.cbic.gov.in/content/html/tax_repository/gst/acts/2017_IGST_Act/active/chapterv/section13_v1.00.html
39. CBIC, IGST Act s.16 (zero-rated supply) — https://taxinformation.cbic.gov.in/content/html/tax_repository/gst/acts/2017_IGST_Act/active/chaptervii/section16_v1.00.html
40. GST Council / CBIC, Sectoral FAQ booklet – Exports — https://gstcouncil.gov.in/sites/default/files/2024-02/sectoral-booklets-export.pdf
41. CBIC, CGST Rules, Rule 96A — https://taxinformation.cbic.gov.in/content/html/tax_repository/gst/rules/cgst_rules/active/chapter10/rule96a_v1.00.html
42. RBI, Master Direction – Export of Goods and Services (updated 17 Jul 2026) — https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=10395
43. DGFT, Self-certification of e-BRC FAQs — https://content.dgft.gov.in/Website/DGFT%20FAQs%20on%20Self-Certification%20of%20eBRC.pdf ; e-BRC portal — https://www.dgft.gov.in/CP/?opt=eBRC
44. Secondary: TaxTMI listing of FEMA 23(R)/(7)/2025-RB — https://www.taxtmi.com/notifications?id=144369 ; CorpLawUpdates on 2026 First Amendment — https://www.corplawupdates.in/updates/fema-export-realisation-period-9-months-first-amendment-2026 (the RBI PDF was behind a CAPTCHA)
45. RBI, FEMA (Export and Import of Goods and Services) Regulations, 2026 (FEMA 23(R)/2026-RB, 13 Jan 2026; in force 1 Oct 2026) — https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13277&Mode=0
46. RBI, Regulation of Payment Aggregator – Cross Border (RBI/2023-24/80, 31 Oct 2023) — https://rbi.org.in/Scripts/NotificationUser.aspx?Id=12561&Mode=0
47. Income Tax Department, Equalisation Levy — https://www.incometaxindia.gov.in/equalisation-levy3
