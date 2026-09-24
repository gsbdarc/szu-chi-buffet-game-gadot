# Unity buffet game: recovered ask list

Prepared September 14, 2026 from the supplied Google Drive folder and its attachments subfolder.

The intended deliverable is an online behavioral research simulator: participants browse a cafeteria buffet, choose individual portions, see those portions accumulate on a plate, and generate usable research data. The strongest later direction is a guided, constrained buffet-line experience with clear food views and smooth selection. Unity is the reconstruction platform specified by you; the reviewed source text establishes a web-based WebGL application but does not establish the original engine.

This list distinguishes Szu-chi Huang's direct instructions, the project brief approved on behalf of both researchers, collaborator requests, and developer proposals. Historical reports of progress are not verification that a feature worked. No current application or recovered source code was tested.

## Most important reconstruction decision

Use the February 2024 interaction revision as the best-supported later direction: show the entire buffet initially, move automatically to the first dish, then let participants move left/right between dishes with a plate or tray in front of them. Let them inspect dish information and add food without free rotation or zoom-out. This was proposed to prevent accidental selections, confusing camera motion, and unreadable food displays. It is a constrained presentation of the buffet, not an instruction to discard the 3D food assets. [S5, quoted February 8 email, pp. 1–2][S5]

The central research goal in Szu-chi's words: “see each food item clearly and to add items to their plate smoothly.” [S5][S5]

## A. Product asks directly attributable to Szu-chi

| ID | Deliverable / ask | Recovered detail and reconstruction implication | Evidence |
| --- | --- | --- | --- |
| A01 | Online buffet simulation | Show 15 food items, sequentially or together; let participants choose how many scoops of each to take and see the scoops appear on a plate. Fifteen is the original intake target, not a verified final menu count. | June 29, 2023 request attributed to Szu-chi, [S1, pp. 1–2][S1]. |
| A02 | Select and count individual portions | A participant must be able to move and track each piece or portion independently. Szu-chi objected to the chicken dish moving four pieces at once. | September 22, 2023, [S4, pp. 13–14][S4]. |
| A03 | Realistic food matching the reference document | Match the shared food/Word reference. Chicken parmesan was suggested for the chicken dish; nugget-like food was potentially acceptable if individually selectable. Salad needed to be greener and less pink. The final reference document is missing from the listed files. | September 22, 2023 and January 18, 2024, [S4, pp. 13–14][S4]; [S5, p. 6][S5]. |
| A04 | Comparable serving sizes across foods | Portions should be visually parallel, such as a string of chicken meat and a scoop of rice. Preserve relative scale across food types. | January 18, 2024, [S5, p. 6][S5]. |
| A05 | Realistic plate and food scale | Use a white, plate-like, regular buffet plate. It should not look large enough to fit more than five burgers; a pizza slice should occupy around one-quarter of the plate. These are visual scale examples, not an explicit five-burger software limit. | September 22, 2023 and January 18, 2024, [S4, pp. 13–14][S4]; [S5, p. 6][S5]. |
| A06 | Food stays on the plate and looks natural | Eliminate floating, airborne or drifting food and implausible relative sizes, such as pizza much smaller than a burger. Food should look and move as realistically as possible. | September 22, 2023, [S4, pp. 13–14][S4]. |
| A07 | Smooth assisted placement | Predetermined food positions or patterns on the plate are acceptable if the experience feels smooth. Physics-based free placement is not required by this approval. | September 20, 2023, [S4, pp. 9–10][S4]. |
| A08 | Believable cafeteria atmosphere | Provide a reasonable cafeteria layout that does not feel empty, with more silhouettes and sound effects as needed. | September 22, 2023, [S4, pp. 11–14][S4]. |
| A09 | Reliable buffet navigation | Make it easy to move down the line; prevent plate movement from triggering unintended food selections, zooming, or sideways camera motion. | September 22, 2023 and February 2024 revision, [S4, pp. 13–14][S4]; [S5, pp. 1–2][S5]. |
| A10 | Food selection from a reasonable distance | Do not allow participants to take food while far from that dish. The later station-by-station design supplies a natural way to meet this requirement. | September 22, 2023, [S4, p. 14][S4]. |
| A11 | Opening buffet overview | Begin with a grand view of the full buffet, then automatically direct or zoom the participant to the first dish. | February 2024 revision, quoted header February 8, [S5, p. 2][S5]. |
| A12 | Guided dish-by-dish interaction | Start the game with the plate/tray in front of the participant and the first dish visible. Move right to later dishes and left to earlier dishes. Constrain user zoom-out and rotation. | February 2024 revision, [S5, p. 2][S5]. |
| A13 | Clear food views and accessible dish information | Each dish and its signage must be legible. Participants should be able to click for more food information, add food, and continue along the buffet. The menu button was positively acknowledged. | February 2024 revision, [S5, p. 2][S5]. |
| A14 | Working plate screenshots | Include the basic screen-capture function from the original briefing. Keep this function even if the phone-camera visual treatment is removed. | September 22, 2023, [S4, pp. 11–14][S4]. |
| A15 | Correct, analysis-compatible data | Count one portion/item at a time correctly. Work with David on the data grid/coding system, then share it with Samina for analysis compatibility review. | September 20 and 22, 2023, [S4, pp. 9–10, 14][S4]. |
| A16 | Research-ready pilot build | Finish the original brief and the remaining revisions so the software is usable with research participants. The January food revisions were explicitly required before piloting. | January 18 and February 2024, [S5, pp. 1–2, 6, 8][S5]. |

