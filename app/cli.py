from __future__ import annotations

import argparse
import time

import uvicorn

from research.latent_supervisor import supervisor


def _print_research_progress(interval: float) -> None:
    """Run research locally and render compact progress in the terminal."""
    supervisor.start()
    last_line = ""
    completion_announced = False
    try:
        while True:
            state = supervisor.status()
            progress = float(state.get("progress", 0.0))
            epoch = int(state.get("epoch", 0))
            epochs = int(state.get("epochs", 0))
            status = str(state.get("status", "unknown"))
            stage = str(state.get("stage", "idle"))
            experiment = str(state.get("experiment_id") or "-")
            loss = state.get("validation_loss")
            loss_text = "-" if loss is None else f"{float(loss):.6f}"
            line = (
                f"\rResearch | stage={stage:<25} status={status:<10} "
                f"progress={progress:6.2f}% epoch={epoch:>2}/{epochs:<2} "
                f"val_loss={loss_text:<10} exp={experiment}"
            )
            if line != last_line:
                print(line, end="", flush=True)
                last_line = line
            if state.get("next_stage_ready") and not completion_announced:
                print(
                    "\n\n"
                    "============================================================\n"
                    "  STAGE 1 COMPLETE — STAGE 2 READY\n"
                    "  Research validation has authorized the next-stage handoff.\n"
                    "============================================================\n",
                    flush=True,
                )
                completion_announced = True
            time.sleep(max(0.2, interval))
    except KeyboardInterrupt:
        print("\n\nResearch stopped by operator.")
        supervisor.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Advanced AI Trader local control plane")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument(
        "--research-progress",
        action="store_true",
        help="run the research supervisor with terminal progress output",
    )
    args = parser.parse_args()
    if args.research_progress:
        _print_research_progress(interval=0.5)
        return
    uvicorn.run("app.api:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
