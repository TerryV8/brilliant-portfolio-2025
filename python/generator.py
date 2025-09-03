"""
MAIN GOAL: Demonstrate Python generators and benchmark them vs regular lists.

This file shows:
- Generator functions with yield statements
- Lazy evaluation vs eager evaluation
- Memory efficiency comparisons
- Performance benchmarking between generators and lists
- Practical use cases for generators in data processing
"""

import time
from typing import Generator, List


def generate_numbers(n: int) -> Generator[int, None, None]:
    """Generator version - yields numbers one by one"""
    for i in range(n):
        yield i**2


def create_list(n: int) -> List[int]:
    """Non-generator version - creates entire list in memory"""
    return [i**2 for i in range(n)]


def benchmark_memory_usage(n: int = 1000000) -> None:
    """Benchmark generator vs list for memory and time"""
    print(f"Benchmarking with {n:,} numbers\n")

    # === GENERATOR APPROACH ===
    print("🔄 GENERATOR APPROACH:")

    # Time generator creation (should be instant)
    start = time.time()
    gen = generate_numbers(n)
    creation_time = time.time() - start
    print(f"  Creation time: {creation_time:.6f} seconds")

    # Time consuming first 10 values
    start = time.time()
    first_10 = [next(gen) for _ in range(10)]
    consumption_time = time.time() - start
    print(f"  First 10 values: {first_10}")
    print(f"  Time to get first 10: {consumption_time:.6f} seconds")

    # === LIST APPROACH ===
    print("\n📋 LIST APPROACH:")

    # Time list creation (creates everything upfront)
    start = time.time()
    numbers_list = create_list(n)
    list_creation_time = time.time() - start
    print(f"  Creation time: {list_creation_time:.6f} seconds")

    # Time accessing first 10 values
    start = time.time()
    first_10_list = numbers_list[:10]
    access_time = time.time() - start
    print(f"  First 10 values: {first_10_list}")
    print(f"  Time to access first 10: {access_time:.6f} seconds")

    # === COMPARISON ===
    print(f"\n📊 COMPARISON:")
    print(
        f"  Generator creation: {creation_time:.6f}s vs List creation: {list_creation_time:.6f}s"
    )
    print(
        f"  Speed difference: {list_creation_time / max(creation_time, 0.000001):.1f}x faster generator creation"
    )
    print(
        f"  Memory: Generator uses ~constant memory, List uses ~{len(numbers_list) * 28} bytes"
    )


def benchmark_processing_speed(n: int = 100000) -> None:
    """Benchmark processing speed when consuming all values"""
    print(f"\n" + "=" * 60)
    print(f"PROCESSING SPEED BENCHMARK ({n:,} numbers)")
    print("=" * 60)

    # Generator - process all values
    start = time.time()
    gen = generate_numbers(n)
    total = sum(gen)  # Consume all values
    gen_time = time.time() - start
    print(f"Generator total processing: {gen_time:.6f} seconds (sum: {total})")

    # List - create and sum all values
    start = time.time()
    numbers_list = create_list(n)
    total_list = sum(numbers_list)
    list_time = time.time() - start
    print(f"List total processing: {list_time:.6f} seconds (sum: {total_list})")

    # Comparison
    if gen_time < list_time:
        print(f"🏆 Generator is {list_time / gen_time:.2f}x faster for full processing")
    else:
        print(f"🏆 List is {gen_time / list_time:.2f}x faster for full processing")


if __name__ == "__main__":
    # Run benchmarks
    benchmark_memory_usage(1000000000)  # 1 million numbers
    benchmark_processing_speed(100000000)  # 100k numbers for speed test
