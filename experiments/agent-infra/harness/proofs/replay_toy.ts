// Models DBOS.runStep with an in-memory array — no DB, no LLM. Run: npx tsx replay_toy.ts
const savedOutputs: unknown[] = [];      // ← stands in for DBOS's operation_outputs table
let stepIndex = 0;                       // position of the step in the current execution

async function runStep<T>(fn: () => Promise<T>, name: string): Promise<T> {
  const i = stepIndex++;
  if (i < savedOutputs.length) {
    console.log(`   [${i}] ${name.padEnd(8)} → CACHED (fn not called)`);
    return savedOutputs[i] as T;
  }
  console.log(`   [${i}] ${name.padEnd(8)} → EXECUTED`);
  const out = await fn();
  savedOutputs.push(out);                // persist = checkpoint
  return out;
}

let fakeModelCalls = 0;
const fakeModel = async () => `reply-${++fakeModelCalls}`;   // fake LLM: a different result on every call

async function workflow(crashAtStep: number | null) {
  stepIndex = 0;
  const turns: string[] = [];                          // ← EMPTY at the start, on first run and on replay
  for (let step = 0; step < 4; step++) {
    if (step === crashAtStep) throw new Error("💥 CRASH");
    const reply = await runStep(fakeModel, `model-${step}`);
    turns.push(reply);                                 // rebuilt from the step's (possibly cached) output
    console.log(`        turns = [${turns.join(", ")}]`);
  }
  return turns;
}

console.log("RUN 1 (crash at step 2):");
await workflow(2).catch((e) => console.log("  ", e.message));

console.log("\nRECOVER (workflow body re-runs from line 1):");
const final = await workflow(null);
console.log(`\nResult: [${final.join(", ")}] · real model calls: ${fakeModelCalls} (not 6)`);
