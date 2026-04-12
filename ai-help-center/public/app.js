const askForm = document.getElementById("ask-form");
const promptInput = document.getElementById("prompt-input");
const contentSection = document.getElementById("content-section");
const chatSection = document.getElementById("chat-section");
const chatTranscript = document.getElementById("chat-transcript");
const messageTemplate = document.getElementById("message-template");
const presetButtons = document.querySelectorAll(".preset-prompt");

let busy = false;

function addMessage(role, text, { html = false } = {}) {
  const fragment = messageTemplate.content.cloneNode(true);
  const row = fragment.querySelector(".message-row");
  const bubble = fragment.querySelector(".bubble");

  row.classList.add(role === "user" ? "user" : "assistant");

  if (html) {
    bubble.innerHTML = text;
  } else {
    bubble.textContent = text;
  }

  chatTranscript.appendChild(fragment);
  chatTranscript.lastElementChild?.scrollIntoView({ behavior: "smooth", block: "end" });
}

function buildTypingIndicator() {
  return '<span class="typing" aria-label="Assistant is typing"><span></span><span></span><span></span></span>';
}

async function submitPrompt(rawPrompt) {
  const prompt = rawPrompt.trim();
  if (!prompt || busy) {
    return;
  }

  busy = true;
  promptInput.value = "";
  promptInput.blur();

  contentSection.classList.add("hidden");
  chatSection.classList.remove("hidden");

  addMessage("user", prompt);
  addMessage("assistant", buildTypingIndicator(), { html: true });

  const typingRow = chatTranscript.lastElementChild;

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Request failed");
    }

    if (typingRow) {
      typingRow.remove();
    }

    addMessage("assistant", payload.answer || "I could not generate an answer.");
  } catch (error) {
    if (typingRow) {
      typingRow.remove();
    }

    addMessage(
      "assistant",
      `I could not reach the local AI service. ${error.message}. Please confirm Ollama is running on localhost:11434.`
    );
  } finally {
    busy = false;
    promptInput.focus();
  }
}

askForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitPrompt(promptInput.value);
});

presetButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const prompt = button.dataset.prompt || button.textContent || "";
    promptInput.value = prompt.trim();
    submitPrompt(promptInput.value);
  });
});
