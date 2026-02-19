#!/usr/bin/env python3
"""Quick latency benchmark for core read-only operations."""

from __future__ import annotations

import argparse
import statistics
import time

from lib.features.simulator_control.data.datasources.simctl_datasource import SimctlDatasource


def benchmark_operation(name: str, operation, iterations: int) -> dict:
    latencies_ms = []
    last_success = False
    for _ in range(iterations):
        start = time.perf_counter()
        result = operation()
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies_ms.append(elapsed_ms)
        last_success = result.is_success

    p95_index = max(0, min(len(latencies_ms) - 1, int(iterations * 0.95) - 1))
    sorted_latencies = sorted(latencies_ms)
    return {
        "name": name,
        "success": last_success,
        "avg_ms": statistics.mean(latencies_ms),
        "min_ms": min(latencies_ms),
        "max_ms": max(latencies_ms),
        "p95_ms": sorted_latencies[p95_index],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark iOS Simulator MCP read operations")
    parser.add_argument(
        "--iterations",
        type=int,
        default=20,
        help="Number of iterations per operation",
    )
    args = parser.parse_args()

    datasource = SimctlDatasource()
    operations = [
        ("list_simulators", datasource.list_simulators),
        ("list_runtimes", datasource.list_runtimes),
        ("list_device_types", datasource.list_device_types),
    ]

    for name, operation in operations:
        metrics = benchmark_operation(name, operation, args.iterations)
        print(
            f"{metrics['name']}: success={metrics['success']} "
            f"avg={metrics['avg_ms']:.2f}ms p95={metrics['p95_ms']:.2f}ms "
            f"min={metrics['min_ms']:.2f}ms max={metrics['max_ms']:.2f}ms"
        )


if __name__ == "__main__":
    main()