## B. Additional requirements in the approved project brief

The brief was shared July 20, 2023. On July 28, Samina wrote that it looked good to both her and Szu-chi, after Nick explicitly requested agreement on scope. These are approved project requirements, although they are not all separate emails written by Szu-chi. [S3, pp. 1–3][S3]

| ID | Deliverable / ask | Recovered detail and qualification | Evidence |
| --- | --- | --- | --- |
| B01 | Environment and asset package | 10–15 3D food models, 3–5 scene models, one environment, a buffet-line table model, and a panoramic university cafeteria hall. | [S2, Project Requirements][S2]. |
| B02 | Hosted WebGL application | A web experience that can be hosted and instantiated for multiple users; hosting on a server chosen by the client. This does not establish real-time multiplayer as a requirement. | [S2, Project Requirements; Additional Requirements][S2]. |
| B03 | Web and mobile interaction | Support web and mobile devices, and evaluate usability/performance across devices and browsers. Later laptop-and-mouse optimization was a developer limitation, not an explicit researcher waiver of mobile support. | [S2, Interactivity; Mitigation][S2]; [S5, p. 7][S5]. |
| B04 | Landing pages and introductory guides | Provide landing pages and instructions for interacting with the simulator. Exact final text and images are not recovered. | [S2, Interactivity Requirements][S2]. |
| B05 | Drag-and-drop food selection | Place food onto one or more plates using drag-and-drop with 2D/3D effects. Later correspondence introduced click-to-add and guided navigation; the exact final mix of gestures needs confirmation. | [S2, Overview; Interactivity][S2]; [S5, pp. 1, 9–10][S5]. |
| B06 | Session identity and persistence | URL-trackable sessions logged and stored in a database. Specific URL parameter names and identifier formats are not given. | [S2, Interactivity Requirements][S2]. |
| B07 | Research measurements and export | Track food types, scoops per plate, and time spent in the simulation. Produce accessible output for study analysis, developed with the Behavioral Lab engineer. Exact event definitions and export schema are not supplied. | [S2, Overview; Requirements; Mitigation][S2]. |
| B08 | Per-user screenshot control and image logs | Screenshot functionality must be controllable per user and permit image logs of food plates. The exact condition assignment and capture trigger remain unspecified. | [S2, Interactivity Requirements][S2]. |
| B09 | Settings for participant subgroups | Make application settings customizable for different participant subgroups. The reviewed brief does not enumerate those settings or conditions. | [S2, Additional Requirements][S2]. |
| B10 | Sandbox evaluation and final signoff | Provide a sandbox that does not require server installation for evaluation of performance, bugs, and improvements, followed by final delivery/signoff. | [S2, Timeline; Additional Requirements][S2]. |

