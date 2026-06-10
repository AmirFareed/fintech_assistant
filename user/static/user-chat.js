(function () {
    if (window.FintechUserChatWidget && window.FintechUserChatWidget.mounted) {
        return;
    }

    const currentScript = document.currentScript || (function () {
        const scripts = document.getElementsByTagName("script");
        return scripts[scripts.length - 1] || null;
    })();

    const scriptUrl = currentScript ? new URL(currentScript.src, window.location.href) : null;
    const scriptOrigin = scriptUrl ? scriptUrl.origin : window.location.origin;
    const scriptPath = scriptUrl ? scriptUrl.pathname : "/user/static/user-chat.js";
    const assetBasePath = scriptPath.replace(/\/user-chat\.js$/, "");
    const defaultStylesheetUrl = `${scriptOrigin}${assetBasePath}/user-chat.css`;
    const defaultApiEndpoint = `${scriptOrigin}/api/chat`;
    const defaultLogoUrl = `${scriptOrigin}/static/fintech-logo.png`;

    const DEFAULTS = {
        apiEndpoint: defaultApiEndpoint,
        logoUrl: defaultLogoUrl,
        stylesheetUrl: defaultStylesheetUrl,
        assistantName: "FinTech AI Assistant",
        assistantTagline: "",
        launcherLabel: "Ask Me",
        launcherSubtitle: "",
        welcomeTitle: "Welcome to FinTech AI Assistant!",
        welcomeMessage: "",
        welcomePrompt: "Choose a question or ask your own",
        suggestions: [
            "What is PSID?",
            "How to generate PSID?",
            "How to verify PSID?",
            "How to make a digital payment through PSID?",
            "How to pay via Easypaisa using PSID?",
            "How to pay via JazzCash using PSID?",
            "What banks support PSID payment?",
            "Is PSID payment secure?",
            "What if my PSID payment fails?"
        ],
        initialOpen: false,
        theme: "light",
        movable: true
    };

    function ensureStylesheet(stylesheetUrl) {
        if (!stylesheetUrl) {
            return;
        }

        const normalizedTarget = new URL(stylesheetUrl, window.location.href).href;
        const existingLinks = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
        const alreadyLoaded = existingLinks.some(function (link) {
            try {
                return new URL(link.href, window.location.href).href === normalizedTarget;
            } catch (error) {
                return link.href === normalizedTarget;
            }
        });

        if (alreadyLoaded) {
            return;
        }

        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = normalizedTarget;
        document.head.appendChild(link);
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function formatMessage(value) {
        return escapeHtml(value)
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
            .replace(/^### (.+)$/gm, "<strong>$1</strong>")
            .replace(/^## (.+)$/gm, "<strong>$1</strong>")
            .replace(/^# (.+)$/gm, "<strong>$1</strong>")
            .replace(/\n/g, "<br>");
    }

    function isRtl(language) {
        return language === "ur" || language === "ps";
    }

    function autosize(textarea) {
        textarea.style.height = "auto";
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
    }

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function mountWidget() {
        const config = Object.assign({}, DEFAULTS, window.FintechUserChatWidgetConfig || {});
        ensureStylesheet(config.stylesheetUrl);
        if (document.querySelector(".fintech-widget-root")) {
            return;
        }

        const root = document.createElement("section");
        root.className = "fintech-widget-root";
        const launcherSubtitleMarkup = config.launcherSubtitle
            ? `<span class="fw-launcher-subtitle">${escapeHtml(config.launcherSubtitle)}</span>`
            : "";
        const assistantTaglineMarkup = config.assistantTagline
            ? `<span class="fw-brand-subtitle">${escapeHtml(config.assistantTagline)}</span>`
            : "";
        const welcomeMessageMarkup = config.welcomeMessage
            ? `<p>${escapeHtml(config.welcomeMessage)}</p>`
            : "";
        const welcomePromptMarkup = config.welcomePrompt
            ? `
                        <div class="fw-welcome-divider">
                            <span>${escapeHtml(config.welcomePrompt)}</span>
                        </div>`
            : "";

        root.innerHTML = `
            <section class="fw-panel" aria-label="${escapeHtml(config.assistantName)}">
                <header class="fw-header">
                    <div class="fw-brand">
                        <img class="fw-brand-logo" src="${escapeHtml(config.logoUrl)}" alt="${escapeHtml(config.assistantName)} logo">
                        <div class="fw-brand-copy">
                            <span class="fw-brand-title">${escapeHtml(config.assistantName)}</span>
                            ${assistantTaglineMarkup}
                            <span class="fw-brand-status">
                                <span class="fw-status-dot" aria-hidden="true"></span>
                                <span>Online now</span>
                            </span>
                        </div>
                    </div>
                    <div class="fw-header-actions">
                        <button type="button" class="fw-icon-btn" data-action="reset" aria-label="Clear conversation">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <path d="M3 6h18"></path>
                                <path d="M8 6V4h8v2"></path>
                                <path d="M19 6l-1 14H6L5 6"></path>
                            </svg>
                        </button>
                        <button type="button" class="fw-icon-btn" data-action="close" aria-label="Close chat">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <path d="M18 6 6 18"></path>
                                <path d="M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                </header>
                <div class="fw-body">
                    <section class="fw-welcome" data-role="welcome">
                        <h2>${escapeHtml(config.welcomeTitle)}</h2>
                        ${welcomeMessageMarkup}
                        ${welcomePromptMarkup}
                        <div class="fw-suggestion-grid" data-role="welcome-suggestions"></div>
                    </section>
                    <div class="fw-messages" data-role="messages"></div>
                </div>
                <footer class="fw-footer">
                    <div class="fw-toolbar">
                        <label class="fw-language-wrap" aria-label="Choose response language">
                            <span class="fw-language-icon" aria-hidden="true">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="9"></circle>
                                    <path d="M3 12h18"></path>
                                    <path d="M12 3a14 14 0 0 1 0 18"></path>
                                    <path d="M12 3a14 14 0 0 0 0 18"></path>
                                </svg>
                            </span>
                            <select class="fw-language-select" data-role="language">
                                <option value="en">English</option>
                                <option value="ur">Urdu</option>
                                <option value="ps">Pashto</option>
                            </select>
                        </label>
                    </div>
                    <div class="fw-input-row">
                        <textarea class="fw-input" data-role="input" rows="1" placeholder="Ask about PSID, Easypaisa, JazzCash..." aria-label="Your message"></textarea>
                        <button type="button" class="fw-voice" data-role="voice" aria-label="Start voice input" title="Start voice input">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <path d="M12 3a3 3 0 0 1 3 3v6a3 3 0 1 1-6 0V6a3 3 0 0 1 3-3z"></path>
                                <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                                <path d="M12 19v3"></path>
                            </svg>
                        </button>
                        <button type="button" class="fw-send" data-role="send" aria-label="Send message">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <line x1="22" y1="2" x2="11" y2="13"></line>
                                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                            </svg>
                        </button>
                    </div>
                    <p class="fw-voice-status" data-role="voice-status" hidden></p>
                </footer>
            </section>
            <button type="button" class="fw-launcher" aria-expanded="false" aria-label="${escapeHtml(config.launcherLabel)}">
                <span class="fw-launcher-icon" aria-hidden="true">
                    <img class="fw-launcher-logo" src="${escapeHtml(config.logoUrl)}" alt="">
                    <span class="fw-launcher-online-dot"></span>
                </span>
                <span class="fw-launcher-text">
                    <span class="fw-launcher-label">${escapeHtml(config.launcherLabel)}</span>
                    <span class="fw-launcher-status">
                        <span class="fw-launcher-status-dot" aria-hidden="true"></span>
                        <span>Online now</span>
                    </span>
                </span>
            </button>
        `;

        document.body.appendChild(root);

        const panel = root.querySelector(".fw-panel");
        const launcher = root.querySelector(".fw-launcher");
        const brand = root.querySelector(".fw-brand");
        const welcome = root.querySelector('[data-role="welcome"]');
        const welcomeSuggestions = root.querySelector('[data-role="welcome-suggestions"]');
        const messages = root.querySelector('[data-role="messages"]');
        const input = root.querySelector('[data-role="input"]');
        const voice = root.querySelector('[data-role="voice"]');
        const voiceStatus = root.querySelector('[data-role="voice-status"]');
        const send = root.querySelector('[data-role="send"]');
        const language = root.querySelector('[data-role="language"]');
        const closeButton = root.querySelector('[data-action="close"]');
        const resetButton = root.querySelector('[data-action="reset"]');

        // Session & conversation history
        let sessionId = sessionStorage.getItem("fw-session-id");
        if (!sessionId) {
            sessionId = typeof crypto !== "undefined" && crypto.randomUUID
                ? crypto.randomUUID()
                : Math.random().toString(36).slice(2) + Date.now().toString(36);
            sessionStorage.setItem("fw-session-id", sessionId);
        }
        let conversationHistory = [];

        function pushHistory(role, content) {
            conversationHistory.push({ role, content });
            if (conversationHistory.length > 10) {
                conversationHistory = conversationHistory.slice(-10);
            }
        }

        const state = {
            open: Boolean(config.initialOpen),
            loading: false,
            customPosition: null,
            suppressLauncherClick: false,
            drag: {
                active: false,
                moved: false,
                pointerId: null,
                startX: 0,
                startY: 0,
                originLeft: 0,
                originTop: 0,
                handle: null,
                source: ""
            },
            voiceRecognition: null,
            isListening: false,
            transcriptBase: "",
            voiceEndedWithError: false
        };
        const themeMedia = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
        const dragMedia = window.matchMedia ? window.matchMedia("(min-width: 768px) and (pointer: fine)") : null;

        function applyTheme() {
            let theme = config.theme || "system";
            if (theme === "system") {
                theme = themeMedia && themeMedia.matches ? "dark" : "light";
            }
            root.dataset.theme = theme === "dark" ? "dark" : "light";
        }

        function isDragEnabled() {
            return Boolean(config.movable) && !state.open && (!dragMedia || dragMedia.matches);
        }

        function getMetrics() {
            const rootRect = root.getBoundingClientRect();
            const launcherRect = launcher.getBoundingClientRect();
            const panelRect = panel.getBoundingClientRect();
            const panelBottom = parseFloat(window.getComputedStyle(panel).bottom) || 84;

            return {
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight,
                rootWidth: Math.round(rootRect.width || launcherRect.width),
                rootHeight: Math.round(rootRect.height || launcherRect.height),
                launcherWidth: Math.round(launcherRect.width),
                launcherHeight: Math.round(launcherRect.height),
                panelWidth: Math.round(panelRect.width),
                panelHeight: Math.round(panelRect.height),
                panelBottom: Math.round(panelBottom)
            };
        }

        function constrainPosition(left, top, mode) {
            const gutter = 16;
            const metrics = getMetrics();
            const launcherOnly = mode === "launcher";
            const minLeft = launcherOnly
                ? gutter
                : gutter + Math.max(0, metrics.panelWidth - metrics.rootWidth);
            const maxLeft = metrics.viewportWidth - gutter - metrics.rootWidth;
            const minTop = launcherOnly
                ? gutter
                : gutter + Math.max(0, metrics.panelHeight + metrics.panelBottom - metrics.rootHeight);
            const maxTop = metrics.viewportHeight - gutter - metrics.rootHeight;

            const resolvedLeft = minLeft > maxLeft
                ? Math.max(gutter, Math.round((metrics.viewportWidth - metrics.rootWidth) / 2))
                : clamp(left, minLeft, maxLeft);
            const resolvedTop = minTop > maxTop
                ? Math.max(gutter, Math.round((metrics.viewportHeight - metrics.rootHeight) / 2))
                : clamp(top, minTop, maxTop);

            return {
                left: Math.round(resolvedLeft),
                top: Math.round(resolvedTop)
            };
        }

        function clearCustomPosition() {
            root.style.left = "";
            root.style.top = "";
            root.style.right = "";
            root.style.bottom = "";
            root.dataset.position = "docked";
        }

        function applyCustomPosition(position, mode) {
            const constrained = constrainPosition(position.left, position.top, mode);
            state.customPosition = constrained;
            root.style.left = `${constrained.left}px`;
            root.style.top = `${constrained.top}px`;
            root.style.right = "auto";
            root.style.bottom = "auto";
            root.dataset.position = "custom";
            return constrained;
        }

        function syncMovableState() {
            const movable = isDragEnabled();
            root.classList.toggle("is-movable", movable);
            if (!movable) {
                clearCustomPosition();
                return;
            }
            if (state.customPosition) {
                applyCustomPosition(state.customPosition, "launcher");
            }
        }

        function stopDragging() {
            if (!state.drag.active) {
                return;
            }

            window.removeEventListener("pointermove", handleDragMove);
            window.removeEventListener("pointerup", handleDragEnd);
            window.removeEventListener("pointercancel", handleDragEnd);

            if (state.drag.handle && typeof state.drag.handle.releasePointerCapture === "function") {
                try {
                    state.drag.handle.releasePointerCapture(state.drag.pointerId);
                } catch (error) {
                    // Ignore invalid pointer capture releases.
                }
            }

            state.drag.active = false;
            state.drag.moved = false;
            state.drag.pointerId = null;
            state.drag.handle = null;
            state.drag.source = "";
            root.classList.remove("is-dragging");
        }

        function handleDragMove(event) {
            if (!state.drag.active || event.pointerId !== state.drag.pointerId) {
                return;
            }

            const deltaX = event.clientX - state.drag.startX;
            const deltaY = event.clientY - state.drag.startY;

            if (!state.drag.moved && Math.abs(deltaX) + Math.abs(deltaY) > 4) {
                state.drag.moved = true;
                if (state.drag.source === "launcher") {
                    state.suppressLauncherClick = true;
                }
            }

            const dragMode = state.drag.source === "launcher" && !state.open ? "launcher" : "panel";
            const nextPosition = constrainPosition(
                state.drag.originLeft + deltaX,
                state.drag.originTop + deltaY,
                dragMode
            );
            applyCustomPosition(nextPosition, dragMode);
        }

        function handleDragEnd(event) {
            if (!state.drag.active || event.pointerId !== state.drag.pointerId) {
                return;
            }
            stopDragging();
        }

        function beginDrag(event, source) {
            if (!isDragEnabled() || event.button !== 0) {
                return;
            }
            const blockedInteractive = event.target.closest("[data-action], select, textarea, option");
            if (blockedInteractive) {
                return;
            }
            if (source !== "launcher" && event.target.closest("button")) {
                return;
            }

            const rect = root.getBoundingClientRect();
            const startingPosition = state.customPosition || {
                left: Math.round(rect.left),
                top: Math.round(rect.top)
            };

            state.drag.active = true;
            state.drag.moved = false;
            state.drag.pointerId = event.pointerId;
            state.drag.startX = event.clientX;
            state.drag.startY = event.clientY;
            state.drag.originLeft = startingPosition.left;
            state.drag.originTop = startingPosition.top;
            state.drag.handle = event.currentTarget;
            state.drag.source = source;

            root.classList.add("is-dragging");
            applyCustomPosition(
                startingPosition,
                source === "launcher" && !state.open ? "launcher" : "panel"
            );

            if (typeof event.currentTarget.setPointerCapture === "function") {
                try {
                    event.currentTarget.setPointerCapture(event.pointerId);
                } catch (error) {
                    // Ignore capture failures and continue with window listeners.
                }
            }

            window.addEventListener("pointermove", handleDragMove);
            window.addEventListener("pointerup", handleDragEnd);
            window.addEventListener("pointercancel", handleDragEnd);
            event.preventDefault();
        }

        function handleViewportChange() {
            if (isDragEnabled()) {
                if (state.customPosition) {
                    applyCustomPosition(state.customPosition, "launcher");
                }
            } else {
                clearCustomPosition();
            }
            syncMovableState();
        }

        function scrollMessages() {
            messages.scrollTo({ top: messages.scrollHeight, behavior: "smooth" });
        }

        function setVoiceStatus(message, type) {
            if (!message) {
                voiceStatus.hidden = true;
                voiceStatus.textContent = "";
                voiceStatus.className = "fw-voice-status";
                return;
            }

            voiceStatus.hidden = false;
            voiceStatus.textContent = message;
            voiceStatus.className = `fw-voice-status is-${type || "info"}`;
        }

        function updateVoiceButton() {
            voice.classList.toggle("is-listening", state.isListening);
            voice.setAttribute("aria-pressed", state.isListening ? "true" : "false");
            voice.setAttribute("aria-label", state.isListening ? "Stop voice input" : "Start voice input");
            voice.title = state.isListening ? "Stop voice input" : "Start voice input";
        }

        function stopVoiceRecognition() {
            if (state.voiceRecognition && state.isListening) {
                state.voiceRecognition.stop();
            }
        }

        function setupVoiceRecognition() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                voice.disabled = true;
                setVoiceStatus("Voice input is not supported in this browser.", "error");
                return;
            }

            state.voiceRecognition = new SpeechRecognition();
            state.voiceRecognition.lang = "en-US";
            state.voiceRecognition.interimResults = true;
            state.voiceRecognition.continuous = false;

            state.voiceRecognition.addEventListener("start", function () {
                state.isListening = true;
                state.transcriptBase = input.value ? `${input.value.trim()} ` : "";
                state.voiceEndedWithError = false;
                updateVoiceButton();
                setVoiceStatus("Listening... speak now.", "active");
            });

            state.voiceRecognition.addEventListener("result", function (event) {
                let interimTranscript = "";
                let finalTranscript = "";

                for (let index = event.resultIndex; index < event.results.length; index += 1) {
                    const transcript = event.results[index][0].transcript;
                    if (event.results[index].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }

                input.value = `${state.transcriptBase}${finalTranscript}${interimTranscript}`.trim();
                autosize(input);
            });

            state.voiceRecognition.addEventListener("end", function () {
                state.isListening = false;
                state.transcriptBase = "";
                updateVoiceButton();

                if (state.voiceEndedWithError) {
                    state.voiceEndedWithError = false;
                    return;
                }

                if (input.value.trim()) {
                    setVoiceStatus("Voice input added. Review or press send.", "success");
                } else {
                    setVoiceStatus("");
                }
            });

            state.voiceRecognition.addEventListener("error", function (event) {
                state.isListening = false;
                state.transcriptBase = "";
                state.voiceEndedWithError = true;
                updateVoiceButton();

                const messagesByError = {
                    "audio-capture": "No microphone was detected.",
                    "network": "Voice recognition failed because of a network error.",
                    "not-allowed": "Microphone permission was denied.",
                    "service-not-allowed": "Microphone access is blocked in this browser.",
                    "no-speech": "No speech was detected. Try again.",
                    "aborted": "Voice input was cancelled."
                };
                setVoiceStatus(messagesByError[event.error] || "Voice input failed. Try again.", "error");
            });

            voice.addEventListener("click", function () {
                if (state.isListening) {
                    stopVoiceRecognition();
                    return;
                }

                try {
                    setVoiceStatus("");
                    state.voiceRecognition.start();
                } catch (error) {
                    setVoiceStatus("Voice input is already starting. Try again.", "error");
                }
            });
        }

        function renderWelcomeSuggestions() {
            welcomeSuggestions.innerHTML = "";
            config.suggestions.forEach((question) => {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "fw-suggestion";
                button.textContent = question;
                button.addEventListener("click", function () {
                    sendMessage(question);
                });
                welcomeSuggestions.appendChild(button);
            });
        }

        function syncOpenState() {
            root.classList.toggle("is-open", state.open);
            launcher.setAttribute("aria-expanded", state.open ? "true" : "false");
            panel.setAttribute("aria-hidden", state.open ? "false" : "true");
            if (state.open) {
                input.focus();
            }
        }

        function setLoading(loading) {
            state.loading = loading;
            send.disabled = loading;
        }

        function updateWelcomeVisibility() {
            welcome.hidden = messages.children.length > 0;
        }

        function appendTypingIndicator() {
            const wrapper = document.createElement("div");
            wrapper.className = "fw-message is-bot";
            wrapper.dataset.role = "typing";
            wrapper.innerHTML = `
                <span class="fw-avatar"><img src="${escapeHtml(config.logoUrl)}" alt=""></span>
                <div class="fw-bubble-wrap">
                    <div class="fw-bubble">
                        <span class="fw-typing" aria-label="Assistant is typing">
                            <span></span><span></span><span></span>
                        </span>
                    </div>
                </div>
            `;
            messages.appendChild(wrapper);
            updateWelcomeVisibility();
            scrollMessages();
        }

        function removeTypingIndicator() {
            const indicator = messages.querySelector('[data-role="typing"]');
            if (indicator) {
                indicator.remove();
            }
        }

        function buildFeedbackRow(queryText, intent, service) {
            const wrap = document.createElement("div");
            wrap.className = "fw-feedback-row";

            const lbl = document.createElement("span");
            lbl.className = "fw-feedback-label";
            lbl.textContent = "Helpful?";
            wrap.appendChild(lbl);

            [{ rating: 1, emoji: "👍" }, { rating: -1, emoji: "👎" }].forEach(function (item) {
                const btn = document.createElement("button");
                btn.type = "button";
                btn.className = "fw-feedback-btn";
                btn.textContent = item.emoji;
                btn.addEventListener("click", function () {
                    if (wrap.dataset.voted) return;
                    wrap.dataset.voted = "1";
                    wrap.querySelectorAll(".fw-feedback-btn").forEach(function (b) { b.disabled = true; });
                    btn.classList.add("active");
                    const thanks = document.createElement("span");
                    thanks.className = "fw-feedback-thanks";
                    thanks.textContent = item.rating === 1 ? "Thanks!" : "We'll improve.";
                    wrap.appendChild(thanks);

                    fetch(config.apiEndpoint.replace("/api/chat", "/api/feedback"), {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            rating: item.rating,
                            query_text: queryText,
                            intent: intent,
                            service: service,
                            session_id: sessionId,
                        }),
                    }).catch(function () { /* silent */ });
                });
                wrap.appendChild(btn);
            });
            return wrap;
        }

        function appendMessage(role, text, options) {
            const details = options || {};
            const message = document.createElement("div");
            message.className = `fw-message is-${role}`;

            const bubbleWrap = document.createElement("div");
            bubbleWrap.className = "fw-bubble-wrap";

            const bubble = document.createElement("div");
            bubble.className = "fw-bubble";
            bubble.innerHTML = formatMessage(text);

            if (details.language && isRtl(details.language)) {
                bubble.setAttribute("dir", "rtl");
            }

            bubbleWrap.appendChild(bubble);

            if (details.service) {
                const badgeRow = document.createElement("div");
                badgeRow.className = "fw-badge-row";
                const badge = document.createElement("span");
                badge.className = "fw-badge";
                badge.textContent = details.service;
                badgeRow.appendChild(badge);
                bubbleWrap.appendChild(badgeRow);
            }

            if (details.suggestedQuestions && details.suggestedQuestions.length) {
                const inlineSuggestions = document.createElement("div");
                inlineSuggestions.className = "fw-inline-suggestions";

                details.suggestedQuestions.forEach((question) => {
                    const button = document.createElement("button");
                    button.type = "button";
                    button.className = "fw-inline-suggestion";
                    button.textContent = question;
                    button.addEventListener("click", function () {
                        sendMessage(question);
                    });
                    inlineSuggestions.appendChild(button);
                });

                bubbleWrap.appendChild(inlineSuggestions);
            }

            if (role === "bot" && details.intent && details.intent !== "greeting" && details.intent !== "guard_rail") {
                bubbleWrap.appendChild(buildFeedbackRow(
                    details.queryText || "",
                    details.intent,
                    details.service || ""
                ));
            }

            if (role === "user") {
                message.appendChild(bubbleWrap);
            } else {
                const avatar = document.createElement("span");
                avatar.className = "fw-avatar";
                if (role === "bot") {
                    avatar.innerHTML = `<img src="${escapeHtml(config.logoUrl)}" alt="">`;
                } else {
                    avatar.textContent = "!";
                }
                message.appendChild(avatar);
                message.appendChild(bubbleWrap);
            }

            messages.appendChild(message);
            updateWelcomeVisibility();
            scrollMessages();
        }

        function resetConversation() {
            stopVoiceRecognition();
            messages.innerHTML = "";
            conversationHistory = [];
            updateWelcomeVisibility();
            input.value = "";
            autosize(input);
            setVoiceStatus("");
            input.focus();
        }

        async function sendMessage(overrideText) {
            const rawValue = typeof overrideText === "string" ? overrideText : input.value;
            const query = rawValue.trim();

            if (!query || state.loading) {
                return;
            }

            if (query.length > 500) {
                appendMessage("system", "Message too long (max 500 characters). Please shorten your question.");
                return;
            }

            stopVoiceRecognition();
            if (!overrideText) {
                input.value = "";
                autosize(input);
            }

            state.open = true;
            syncOpenState();
            appendMessage("user", query);
            appendTypingIndicator();
            setLoading(true);
            setVoiceStatus("");

            try {
                const response = await fetch(config.apiEndpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        user_query: query,
                        preferred_language: language.value,
                        history: conversationHistory.slice(),
                        session_id: sessionId,
                    })
                });

                const data = await response.json();
                removeTypingIndicator();

                if (!response.ok || data.error) {
                    appendMessage("system", data.error || "Unable to process your request right now.");
                } else {
                    appendMessage("bot", data.answer || "", {
                        service: data.service || "",
                        language: data.response_language,
                        suggestedQuestions: data.suggested_questions || [],
                        intent: data.intent || "",
                        queryText: query,
                    });
                    pushHistory("user", query);
                    pushHistory("assistant", data.answer || "");
                }
            } catch (error) {
                removeTypingIndicator();
                appendMessage("system", "Connection error. Please try again.");
            } finally {
                setLoading(false);
                input.focus();
            }
        }

        launcher.addEventListener("click", function () {
            if (state.suppressLauncherClick) {
                state.suppressLauncherClick = false;
                return;
            }
            state.open = !state.open;
            if (state.open) {
                clearCustomPosition();
            } else if (state.customPosition) {
                applyCustomPosition(state.customPosition, "launcher");
            }
            syncMovableState();
            syncOpenState();
        });

        launcher.addEventListener("pointerdown", function (event) {
            beginDrag(event, "launcher");
        });

        closeButton.addEventListener("click", function () {
            state.open = false;
            if (state.customPosition) {
                applyCustomPosition(state.customPosition, "launcher");
            }
            syncMovableState();
            syncOpenState();
        });

        resetButton.addEventListener("click", resetConversation);

        send.addEventListener("click", function () {
            sendMessage();
        });

        input.addEventListener("input", function () {
            autosize(input);
        });

        input.addEventListener("keydown", function (event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && state.open) {
                state.open = false;
                syncOpenState();
            }
        });

        renderWelcomeSuggestions();
        autosize(input);
        setupVoiceRecognition();
        updateVoiceButton();
        applyTheme();
        if (themeMedia) {
            if (typeof themeMedia.addEventListener === "function") {
                themeMedia.addEventListener("change", applyTheme);
            } else if (typeof themeMedia.addListener === "function") {
                themeMedia.addListener(applyTheme);
            }
        }
        if (dragMedia) {
            if (typeof dragMedia.addEventListener === "function") {
                dragMedia.addEventListener("change", handleViewportChange);
            } else if (typeof dragMedia.addListener === "function") {
                dragMedia.addListener(handleViewportChange);
            }
        }
        window.addEventListener("resize", handleViewportChange);
        handleViewportChange();
        syncOpenState();

        window.FintechUserChatWidget = {
            mounted: true,
            open: function () {
                state.open = true;
                clearCustomPosition();
                syncMovableState();
                syncOpenState();
            },
            close: function () {
                state.open = false;
                if (state.customPosition) {
                    applyCustomPosition(state.customPosition, "launcher");
                }
                syncMovableState();
                syncOpenState();
            },
            reset: resetConversation,
            setTheme: function (theme) {
                config.theme = theme || "system";
                applyTheme();
            },
            resetPosition: function () {
                state.customPosition = null;
                clearCustomPosition();
                syncMovableState();
            }
        };
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", mountWidget);
    } else {
        mountWidget();
    }
})();
