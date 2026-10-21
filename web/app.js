/* The browser sees only the restricted API's public packet. Never fetch case authoring data. */
const $ = (id) => document.getElementById(id);
let base = "";
const renderText = (node, value) => { node.textContent = value == null ? "" : String(value); };
function entry(message) {
  const item = document.createElement("li");
  renderText(item, message);
  $("transcript").append(item);
}
function renderPacket(packet) {
  if (!packet || !packet.view) throw new Error("The server did not return a narration packet.");
  const view = packet.view;
  renderText($("scene"), JSON.stringify(view, null, 2));
  const book = $("casebook");
  book.replaceChildren();
  const pre = document.createElement("pre");
  pre.style.whiteSpace = "pre-wrap";
  pre.style.overflowWrap = "anywhere";
  renderText(pre, JSON.stringify(view, null, 2));
  book.append(pre);
  if (packet.outcome) {
    const outcome = packet.outcome;
    entry([outcome.accepted ? "Action accepted" : "Action rejected", outcome.detail, outcome.observation, ...(outcome.statements || []), outcome.verdict].filter(Boolean).join("\n"));
  }
}
async function request(path, options = {}) {
  const response = await fetch(base + path, { ...options, headers: { "Content-Type": "application/json", ...(options.headers || {}) } });
  if (!response.ok) throw new Error("HTTP " + response.status + ": " + (await response.text()).slice(0, 300));
  return response.json();
}
$("connect").addEventListener("click", async () => {
  base = $("server").value.trim().replace(/\/$/, "");
  $("connect").disabled = true;
  try {
    const packet = await request("/api/investigation");
    renderPacket(packet);
    renderText($("status"), "Connected.");
    $("command").focus();
  } catch (error) {
    renderText($("status"), "Connection failed: " + error.message);
  } finally { $("connect").disabled = false; }
});
$("command-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = $("command");
  const text = input.value.trim();
  if (!text || !base) return;
  entry("You: " + text);
  input.disabled = true;
  try {
    renderPacket(await request("/api/investigation/actions", { method: "POST", body: JSON.stringify({ text }) }));
    input.value = "";
  } catch (error) { entry("Unable to act: " + error.message); }
  finally { input.disabled = false; input.focus(); }
});