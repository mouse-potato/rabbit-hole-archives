/* Only restricted projections and explicitly safe action options reach the browser. */
const $ = (id) => document.getElementById(id);
let base = location.origin;
const say = (node, value) => { node.textContent = String(value ?? ""); };
function element(tag, text, parent) {
  const node = document.createElement(tag);
  say(node, text);
  parent.append(node);
  return node;
}
function entry(message) { element("li", message, $("transcript")); }
async function act(text) {
  entry("You: " + text);
  $("command").disabled = true;
  try {
    renderPacket(await request("/api/investigation/actions", {
      method: "POST", body: JSON.stringify({ text })
    }));
  } catch (error) { entry("Unable to act: " + error.message); }
  finally { $("command").disabled = false; $("command").focus(); }
}
function actions(title, items, verb, parent) {
  if (!items?.length) return;
  element("h3", title, parent);
  const list = document.createElement("ul");
  parent.append(list);
  for (const option of items) {
    const li = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    say(button, option.name);
    button.addEventListener("click", () => act(verb + " " + option.key));
    li.append(button);
    list.append(li);
  }
}
function renderPacket(packet) {
  if (!packet?.view) throw Error("Invalid narration packet.");
  const view = packet.view;
  const scene = $("scene");
  scene.replaceChildren();
  element("h3", view.case_title, scene);
  element("p", view.solved ? "Case solved!" : "Current location: " + (view.place_name || "Unknown"), scene);
  if (view.solved) entry("The case is solved. Well done, investigator.");
  const options = packet.options || {};
  actions("Explore locations", options.places || [], "go to", scene);
  actions("Examine nearby evidence", options.evidence || [], "examine", scene);
  actions("Question witnesses", view.witnesses?.map(w => ({
    key: w.witness_key, name: w.name
  })) || [], "talk to", scene);
  actions("Accuse a suspect", options.suspects || [], "accuse", scene);
  const book = $("casebook");
  book.replaceChildren();
  element("h3", "Evidence", book);
  if (!view.discovered.length) element("p", "No evidence recorded yet.", book);
  for (const clue of view.discovered) {
    element("h4", clue.label, book);
    element("p", clue.observation, book);
  }
  element("h3", "Witness statements", book);
  if (!view.heard.length) element("p", "No interviews recorded yet.", book);
  for (const statement of view.heard) {
    element("h4", statement.witness_key.replaceAll("-", " "), book);
    element("p", statement.statement, book);
    if (statement.lead_evidence_key) element("p", "Lead: " + statement.lead_evidence_key, book);
  }
  if (packet.outcome) {
    const result = packet.outcome;
    const description = [result.accepted ? "Action accepted" : "Action rejected",
      result.detail, result.observation, ...(result.statements || []),
      result.verdict === "solved" ? "Case solved!" : result.verdict === "unproven" ? "Accusation unproven." : ""]
      .filter(Boolean).join("\n");
    entry(description);
  }
}
async function request(path, options = {}) {
  const response = await fetch(base + path, {
    ...options, headers: { "Content-Type": "application/json", ...(options.headers || {}) }
  });
  if (!response.ok) throw Error("HTTP " + response.status);
  return response.json();
}
$("server").value = location.origin;
$("connect").addEventListener("click", async () => {
  base = $("server").value.trim().replace(/\/$/, "");
  $("connect").disabled = true;
  try {
    renderPacket(await request("/api/investigation"));
    say($("status"), "Connected to the investigation.");
    $("command").focus();
  } catch (error) { say($("status"), "Connection failed: " + error.message); }
  finally { $("connect").disabled = false; }
});
$("command-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = $("command").value.trim();
  if (!text) return;
  $("command").value = "";
  await act(text);
});
$("connect").click();
