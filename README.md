<div align="center">

```
    ____  __    ___   ________ __ ____  ____  ___    ____
   / __ )/ /   /   | / ____/ //_// __ \/ __ \/   |  / __ \
  / __  / /   / /| |/ /   / ,<  / /_/ / / / / /| | / / / /
 / /_/ / /___/ ___ / /___/ /| |/ _, _/ /_/ / ___ |/ /_/ /
/_____/_____/_/  |_\____/_/ |_/_/ |_|\____/_/  |_/_____/
```

**I build systems from scratch. Compilers, quantum simulators, AI infrastructure, fleet orchestration.**

[![CI](https://img.shields.io/badge/CI-passing-00e676?style=flat-square)](#projects)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](#projects)
[![C99](https://img.shields.io/badge/C99-zero_deps-A8B9CC?style=flat-square&logo=c&logoColor=white)](#projects)
[![Shell](https://img.shields.io/badge/Shell-400+_scripts-4EAA25?style=flat-square&logo=gnu-bash&logoColor=white)](#projects)

</div>

---

## Projects

### [RoadC](https://github.com/blackboxprogramming/roadc) &mdash; Programming Language

A custom language with Python-style indentation, built from scratch. Lexer, parser, AST, tree-walking interpreter in Python. Zero-dependency C99 compiler. Supports functions, recursion, pattern matching, type annotations.

```road
fun fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

### [Quantum Math Lab](https://github.com/blackboxprogramming/quantum-math-lab) &mdash; Quantum Circuit Simulator

Pure-Python state-vector simulator. Hadamard, Pauli-X, CNOT, custom unitaries, measurement with configurable RNG. Companion catalog of 10 unsolved problems in mathematics.

```python
circuit = QuantumCircuit(2)
circuit.hadamard(0)
circuit.cnot(0, 1)          # Bell state: |00> + |11>
circuit.probabilities()      # {'00': 0.5, '11': 0.5}
```

### [The Trivial Zero](https://github.com/blackboxprogramming/simulation-theory) &mdash; Computational Philosophy

675-section research paper with 20+ supporting Python demos. SHA-256 hash chains, Godel incompleteness, Riemann zeta zeros, DNA encoding, Lorenz chaos. Published to npm. Live evidence explorer and VR app.

### [Universal Computer](https://github.com/blackboxprogramming/universal-computer) &mdash; Turing Machine Simulator

Universal Turing machine implementation. Dictionary-based infinite tape, JSON machine descriptions, configurable step limits. Included machines: binary incrementer, parity checker, palindrome detector.

### [Lucidia CLI](https://github.com/blackboxprogramming/lucidia-cli) &mdash; Terminal Operating System

Full TUI application built on Textual/Rich. Terminal web browser with HTML parser, sandboxed virtual filesystem, Ollama AI agents with multi-personality council mode, background process manager.

### [blackroad-scripts](https://github.com/blackboxprogramming/blackroad-scripts) &mdash; Fleet Automation

400+ shell scripts managing a 5-node Raspberry Pi cluster. WireGuard mesh networking, Cloudflare tunnel orchestration, Docker Swarm, automated health monitoring, deployment pipelines.

---

## Infrastructure

```
Cluster        5x Raspberry Pi 5 (4x 8GB + 1x Pi 400)
AI             2x Hailo-8 accelerators (52 TOPS), 16 Ollama models
Networking     WireGuard mesh, 48 domains, 18 Cloudflare tunnels
Storage        1TB NVMe, Gitea (207 repos), MinIO S3
Orchestration  Docker Swarm, systemd fleet, cron autonomy
Monitoring     Custom health agents, power optimization, thermal management
```

All self-hosted. No cloud compute dependency.

---

## Stats

```
Languages      Python, C, Shell, TypeScript, JavaScript, SQL
Repos          49 public, 207 on self-hosted Gitea
Scripts        400+ production shell scripts
Test Suites    pytest, Playwright, shellcheck
CI/CD          GitHub Actions across all active repos
```

---

<div align="center">

**Alexa Amundson** &mdash; [blackroad.io](https://blackroad.io) &mdash; amundsonalexa@gmail.com

</div>