## C. Research-team follow-up asks

| ID | Deliverable / ask | Requester and recovered detail | Evidence |
| --- | --- | --- | --- |
| C01 | Qualtrics-embedded simulator | April 26, 2024 help request submitted by David for Samina and Szu-chi: integrate the dining simulator into a Qualtrics survey using an iFrame. | [S6, p. 1][S6]. |
| C02 | Simulator-to-Qualtrics data transfer | Samina requested verification that simulation data passed into and was stored as Qualtrics embedded data. This is more than merely displaying the game inside the survey. | January 22–23, 2025, [S7, pp. 1–3][S7]. |
| C03 | Prolific-compatible study setup | Check the setup of `online_buffet_V1_1_21_25` for Prolific; the prior version was for SIM. Samina wanted to be able to repeat the setup herself after the first validation. This was not simply a request to post the study on Prolific. | [S7, pp. 1–3][S7]. |
| C04 | Review a small food sample before full production | Samina asked to see one or two updated food items first, check their size/look, and adjust before the rest were completed. | January 27 and 29, 2024, [S5, pp. 3–5][S5]. |
| C05 | Fix known plate/food interaction defects | Samina flagged a floating kale salad and a disappearing/lost plate after fast movement. Nick flagged items stacking inside one another and hanging off the plate. These reinforce A06 and A09. | August 28 and September 20, 2023, [S4, pp. 5, 8][S4]; January 29, 2024, [S5, pp. 3–4][S5]. |

## D. Developer-reported behavior and remaining work

These details help reconstruct the later build, but should not be represented as independent professor requests or verified completed features.

| ID | Behavior / work item | What the historical email actually establishes | Evidence |
| --- | --- | --- | --- |
| D01 | Button-based navigation and camera views | After his February 8 call with Szu-chi, JD reported linear button-based navigation without dragging the plate; start/end scenes, buttons and camera movement; and return-to-food/return-to-plate views. This is developer corroboration of A09–A13. | February 8, 2024, [S5, p. 1][S5]. |
| D02 | Click-to-add | Outstanding on February 8; double-click was proposed February 10; click events were reported implemented February 12. Sandwiches and beef/chicken skewers still broke when revisited and selected again. Do not assume double-click was the final intended gesture. | [S5, pp. 1, 9–10][S5]. |
| D03 | Plate grouping and assisted food placement | JD reported assigned positions and grouping by food type, and preventing the plate from entering stations. Auto-movement after an accidental release remained in progress for some foods. | January 11 and 30, 2024, [S5, pp. 3, 7][S5]. |
| D04 | Smaller main plate, separate dessert plate, dynamic scaling | A smaller plate and separate dessert plate were reported in January. Dynamic plate resizing/food-size optimization was still outstanding in February. The emails do not establish the final scale rules or whether dessert separation was explicitly approved. | [S5, pp. 1, 4–5, 9–10][S5]. |
| D05 | Menu and image-based dish information | JD reported food hotspot images, 17 renders, and a menu popup with images. Further dish-information buttons and UI enhancements were still on the February 12 list. | January 28 and February 5/12, 2024, [S5, pp. 2–4, 10][S5]. |
| D06 | Stanford styling and ambient sound | Stanford logo/colors on the loading screen, UI color work, normalized item-name notifications, improved illustrated instructions, and cafeteria audio were reported or planned. Samina liked the background sound. Logo/branding is not separately documented as a professor ask. | January 24–27, 2024, [S5, pp. 5–6][S5]. |
| D07 | Performance, camera visibility, and final publishing | JD reported compressing the experience from about 300 MB to under 50 MB, removing view obstructions, labeling previous/next buttons with food names, and restricting panning. Bug fixes, optimization, final polish and publishing remained on his lists. These sizes are historical reports, not a new performance target. | January 11 and February 8–12, 2024, [S5, pp. 1, 7, 9–10][S5]. |
| D08 | Firebase backend and session-linked screenshots | In September 2023 JD reported live Firebase logging of session IDs, screenshots, user activity and food selections, including name/email information. Authentication/sign-up pages were proposed. The evidence does not make name/email collection or mandatory login a research requirement. | September 22, 2023, [S4, p. 10][S4]. |

