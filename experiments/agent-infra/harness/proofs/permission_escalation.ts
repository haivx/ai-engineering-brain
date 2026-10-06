// Proof: checking tool permission against the agent that is current *at execution time*
// lets a handoff inside the same turn escalate privilege. Checking against the agent that
// *made the decision* (the one that produced the turn) does not.
// Pure simulation — no LLM, no DB. Run: npx tsx permission_escalation.ts

type Agent = { name: string; tools: Set<string> };
const triage: Agent = { name: "triage", tools: new Set(["classifyItem", "runCode", "draftReply", "sendReply", "handoff"]) };
const billing: Agent = { name: "billing", tools: new Set(["runCode", "issueRefund", "draftReply", "sendReply"]) };
const agents: Record<string, Agent> = { triage, billing };

// One model turn produced BY TRIAGE (e.g. via prompt injection): hand off, then refund in the same turn.
const turnFromTriage = [
  { toolName: "handoff", input: { to: "billing" } },
  { toolName: "issueRefund", input: { chargeId: "ch_002", amountCents: 500000 } },
];

function runTurn(mode: "current" | "acting") {
  let currentAgent = triage;
  const actingAgent = currentAgent; // the agent that generated this turn
  const log: string[] = [];
  for (const call of turnFromTriage) {
    const checkAgainst = mode === "acting" ? actingAgent : currentAgent;
    if (!checkAgainst.tools.has(call.toolName)) {
      log.push(`DENY  ${call.toolName} (checked against ${checkAgainst.name})`);
      continue;
    }
    if (call.toolName === "handoff") {
      currentAgent = agents[String(call.input.to)];
      log.push(`ALLOW handoff → currentAgent is now ${currentAgent.name}`);
      continue;
    }
    log.push(`ALLOW ${call.toolName} ${JSON.stringify(call.input)} (checked against ${checkAgainst.name})`);
  }
  return log;
}

for (const mode of ["current", "acting"] as const) {
  console.log(`\n== permission checked against ${mode}Agent ==`);
  for (const line of runTurn(mode)) console.log("  " + line);
}
