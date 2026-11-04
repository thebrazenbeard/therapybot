# Local launch scripts (development build)

The launchers **do not install dependencies or contact a package index during an ordinary start**. They check an existing `.venv`, verify Python 3.10+ and the declared `cryptography>=43,<51` requirement, then start the loopback-only TherapyBot application. They neither download nor load model weights on their own.

## Linux

```sh
sh launch/start-linux.sh --setup                # explicit one-time dependency installation; may access PyPI
sh launch/start-linux.sh --check                # local dependency check only; no model connection
sh launch/start-linux.sh --no-browser --model-url http://127.0.0.1:11435/completion
```

For installation from **preobtained platform-compatible wheels** without a package-index connection:

```sh
sh launch/start-linux.sh --setup-offline /absolute/path/to/wheels
```

That mode uses `pip --isolated --no-index` and fails if an appropriate wheel is missing. A relative wheel-directory path is resolved against the directory from which you invoke the launcher. The wheel directory and weights remain outside the repository. Verify downloaded package provenance before using it.

## Windows PowerShell

```powershell
.\launch\start-windows.ps1 -Setup             # explicit one-time dependency installation; may access PyPI
.\launch\start-windows.ps1 -Check             # local dependency check only
.\launch\start-windows.ps1 --no-browser --model-url http://127.0.0.1:5001/api/v1/generate
```

Offline dependency setup from an existing wheel directory:

```powershell
.\launch\start-windows.ps1 -SetupOffline 'D:\my-wheels'
```

Both scripts intentionally stop with an explanation if the environment is missing or incompatible. The check **does not establish that a GGUF model is installed, reachable, licensed, safe, or performant**; configure and start a compatible local KoboldCPP/llama.cpp service separately. A successful launch is development evidence, not approval for public interactive mental-health use.
