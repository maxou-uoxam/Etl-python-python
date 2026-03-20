"""Step 6 - Post processing (file move on success)."""
import shutil
from pathlib import Path
from loguru import logger
from .base import BaseStep, StepResult


class PostProcessingStep(BaseStep):
    def execute(self, config: dict, context: dict) -> StepResult:
        source_file = context.get("source_file")
        output_path = context.get("output_path")
        all_success = context.get("all_previous_success", True)

        if not source_file:
            return StepResult(True, message="No file to move (no source file in context).")

        if not all_success:
            logger.warning("Previous steps had failures — skipping file move.")
            return StepResult(True, message="Skipped file move due to previous errors.")

        if not output_path:
            return StepResult(True, message="No output path configured — file stays in place.")

        try:
            src = Path(source_file)
            out_dir = Path(output_path)

            if self.is_dry_run:
                return StepResult(
                    True,
                    message=f"[DRY RUN] Would move {src.name} → {out_dir}",
                )

            out_dir.mkdir(parents=True, exist_ok=True)
            dest = out_dir / src.name
            shutil.move(str(src), str(dest))
            logger.info(f"Moved {src.name} → {dest}")
            return StepResult(True, message=f"File moved to {dest}")
        except Exception as e:
            logger.error(f"Post-processing failed: {e}")
            return StepResult(False, message=str(e))
