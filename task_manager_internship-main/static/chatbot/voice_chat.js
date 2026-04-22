(function () {
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatMessages = document.getElementById("chat-messages");
  const micButton = document.getElementById("mic-button");
  const micButtonText = document.getElementById("mic-button-text");
  const sendButton = document.getElementById("send-button");
  const speechStatus = document.getElementById("speech-status");
  const listeningIndicator = document.getElementById("listening-indicator");
  const csrfTokenField = document.querySelector("[name=csrfmiddlewaretoken]");
  const config = window.chatbotVoiceConfig || {};
  const chatUrl = config.chatUrl;
  const csrfToken = csrfTokenField ? csrfTokenField.value : "";

  if (!chatForm || !chatInput || !chatMessages || !micButton || !chatUrl) {
    return;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const speechSynthesisSupported = "speechSynthesis" in window;
  let recognition = null;
  let isListening = false;

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function removeEmptyState() {
    const emptyState = chatMessages.querySelector(".border-dashed");
    if (emptyState) {
      emptyState.remove();
    }
  }

  function setStatus(message, tone) {
    if (!speechStatus) {
      return;
    }

    if (!message) {
      speechStatus.className = "hidden";
      speechStatus.textContent = "";
      return;
    }

    const toneClasses = {
      info: "rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-800",
      error: "rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800",
      success: "rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
    };

    speechStatus.className = toneClasses[tone] || toneClasses.info;
    speechStatus.textContent = message;
  }

  function setListeningState(listening) {
    isListening = listening;
    micButton.setAttribute("aria-pressed", listening ? "true" : "false");
    micButton.classList.toggle("bg-rose-50", listening);
    micButton.classList.toggle("border-rose-300", listening);
    micButton.classList.toggle("text-rose-700", listening);
    micButtonText.textContent = listening ? "Listening..." : "Speak";

    if (listening) {
      listeningIndicator.classList.remove("hidden");
      listeningIndicator.classList.add("inline-flex");
      setStatus("Listening... please speak your task question.", "info");
    } else {
      listeningIndicator.classList.add("hidden");
      listeningIndicator.classList.remove("inline-flex");
    }
  }

  function appendMessage(label, text, isUser) {
    removeEmptyState();

    const wrapper = document.createElement("div");
    wrapper.className = isUser ? "flex justify-end" : "flex justify-start";

    const bubble = document.createElement("div");
    bubble.className = isUser
      ? "max-w-[80%] rounded-2xl bg-slate-900 text-white px-4 py-3"
      : "max-w-[80%] rounded-2xl bg-white border border-slate-200 px-4 py-3";

    const title = document.createElement("div");
    title.className = isUser
      ? "text-xs uppercase tracking-wide text-slate-300 mb-1"
      : "text-xs uppercase tracking-wide text-slate-500 mb-1";
    title.textContent = label;

    const body = document.createElement("div");
    body.className = isUser ? "whitespace-pre-wrap" : "whitespace-pre-wrap text-slate-800";
    body.textContent = text;

    bubble.appendChild(title);
    bubble.appendChild(body);
    wrapper.appendChild(bubble);
    chatMessages.appendChild(wrapper);
    scrollToBottom();
  }

  function speakText(text) {
    if (!speechSynthesisSupported || !text) {
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  }

  async function sendMessage(message) {
    appendMessage("You", message, true);
    chatInput.value = "";
    sendButton.disabled = true;
    micButton.disabled = true;
    setStatus("Bot is preparing a response...", "info");

    try {
      const response = await fetch(chatUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ message: message })
      });

      const data = await response.json();
      if (!response.ok) {
        appendMessage("Bot", data.error || "Something went wrong.", false);
        setStatus(data.error || "Unable to process your request.", "error");
        return;
      }

      appendMessage("Bot", data.response, false);
      setStatus("Voice message processed successfully.", "success");
      speakText(data.response);
    } catch (error) {
      appendMessage("Bot", "Unable to send message right now.", false);
      setStatus("Network error while sending your message.", "error");
    } finally {
      sendButton.disabled = false;
      micButton.disabled = false;
      chatInput.focus();
    }
  }

  if (!SpeechRecognition) {
    micButton.disabled = true;
    setStatus("Speech recognition is not supported in this browser. Please type your message instead.", "error");
  } else {
    recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = function () {
      setListeningState(true);
    };

    recognition.onresult = function (event) {
      const transcript = event.results[0][0].transcript.trim();
      chatInput.value = transcript;
      setStatus("Voice captured successfully. Sending message to the chatbot...", "success");

      if (transcript) {
        sendMessage(transcript);
      }
    };

    recognition.onerror = function (event) {
      const message = event.error === "not-allowed"
        ? "Microphone permission was denied. Please allow access and try again."
        : "Voice recognition failed. Please try again or type your message.";
      setStatus(message, "error");
    };

    recognition.onend = function () {
      setListeningState(false);
    };

    micButton.addEventListener("click", function () {
      if (isListening) {
        recognition.stop();
        return;
      }

      chatInput.focus();
      recognition.start();
    });
  }

  chatForm.addEventListener("submit", function (event) {
    event.preventDefault();

    const message = chatInput.value.trim();
    if (!message) {
      setStatus("Please type or speak a message first.", "error");
      return;
    }

    sendMessage(message);
  });

  scrollToBottom();
})();
