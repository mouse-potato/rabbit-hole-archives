/* The browser receives only public investigation packets, never the case solution. */
const $ = (id) => document.getElementById(id);
const say = (node, value) => { node.textContent = String(value ?? ""); };
const element = (tag, text, parent) => {
  const node = document.createElement(tag);
  say(node, text);
  parent.append(node);
  return node;
};
let busy = false;
let solvedAnnounced = false;
let caseTitle = "Rabbit Hole Archives";
const transcript = $("transcript");
const transcriptScroll = $("transcript-scroll");
const latestButton = $("latest-transcript");
let unseenEntries = 0;
function isAtLatest() {
  return transcriptScroll.scrollHeight - transcriptScroll.scrollTop -
    transcriptScroll.clientHeight <= 48;
}
function showUnreadCount() {
  say(latestButton, unseenEntries ?
    "Jump to latest (" + unseenEntries + " new)" : "Jump to latest");
}
function entry(message) {
  // Only follow new entries when the player was already reading the end.
  // Never pull the entire page away from the command input or casebook.
  const atLatest = isAtLatest();
  element("li", message, transcript);
  if (atLatest) {
    transcriptScroll.scrollTop = transcriptScroll.scrollHeight;
    unseenEntries = 0;
  } else {
    unseenEntries++;
  }
  showUnreadCount();
}
function announceResult(message) {
  // A compact announcement avoids re-reading the entire growing transcript.
  say($("transcript-update"), message);
}
async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) }
  });
  if (!response.ok) throw Error("HTTP " + response.status);
  return response.json();
}
async function act(text) {
  if (busy) return;
  busy = true;
  $("command").disabled = true;
  $("act-button").disabled = true;
  $("action-options").querySelectorAll("button").forEach(button => { button.disabled = true; });
  entry("You: " + text);
  try {
    const packet = await request("/api/investigation/actions", {
      method: "POST", body: JSON.stringify({ text })
    });
    // Finish the pending state before rendering the replacement action buttons.
    busy = false;
    renderPacket(packet);
  } catch (error) {
    entry("Unable to act: " + error.message);
    announceResult("Unable to act: " + error.message);
  } finally {
    busy = false;
    const closingMessage = $("scene").querySelector(".success");
    const closed = Boolean(closingMessage);
    $("command").disabled = closed;
    $("act-button").disabled = closed;
    $("action-options").querySelectorAll("button").forEach(button => { button.disabled = closed; });
    if (closingMessage) closingMessage.focus();
    else $("command").focus();
  }
}
function actions(title, items, verb, parent, currentKey = "") {
  const available = items.filter(option => option.key !== currentKey);
  if (!available.length) return;
  const group = document.createElement("div");
  group.className = "action-group";
  element("h4", title, group);
  const list = document.createElement("ul");
  list.className = "action-list";
  group.append(list);
  parent.append(group);
  for (const option of available) {
    const li = document.createElement("li");
    const button = element("button", option.name, li);
    button.type = "button";
    button.setAttribute("aria-label", verb + " " + option.name);
    button.disabled = busy;
    button.addEventListener("click", () => act(verb + " " + option.key));
    list.append(li);
  }
}
function renderPacket(packet) {
  if (!packet?.view) throw Error("Invalid investigation response.");
  const view = packet.view;
  caseTitle = view.case_title || caseTitle;
  const scene = $("scene");
  const sceneDetailsOpen = scene.querySelector("details")?.open ?? false;
  scene.replaceChildren();
  element("h3", view.place_name || "Unknown location", scene);
  const sceneDetails = document.createElement("details");
  sceneDetails.className = "scene-presence";
  sceneDetails.open = sceneDetailsOpen;
  element("summary", "Room description and witnesses", sceneDetails);
  element("p", packet.scene_description || "You survey the room.", sceneDetails)
    .className = "room-description";
  const visibleWitnesses = view.witnesses || [];
  for (const witness of visibleWitnesses) {
    const person = document.createElement("div");
    person.className = "scene-person";
    element("p", witness.name, person).className = "scene-person-name";
    const appearance = packet.witness_descriptions?.[witness.witness_key];
    if (appearance) element("p", appearance, person);
    sceneDetails.append(person);
  }
  scene.append(sceneDetails);
  const options = packet.options || {};
  if (view.solved) {
    const closingMessage = element("p", "Case closed. You have assembled enough evidence to support your accusation.", scene);
    closingMessage.className = "success";
    closingMessage.tabIndex = -1;
    if (!solvedAnnounced) {
      entry("Case closed. The evidence supports your conclusion.");
      solvedAnnounced = true;
    }
  }
  const palette = $("action-palette");
  const actionOptions = $("action-options");
  actionOptions.replaceChildren();
  palette.hidden = Boolean(view.solved);
  if (!view.solved) {
    actions("Travel", options.places || [], "go to", actionOptions, view.place_key);
    actions("Examine", options.evidence || [], "examine", actionOptions);
    actions("Interview", visibleWitnesses.map(w => ({
      key: w.witness_key, name: w.name
    })), "talk to", actionOptions);
    actions("Make an accusation", options.suspects || [], "accuse", actionOptions);
  }
  $("command").disabled = Boolean(view.solved);
  $("act-button").disabled = Boolean(view.solved);

  const book = $("casebook");
  book.replaceChildren();
  element("h3", "Evidence", book);
  if (!view.discovered?.length) element("p", "Nothing recorded yet.", book);
  for (const clue of view.discovered || []) {
    const section = document.createElement("section");
    section.className = "casebook-entry";
    element("h4", clue.label, section);
    element("p", clue.observation, section);
    book.append(section);
  }
  element("h3", "Witness statements", book);
  if (!view.heard?.length) element("p", "No interviews recorded yet.", book);
  for (const statement of view.heard || []) {
    const section = document.createElement("section");
    section.className = "casebook-entry";
    element("h4", statement.witness_key.replaceAll("-", " "), section);
    element("p", "“" + statement.statement + "”", section);
    if (statement.lead_evidence_key) {
      element("p", "Lead: " + statement.lead_evidence_key.replaceAll("-", " "), section).className = "hint";
    }
    book.append(section);
  }
  if (packet.outcome) {
    if (typeof packet.narration === "string" && packet.narration) {
      entry("Narrator: " + packet.narration);
    }
    const outcome = packet.outcome;
    const result = [
      outcome.accepted && outcome.action === "inquire" ? "Narrator: " + outcome.detail :
        [outcome.accepted ? "Action accepted" : "Action not completed", outcome.detail]
          .filter(Boolean).join("\n"),
      outcome.observation,
      ...(outcome.statements || []),
      outcome.verdict === "solved" ? "Accusation supported." :
        outcome.verdict === "unproven" ? "Accusation unproven. Your evidence does not establish the case." : ""
    ].filter(Boolean).join("\n");
    entry(result);
    announceResult(result);
  }
}
async function connect() {
  $("connect").disabled = true;
  try {
    const packet = await request("/api/investigation");
    renderPacket(packet);
    say($("status"), packet.ai_enabled ? "Ollama enabled." : "Offline mode.");
  } catch (error) {
    say($("status"), "Unable to open investigation: " + error.message);
  } finally {
    $("connect").disabled = false;
  }
}
$("connect").addEventListener("click", connect);
latestButton.addEventListener("click", () => {
  transcriptScroll.scrollTop = transcriptScroll.scrollHeight;
  unseenEntries = 0;
  showUnreadCount();
  announceResult("Showing the latest investigation messages.");
});
transcriptScroll.addEventListener("scroll", () => {
  if (isAtLatest() && unseenEntries) {
    unseenEntries = 0;
    showUnreadCount();
  }
});
$("export-transcript").addEventListener("click", () => {
  const lines = Array.from(transcript.querySelectorAll("li"), (item, index) =>
    String(index + 1) + ". " + item.textContent.trim());
  const content = [caseTitle, "Investigation transcript", "", ...lines, ""].join("\n");
  const file = new Blob([content], { type: "text/plain;charset=utf-8" });
  const address = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = address;
  link.download = "rabbit-hole-archives-transcript.txt";
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(address);
});
$("command-form").addEventListener("submit", async event => {
  event.preventDefault();
  const text = $("command").value.trim();
  if (!text || busy) return;
  $("command").value = "";
  await act(text);
});
connect();