## E. Explicitly optional, simplified, or unresolved scope

| Item | Treatment for reconstruction | Evidence |
| --- | --- | --- |
| Steam on food and extra visual effects | Szu-chi explicitly allowed steam to be dropped to stay within budget. Do not treat it as essential. | September 22, 2023, [S4, pp. 11–14][S4]. |
| Phone-camera-style screen capture | Szu-chi allowed its visual treatment to be simplified/dropped if it cost extra. The underlying screenshot function remains required. | [S4, pp. 11–14][S4]. |
| End-of-experience verification page/session ID | Explicitly optional in the brief. This does not make database session tracking optional. | [S2, Interactivity Requirements][S2]. |
| Free camera movement | The later professor direction constrains movement. Do not recreate unrestricted navigation merely because an earlier demo had it. | [S5, pp. 1–2][S5]. |
| Mobile support | Remains in the original scope. The later emails acknowledge problems but do not contain a clear decision to remove it. | [S2][S2]; [S5, pp. 5, 7][S5]. |
| Exact final food count | Initial request: 15 foods. Brief: 10–15 models. JD later reported 17 renders and nearly 100 positioned food items. These are different kinds of counts; they do not establish a 100-dish menu. | [S1][S1]; [S2][S2]; [S5, pp. 2–3, 7][S5]. |
| Scoring, consumption and computed food waste | The recovered asks describe food selection and measurement for food-waste research. No explicit scoring, nutrition target, eating phase, leftover measurement, or waste-calculation formula was located in the reviewed text. | Scope of [S1][S1], [S2][S2], [S4][S4], [S5][S5]. |

## F. Delivery, recovery, and administrative asks

These are historical requests, separate from the participant-facing game specification. Old dates and amounts are not a proposed new schedule or budget.

