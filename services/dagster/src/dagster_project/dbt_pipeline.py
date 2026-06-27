"""Reusable factory for the standard bronze -> silver -> gold dbt pipeline.

Each bronze data source follows the same convention:

1. ``dbt source freshness --select source:<data_source>``
2. ``dbt test --select source:<data_source>``         (the source-tests gate)
3. ``dbt build --select tag:silver,tag:<data_source>``
4. ``dbt build --select tag:gold,tag:<data_source>``

Steps 1-2 are plain ops (dbt sources have no model node to materialize); steps
3-4 are real ``@dbt_assets`` so their models show up in the asset graph.

This module lives outside ``defs/`` on purpose: it defines no top-level Dagster
objects, so it must not be picked up by the defs-folder autoloader. Per-source
modules under ``defs/`` call :func:`build_dbt_source_pipeline` and bind the
returned steps at module scope so the autoloader registers them.
"""

from collections.abc import Sequence
from dataclasses import dataclass
import json
from typing import Any

from dagster import AssetExecutionContext, AssetsDefinition, AssetSpec, asset
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets

from dagster_project.dbt_config import dbt_project

# dbt resource types that become materializable Dagster assets (vs. tests, etc.).
DBT_ASSET_RESOURCE_TYPES = {"model", "seed", "snapshot"}
SILVER_TAG = "silver"
GOLD_TAG = "gold"

# Data sources whose models are owned by a dedicated per-source pipeline
# (built via build_dbt_source_pipeline). Every dbt model must belong to exactly
# one @dbt_assets definition, so the whole-warehouse layered dbt_assets must
# exclude these tags — otherwise the same model is defined twice and Dagster
# raises "Duplicate asset key". Add a data source here when it gets its own
# per-source pipeline.
SOURCE_PIPELINE_DATA_SOURCES: tuple[str, ...] = ("revenue",)


def source_pipeline_exclude() -> str | None:
    """dbt exclusion string for models owned by per-source pipelines, or None."""
    if not SOURCE_PIPELINE_DATA_SOURCES:
        return None
    return " ".join(f"tag:{source}" for source in SOURCE_PIPELINE_DATA_SOURCES)


@dataclass(frozen=True)
class DbtSourcePipeline:
    """The dbt steps for one bronze source: freshness -> tests -> silver -> gold.

    ``silver_build`` / ``gold_build`` are ``None`` when no manifest model carries
    the matching ``tag:<layer>,tag:<data_source>`` pair (an empty dbt selection
    would otherwise raise at definition time).
    """

    source_freshness: AssetsDefinition
    source_tests: AssetsDefinition
    silver_build: AssetsDefinition | None
    gold_build: AssetsDefinition | None

    def assets(self) -> list[AssetsDefinition]:
        """Return the defined steps, dropping layers with no matching models."""
        return [
            step
            for step in (
                self.source_freshness,
                self.source_tests,
                self.silver_build,
                self.gold_build,
            )
            if step is not None
        ]


def _source_freshness_args(data_source: str) -> list[str]:
    return ["source", "freshness", "--select", f"source:{data_source}"]


def _source_tests_args(data_source: str) -> list[str]:
    return ["test", "--select", f"source:{data_source}"]


def _layer_build_args(layer_tag: str, data_source: str) -> list[str]:
    return ["build", "--select", f"tag:{layer_tag},tag:{data_source}"]


def _run_dbt(
    context: AssetExecutionContext,
    dbt: DbtCliResource,
    args: Sequence[str],
) -> None:
    # These steps run as plain @asset ops, not @dbt_assets, so .stream() can't
    # map dbt events back to asset keys (it would raise "Expected to find dbt
    # manifest metadata on asset"). .wait() runs the command and raises on
    # failure, preserving fail-fast for source freshness / source tests.
    context.log.info(f"Running dbt command: dbt {' '.join(args)}")
    dbt.cli(list(args)).wait()


