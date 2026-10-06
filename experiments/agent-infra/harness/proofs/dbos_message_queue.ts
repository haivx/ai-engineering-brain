// Proof: DBOS.send messages QUEUE until a matching recv. Two approvals sent for the first
// request mean a later recv on the same topic returns immediately — auto-approving an action
// nobody reviewed. Needs DATABASE_URL (Postgres) and @dbos-inc/dbos-sdk (run from the harness repo).
import { DBOS } from "@dbos-inc/dbos-sdk";

async function wf(): Promise<string> {
  const first = await DBOS.recv<{ approved: boolean }>("approval", 20);   // approval for refund #1
  await DBOS.sleep(1000);                                                   // agent does more work…
  const t0 = Date.now();
  const second = await DBOS.recv<{ approved: boolean }>("approval", 3);   // approval for refund #2
  return JSON.stringify({ first, second, secondWaitedMs: Date.now() - t0 });
}

const run = DBOS.registerWorkflow(wf, { name: "approvalQueueProof" });
DBOS.setConfig({ name: "approval-queue-proof", systemDatabaseUrl: process.env.DATABASE_URL });
await DBOS.launch();
const h = await DBOS.startWorkflow(run)();
await new Promise((r) => setTimeout(r, 500));
// The reviewer double-clicks "Approve" on the FIRST card only.
await DBOS.send(h.workflowID, { approved: true }, "approval");
await DBOS.send(h.workflowID, { approved: true }, "approval");
console.log("RESULT", await h.getResult());
await DBOS.shutdown();
