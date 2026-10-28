# TurtleMaxxxing

![A pixel-art turtle](assets/turtle.png)

A free, open-source, **local-first personal assistant and project manager** that keeps work and personal life separate, with AI help only where you allow it.

- 🏠 **Runs locally.** Your data stays on your machine.
- 🔌 **You choose the connectors and the AI:** your own Claude, a fully local model, or another provider.
- 🔒 **Privacy first.** No accounts, no telemetry, nothing in the cloud in our code.
- ✅ **Tasks and reminders** with kanban status and your own labels (star your favorites).
- 💸 **Budgeting that runs itself:** describe your paychecks, splits, bills and subscriptions once, and the app keeps the ledger moving.

🚧 **Status:** early. Milestone 1 (budgeting) is working. See [PLAN.md](PLAN.md).

## Try it

You need [uv](https://docs.astral.sh/uv/) and [Node.js](https://nodejs.org/) (LTS). From this folder:

```bash
uv sync --directory backend
npm install --prefix frontend
npm run build --prefix frontend
uv run --directory backend turtlemaxxxing
```

Then open **http://turtle.localhost:8765**. Your data stays in your local app-data folder, and the app only listens on your own computer.

Just looking? `uv run --directory backend turtlemaxxxing --demo` runs it with fictional data in a throwaway folder.

🧪 **Trust, but verify:** every privacy promise has a test you can run yourself. See the [testing SOP](docs/TESTING.md).

Stuck? Open this folder in Claude Code and ask for help. The bundled `turtle-help` skill and [troubleshooting guides](docs/troubleshooting/README.md) walk you through it. For other AI agents, start with [AGENTS.md](AGENTS.md).

I like turtles. 🐢

## License

[MIT](LICENSE)
