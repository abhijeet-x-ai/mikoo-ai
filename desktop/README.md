# Mikoo Desktop

Mikoo Desktop is the cross-platform desktop shell for the offline coding agent. It uses a Tauri 2 Rust backend with a static HTML/CSS/JavaScript frontend. The backend loads the bundled `models/mikoo_bootstrap.bin` checkpoint and performs local byte-level GRU inference; it does not call a cloud model, API, or network service.

## Local development

Install Rust, the platform WebView development packages, and the Tauri CLI. On Ubuntu, the repository was validated with Rust 1.98, Tauri CLI 2.11.4, GTK 3, WebKitGTK 4.1, and `libxdo-dev`.

From this directory:

```bash
cargo tauri dev --manifest-path src-tauri/Cargo.toml
```

The static frontend is in `frontend/`. The Rust project is in `src-tauri/`. The local model is in `models/mikoo_bootstrap.bin` and is included as a bundle resource.

## Tests and Linux package

```bash
cargo test --manifest-path src-tauri/Cargo.toml --locked
cargo tauri build --manifest-path src-tauri/Cargo.toml --bundles deb --ci
```

The validated Linux artifact is `src-tauri/target/release/bundle/deb/Mikoo_0.1.0_amd64.deb`. It contains the desktop executable and the bundled local checkpoint.

## Windows and macOS

Tauri packaging is configured for all targets, but native Windows and macOS installers must be built on their respective operating systems because their WebView, signing, and packaging toolchains are platform-specific. On Windows use `cargo tauri build`; on macOS use `cargo tauri build`. The same source and model resource are used on all platforms.

## Product boundary

The desktop shell supports local chat generation, local history, workspace-path validation, explicit agent state, and an approval-oriented interface. The bundled checkpoint is a small self-authored bootstrap model used to validate the local runtime. It is not the planned 6B teacher or the larger production coding student. The 6B profile remains training/distillation-only; the mobile-sized student profile remains the target for constrained devices.
