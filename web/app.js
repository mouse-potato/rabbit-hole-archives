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
function entry(message) {
  const item = element("li", message, transcript);
  item.scrollIntoView({ block: "nearest", behavior: "auto" });
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
  $("scene").querySelectorAll("button").forEach(button => { button.disabled = true; });
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
  } finally {
    busy = false;
    $("command").disabled = false;
    $("act-button").disabled = false;
    $("command").focus();
  }
}
function actions(title, items, verb, parent, currentKey = "") {
  if (!items?.length) return;
  element("h4", title, parent);
  const list = document.createElement("ul");
  list.className = "action-list";
  parent.append(list);
  for (const option of items) {
    if (verb === "go to" && option.key === currentKey) continue;
    const li = document.createElement("li");
    const button = element("button", option.name, li);
    button.type = "button";
    button.disabled = busy;
    button.addEventListener("click", () => act(verb + " " + option.key));
    list.append(li);
  }
  if (!list.children.length) list.remove();
}
function renderPacket(packet) {
  if (!packet?.view) throw Error("Invalid investigation response.");
  const view = packet.view;
  caseTitle = view.case_title || caseTitle;
  const scene = $("scene");
  scene.replaceChildren();
  element("p", "CASE FILE / " + view.case_title, scene).className = "eyebrow";
  element("h3", view.place_name || "Unknown location", scene);
  const description = view.place_key === "study"
    ? "The study is quiet, but the empty space where the seal once rested is impossible to ignore. The desk holds the house's paperwork."
    : "Beyond the study, the hall leads toward a side door. Footsteps and a discarded possession may tell you more than anyone's testimony.";
  element("p", description, scene);
  const options = packet.options || {};
  if (view.solved) {
    element("p", "Case closed. You have assembled enough evidence to support your accusation.", scene).className = "success";
    if (!solvedAnnounced) {
      entry("Case closed. The evidence supports your conclusion.");
      solvedAnnounced = true;
    }
  } else {
    element("p", "Examine the scene, interview the witnesses, and find enough evidence to support your theory.", scene).className = "hint";
  }
  actions("Travel", options.places || [], "go to", scene, view.place_key);
  actions("Examine", options.evidence || [], "examine", scene);
  actions("Interview", (view.witnesses || []).map(w => ({
    key: w.witness_key, name: w.name
  })), "talk to", scene);
  actions("Make an accusation", options.suspects || [], "accuse", scene);

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
    const outcome = packet.outcome;
    const result = [
      outcome.accepted ? "Action accepted" : "Action not completed",
      outcome.detail,
      outcome.observation,
      ...(outcome.statements || []),
      outcome.verdict === "solved" ? "Accusation supported." :
        outcome.verdict === "unproven" ? "Accusation unproven. Your evidence does not establish the case." : ""
    ].filter(Boolean).join("\n");
    entry(result);
  }
}
async function connect() {
  $("connect").disabled = true;
  try {
    renderPacket(await request("/api/investigation"));
    say($("status"), "Investigation ready.");
  } catch (error) {
    say($("status"), "Unable to open investigation: " + error.message);
  } finally {
    $("connect").disabled = false;
  }
}
$("connect").addEventListener("click", connect);
$("command-form").addEventListener("submit", async event => {
  event.preventDefault();
  const text = $("command").value.trim();
  if (!text || busy) return;
  $("command").value = "";
  await act(text);
});
connect();
