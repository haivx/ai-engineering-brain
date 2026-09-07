# State
"State" represents the operational context of a single agent execution: its current step, actions taken, remaining tasks, and any intermediate data being held. Unlike memory—which persists across multiple executions—state exists only for the duration of a single run. Poor state management can cause an agent in a long-running loop to lose sight of its goal, repeat steps, or go off track.