| ID | Ask | Date / evidence |
| --- | --- | --- |
| F01 | Provide an early mockup for pilot studies | June 29, 2023 intake asked for a mockup in about a month and pilots in early-to-mid August. The brief separately targeted a sandbox 14 days after contract signing and final signoff at 21 days, with tentative dates. [S1][S1]; [S2][S2]. |
| F02 | Provide demo links with focused review instructions | Szu-chi asked for a link, instructions on what to focus on, and clarity about which features were ready for feedback versus still in progress. Repeated August 16, September 20/22, and October 5, 2023. [S3, p. 4][S3]; [S4, pp. 9, 12–15][S4]. |
| F03 | Maintain review and communication opportunities | Brief: weekly meetings, email updates/change requests, regular developer updates and availability for calls twice weekly. Szu-chi asked for rapid clarification if feedback was unclear before revisions proceeded. [S2][S2]; January 18, 2024, [S5, p. 6][S5]. |
| F04 | Keep baseline work within the agreed fixed bid | Szu-chi reiterated $7,500 on September 22, 2023 and declined extra-cost embellishments. On January 18, 2024 she authorized an additional 20 hours; in February she confirmed a $5,000 final invoice following her call with JD. These are separate historical decisions, not one unchanged budget. [S4, p. 14][S4]; [S5, pp. 6, 8–9][S5]. |
| F05 | Restore access so studies can run | Szu-chi requested access ASAP on April 14, 2026 and asked David on May 9 to resolve it that week. [S8, April 14 and May 9 messages][S8]. |
| F06 | Give more research-team members access | Szu-chi asked to share access with Nick and Samina on May 9, 2026. Nick subsequently requested owner status and access instructions for both. Current appropriate roles still need to be set for a rebuilt project. [S8, May 9–10 messages][S8]. |
| F07 | Provide a recovery timeline and cost estimate | On May 19, 2026 Szu-chi asked David to collaborate with Joe on an estimated timeline and potential cost. She also expected a retained institutional copy that was not removed without the team's knowledge. [S8, May 19 message][S8]. |
| F08 | Pursue every recovery lead and report progress | Szu-chi requested updates on April 20 and asked to contact every lead and locate a copy on May 21, 2026. This report records those asks; no outreach was performed. [S8][S8]. |
| F09 | Move the application to infrastructure the team can maintain | Nick proposed a server under team control and subsequent DARC support, avoiding dependence on the external developer for repairs. This is Nick's operational request, not a separate direct professor specification. April 17–20, 2026, [S8][S8]. |
| F10 | Process the PO and agreed invoices | Szu-chi asked for prompt PO approval, use of available FY23 funding before the August finance deadline, and upfront/final payment arrangements. In February 2024 she directed processing the single $5,000 invoice against her BG&S fund. [S9, August 1, 2023 messages][S9]; [S5, pp. 8–9][S5]. |
| F11 | Reconcile funding years and accounts | February 8–22, 2024: check when/where the earlier payments posted; explain the account change; transfer the expense to BG&S; and confirm updated balances against the budget sheet. Account identifiers are omitted here because they do not help reconstruction. [S4, pp. 16–17][S4]; [S9, February 20–22 messages][S9]. |

Routine scheduling exchanges, thanks, duplicate quoted messages and unrelated vendor payment-detail changes are not separate deliverables. The later restitution letter requests reimbursement or funded reconstruction with retention arrangements; it is a separate letter attributed to Research Hub leadership, not an email ask authored by Szu-chi. [S11][S11]

## G. Reconstruction information and missing evidence

**Historical project identity.** The project was called the 3D Interactive Food Waste Simulator, Dining Hall Simulator, or Stanford Cafeteria Simulator. The study title “Goal Attainment and Its Effects” and IRB number 33309 appear in the invoices and the January 2025 request. The April 2024 ticket contains 00000 instead; treat that as inconsistent source data, not a verified protocol identifier. [S6][S6]; [S7][S7]; [S12][S12]; [S13][S13]; [S14][S14]

**People and roles.** Szu-chi Huang was the PI/project sponsor; Samina Lutfeali was the lead PhD student and named project manager; Joseph Douglas (Joe/JD) was the developer. David Perlman supported data and survey integration; Nicholas Hall coordinated Behavioral Lab support. “SuChee Huang” is Szu-chi's alternate sender identity in the chains, supported by the original intake's contact details. [S1][S1]; [S2][S2]

**Historical deployment.** The emails document Firebase/GCP project `stanford-cafeteria-simulator`, the historical web.app address, and `stanford-cafeteria-simulator.firebaseapp.com/index.html`. These are historical identifiers, not a working deployment verified in this review. Early development used changing Glitch URLs. Early discussion of MySQL and MongoDB does not establish the final database product/schema. [S4, pp. 6–10][S4]; [S15, pp. 1–2][S15]

**Qualtrics artifacts to locate.** `online_buffet_sim_bothviews_v01` is identified in the retrospective timeline as David's integration/playground survey. `online_buffet_V1_1_21_25` is named directly in Samina's January 2025 ticket. The survey name “bothviews” alone does not prove what experimental conditions existed. The timeline says integration/data transfer was completed, but the supplied request emails do not include the validation results themselves. [S10][S10]; [S7][S7]

