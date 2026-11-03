# J02 disabled-option sampling investigation

The full main J02 action passed, but the following unavailable-map check twice read `isDisabled=false` immediately after changing the parent. A subsequent diagnostic read from the same locator showed the correct unavailable map and a `disabled` attribute. An isolated real Chrome probe with the same imported fixture also produced the correctly disabled option. A static disabled-option probe confirmed Playwright normally reports such options disabled.

The initial timing hypothesis was insufficient: waiting for the actual disabled DOM property did not change the reported Playwright result. Product edits and timing guesses were paused for source-level investigation.

The installed Playwright `playwright-core/lib/coreBundle.js` explains the result: `elementState(node, state)` uses `retarget(..., "follow-label")` for disabled/enabled checks. An OPTION inside the application's wrapping LABEL is retargeted to that label's SELECT control. The SELECT is correctly enabled while its unavailable OPTION is disabled. A minimal real Chrome reproduction with a labelled SELECT returned isDisabled=false, native option.disabled=true and option.matches(':disabled')=true. The same OPTION without a wrapping LABEL returned isDisabled=true.

The corrected check requires the actual selected parent, then asserts both the exact OPTION's native disabled property and its native CSS disabled state. It retains direct API rejection and exact unchanged-database assertions. No product markup, validation or scientific requirement is loosened to satisfy a helper that was inspecting another control. Independent replay remains required.