def build_dbt_step(
    *,
    name: str,
    args: Sequence[str],
    deps: Sequence[Any],
    description: str,
    group_name: str,
) -> AssetsDefinition:
    """Build a plain op-style asset that shells out to a single dbt command."""

    @asset(
        name=name,
        group_name=group_name,
        deps=list(deps),
        description=description,
    )
    def _step(context: AssetExecutionContext, dbt: DbtCliResource) -> None:
        _run_dbt(context, dbt, args)

    return _step


def _manifest_has_tagged_asset(manifest_path: Any, required_tags: set[str]) -> bool:
    """Return True if any materializable model carries all of ``required_tags``."""
    with open(manifest_path) as manifest_file:
        manifest = json.load(manifest_file)

    return any(
        node.get("resource_type") in DBT_ASSET_RESOURCE_TYPES
        and required_tags.issubset(set(node.get("tags", [])))
        for node in manifest.get("nodes", {}).values()
    )


class SourceTestsGateTranslator(DagsterDbtTranslator):
    """Wire silver-layer dbt assets to depend on the upstream source-tests gate.

    The source-tests step is a plain op, so it is invisible to dbt's own DAG.
    Only silver assets get the explicit dep; gold assets inherit it transitively
    because gold models ``ref()`` silver models.
    """

    def __init__(self, *, required_tags: set[str], gate_asset: AssetsDefinition):
        super().__init__()
        self._required_tags = required_tags
        self._gate_asset = gate_asset

    def get_asset_spec(
        self,
        manifest: Any,
        unique_id: str,
        project: Any,
    ) -> AssetSpec:
        spec = super().get_asset_spec(manifest, unique_id, project)
        resource_tags = set(
            self.get_resource_props(manifest, unique_id).get("tags", [])
        )

        if self._required_tags.issubset(resource_tags):
            return spec.merge_attributes(deps=[self._gate_asset])

        return spec


def build_dbt_source_pipeline(
    *,
    data_source: str,
    bronze_asset: AssetsDefinition,
    source_steps_group: str = "quality",
) -> DbtSourcePipeline | None:
    """Build the freshness -> tests -> silver -> gold dbt steps for one source.

    ``bronze_asset`` is the upstream ingestion asset the freshness check waits on.
    ``source_steps_group`` is the Dagster group for the source freshness/tests
    gate ops; the silver/gold dbt assets get their group from the dbt manifest.
    Returns ``None`` when the dbt project/manifest is unavailable (e.g. unit tests
    that import ``dagster_project`` without the dbt project mounted).
    """
    if dbt_project is None:
        return None

    manifest_path = dbt_project.manifest_path

    source_freshness = build_dbt_step(
        name=f"{data_source}_dbt_source_freshness",
        args=_source_freshness_args(data_source),
        deps=[bronze_asset],
        description=f"dbt source freshness --select source:{data_source}",
        group_name=source_steps_group,
    )
    source_tests = build_dbt_step(
        name=f"{data_source}_dbt_source_tests",
        args=_source_tests_args(data_source),
        deps=[source_freshness],
        description=f"dbt test --select source:{data_source}",
        group_name=source_steps_group,
    )

    def _layer_build(
        *,
        layer_tag: str,
        gate_on_source_tests: bool,
    ) -> AssetsDefinition | None:
        required_tags = {layer_tag, data_source}
        if not _manifest_has_tagged_asset(manifest_path, required_tags):
            return None

        select = f"tag:{layer_tag},tag:{data_source}"
        translator = (
            SourceTestsGateTranslator(
                required_tags=required_tags,
                gate_asset=source_tests,
            )
            if gate_on_source_tests
            else DagsterDbtTranslator()
        )

        @dbt_assets(
            manifest=manifest_path,
            select=select,
            name=f"{data_source}_dbt_{layer_tag}_build",
            dagster_dbt_translator=translator,
        )
        def _build(context: AssetExecutionContext, dbt: DbtCliResource):
            yield from dbt.cli(
                _layer_build_args(layer_tag, data_source),
                context=context,
            ).stream()

        return _build

    return DbtSourcePipeline(
        source_freshness=source_freshness,
        source_tests=source_tests,
        silver_build=_layer_build(layer_tag=SILVER_TAG, gate_on_source_tests=True),
        gold_build=_layer_build(layer_tag=GOLD_TAG, gate_on_source_tests=False),
    )