**Food asset clues, not a final menu.** The emails mention chicken parmesan/nugget-like chicken, burgers, pizza, rice, pasta, salads including kale/garden salad, mixed fruit, mixed vegetables, sandwiches, beef and chicken skewers, and desserts/cupcakes. Some are proposed replacements or prototype examples. JD described mixed fruit as dragon fruit, pineapple, mango and watermelon; mixed vegetables as potatoes, mushrooms, kale and cucumbers. These details help locate assets but cannot replace the missing approved menu/reference. [S4][S4]; [S5, pp. 2–7, 10][S5]

**Historical cost.** The three invoice face amounts are $3,000 + $4,500 + $5,000 = $12,500. The timeline and restitution letter describe them as paid. They are not a current reconstruction estimate. The brief's initial payment split differs from the invoices, and the final invoice includes already-incurred overages plus up to 60 further completion hours; do not equate that with the separate January email's 20-hour authorization. [S2][S2]; [S5][S5]; [S10][S10]; [S12][S12]; [S13][S13]; [S14][S14]

**Recovery status is reported, not independently established here.** Early May emails hoped Joe had a backup. The later timeline/letter says no usable contractor copy remained; the June Google support chain reports permanent deletion. Do not treat early backup speculation as proof that usable source exists. This ask-list review does not determine legal responsibility or independently establish the deletion mechanism. [S8][S8]; [S10][S10]; [S11][S11]; [S15, June 17 message][S15]

The most consequential unresolved items are:

- **Final food reference:** the shared Word document, food list, approved portions, food order, and original image/model assets. It is referenced but not present as a standalone file in the enumerated folder contents.
- **Experiment conditions:** what changes by subgroup, how screenshot availability is controlled, and any view manipulation. Neither randomization rules nor full study instructions are specified in the recovered asks.
- **Exact data contract:** URL fields, session-to-participant matching, food/portion codes, timing definitions, screenshot storage/linking, and Qualtrics embedded-data field names.
- **Final controls:** whether drag-and-drop survived alongside click-to-add; single versus double click; the final dessert-plate and plate-size behavior; and precise start/end completion behavior.
- **Supported devices:** whether mobile must be restored to original scope or a desktop-only study is now acceptable.
- **Final accepted build and assets:** no source project, complete final-build package, formal final acceptance record, or final menu appears among the 21 listed files. Linked demo videos and image-only content were not visually verified in this text review. Early demo videos must not be mistaken for the later accepted interaction design.

**Recommended reconstruction handoff, not a recovered historical ask:** deliver the Unity source project and assets, a working web build, the data-field mapping and Qualtrics integration, and a short deployment/backup guide with named institutional maintainers. Demonstrate a full participant run from Qualtrics into the buffet and back, matching plate contents and screenshots to exported data. Validate against A01–A16, the still-applicable brief requirements, and C01–C03 before claiming research readiness.

## Source index and review limits

The supplied folder contained 13 files and one attachments subfolder with eight files: 21 files total (18 PDFs and three Google Docs). Readable text was retrieved for all 21; the two timeline documents returned identical text. Email chains contain extensive repeated quotations, and some hide quoted text or refer to meetings, attachments and images not reproduced in readable text. The list is comprehensive for the substantive asks found in that available text, not proof that every historical instruction survives in the archive. Message dates are used rather than Drive upload dates. February quoted headers show timezone-related date shifts, so the interaction redesign is identified as the February 2024 exchange where appropriate.

- **S1** — [Email 2023-06 - Fwd_ [DARC Request Form] - Building a simulation survey for our food waste buffet study_.pdf](https://drive.google.com/file/d/191I6_Ix_P-uXUSLIvDSs5VC7yFm9H4q2/view?usp=drivesdk)
- **S2** — [Project Summary_ 3D Interactive Food Waste Simulator.pdf](https://drive.google.com/file/d/1Sjx_I_LCGNeJ-lPuwhSHg39y_BYrKSIx/view?usp=drivesdk)
- **S3** — [Email 2023-07 - Document shared with you_ _Project Summary_ 3D Interactive Food Waste Simulator_.pdf](https://drive.google.com/file/d/1ilK95LNmcEMz3CSR7CvdTmuUtkuiIs2U/view?usp=drivesdk)
- **S4** — [Email 2023-08 - 3D Interactive Food Waste Simulator (8_28_Update).pdf](https://drive.google.com/file/d/1zDzLKfUCrUrJtm70IotHxYvRlUcyt0fv/view?usp=drivesdk)
- **S5** — [Email 2024-02 - Re_ Cafeteria Simulator Demo.pdf](https://drive.google.com/file/d/1Fpv6sGz0_YTppPAconx57LhdvctZfG5k/view?usp=drivesdk)
- **S6** — [Email 2024-04 - Other Help Request Samina Lutfeali - Szu-Chi Huang Fri, Apr 26, 2024 1_32 PM.pdf](https://drive.google.com/file/d/197SOi1SV1ozkKJuAsMb6mWVtYY4cOnws/view?usp=drivesdk)
- **S7** — [Email 2025-01 - Other Help Request Samina Lutfeali - Szu-Chi Huang Wed, Jan 22, 2025 4_42 PM.pdf](https://drive.google.com/file/d/1LmisxjzTUfi1Ytrr5QhrylvCWX1F8rH5/view?usp=drivesdk)
- **S8** — [Email 2026-04 - Re Document shared with you Project Summary 3D Interactive Food Waste Simulator.pdf](https://drive.google.com/file/d/1EjUVb_hnuy4amRMM4jVxlS0hQA5INL1C/view?usp=drivesdk)
- **S9** — [Email 2023-07 to 2024-02 - payment to outside developer.pdf](https://drive.google.com/file/d/16Txs3aSUFFfAEll35QMZZA_deAS7LPCD/view?usp=drivesdk)
- **S10** — [* Szu-chi's lost cafeteria simulation project timeline](https://docs.google.com/document/d/11gYS3ikTRHcgk56_QtlH6a6cvILDbeNpAo50X4IuA0U/edit?usp=drivesdk)
- **S11** — [UIT_Restitution_Letter](https://docs.google.com/document/d/1-q8HP-6q8U3pOr-66C9Mal_tiLrqhLpQXEdf0UPDWeQ/edit?usp=drivesdk)
- **S12** — [Invoice-1-for-PO63222239.pdf](https://drive.google.com/file/d/1JVkwoD4e4E5S-2SYvQ6_PPb6VpYNdEkH/view?usp=drivesdk)
- **S13** — [Invoice-2-for-PO63222239.pdf](https://drive.google.com/file/d/1M7juXV0tGb4Gd8bHoJ1sNDuyttpkveZ_/view?usp=drivesdk)
- **S14** — [Invoice-3-for-PO63222239.pdf](https://drive.google.com/file/d/1erhWJzFHsfNAwzlNXu4otkapbOTPwMcl/view?usp=drivesdk)
- **S15** — [Email 2026-05:06 - Fwd_ Question about Google Firebase.pdf](https://drive.google.com/file/d/1H-lfUIKfxCLmX1HvIJD4JbEJpbaL2sBH/view?usp=drivesdk)
- **S16** — [Email 2026-04-17 - Joe Douglas contact.pdf](https://drive.google.com/file/d/1NBcBbRjLQYadjQFYARLZG6_0a4SJ6Ray/view?usp=drivesdk)
- **S17** — [Email 2026-05 - project David summary.pdf](https://drive.google.com/file/d/1baJnd2h6r9Nt03maw0De18HTJWGkcgc0/view?usp=drivesdk)
- **S18** — [Email 2026-05-19 - one long shot.pdf](https://drive.google.com/file/d/1dJrsoAcrqvAcSPwUOhflkun67CLXQ2bx/view?usp=drivesdk)
- **S19** — [Email 2026-05-10 - Fwd_ Project Weekly Summary Report.pdf](https://drive.google.com/file/d/18YEqt3i-3QRWegpD78CMnM3rtAZ5Vjfe/view?usp=drivesdk)
- **S20** — [Email 2026-05-10 - Fwd_ Incident INC02100244 has been resolved.pdf](https://drive.google.com/file/d/1Lxf5LBLQJIXKFies0E1Oil5R-h0Sw7J4/view?usp=drivesdk)
- **S21** — [* Timeline: Szu-chi Huang lost cafeteria simulation project (copy)](https://docs.google.com/document/d/1T7dup1KGTeWYRusT-pPiYwG1DVTRZM6vcoy0APJ6WiM/edit?usp=drivesdk)

[S1]: https://drive.google.com/file/d/191I6_Ix_P-uXUSLIvDSs5VC7yFm9H4q2/view?usp=drivesdk
[S2]: https://drive.google.com/file/d/1Sjx_I_LCGNeJ-lPuwhSHg39y_BYrKSIx/view?usp=drivesdk
[S3]: https://drive.google.com/file/d/1ilK95LNmcEMz3CSR7CvdTmuUtkuiIs2U/view?usp=drivesdk
[S4]: https://drive.google.com/file/d/1zDzLKfUCrUrJtm70IotHxYvRlUcyt0fv/view?usp=drivesdk
[S5]: https://drive.google.com/file/d/1Fpv6sGz0_YTppPAconx57LhdvctZfG5k/view?usp=drivesdk
[S6]: https://drive.google.com/file/d/197SOi1SV1ozkKJuAsMb6mWVtYY4cOnws/view?usp=drivesdk
[S7]: https://drive.google.com/file/d/1LmisxjzTUfi1Ytrr5QhrylvCWX1F8rH5/view?usp=drivesdk
[S8]: https://drive.google.com/file/d/1EjUVb_hnuy4amRMM4jVxlS0hQA5INL1C/view?usp=drivesdk
[S9]: https://drive.google.com/file/d/16Txs3aSUFFfAEll35QMZZA_deAS7LPCD/view?usp=drivesdk
[S10]: https://docs.google.com/document/d/11gYS3ikTRHcgk56_QtlH6a6cvILDbeNpAo50X4IuA0U/edit?usp=drivesdk
[S11]: https://docs.google.com/document/d/1-q8HP-6q8U3pOr-66C9Mal_tiLrqhLpQXEdf0UPDWeQ/edit?usp=drivesdk
[S12]: https://drive.google.com/file/d/1JVkwoD4e4E5S-2SYvQ6_PPb6VpYNdEkH/view?usp=drivesdk
[S13]: https://drive.google.com/file/d/1M7juXV0tGb4Gd8bHoJ1sNDuyttpkveZ_/view?usp=drivesdk
[S14]: https://drive.google.com/file/d/1erhWJzFHsfNAwzlNXu4otkapbOTPwMcl/view?usp=drivesdk
[S15]: https://drive.google.com/file/d/1H-lfUIKfxCLmX1HvIJD4JbEJpbaL2sBH/view?usp=drivesdk
[S16]: https://drive.google.com/file/d/1NBcBbRjLQYadjQFYARLZG6_0a4SJ6Ray/view?usp=drivesdk
[S17]: https://drive.google.com/file/d/1baJnd2h6r9Nt03maw0De18HTJWGkcgc0/view?usp=drivesdk
[S18]: https://drive.google.com/file/d/1dJrsoAcrqvAcSPwUOhflkun67CLXQ2bx/view?usp=drivesdk
[S19]: https://drive.google.com/file/d/18YEqt3i-3QRWegpD78CMnM3rtAZ5Vjfe/view?usp=drivesdk
[S20]: https://drive.google.com/file/d/1Lxf5LBLQJIXKFies0E1Oil5R-h0Sw7J4/view?usp=drivesdk
[S21]: https://docs.google.com/document/d/1T7dup1KGTeWYRusT-pPiYwG1DVTRZM6vcoy0APJ6WiM/edit?usp=drivesdk
