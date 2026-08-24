#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::{Path, PathBuf};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Mutex, OnceLock,
};

use tauri::{AppHandle, Manager};

const MAGIC: &[u8; 8] = b"MKGRU01\0";
const VOCAB: usize = 256;
const EMBED: usize = 128;
const HIDDEN: usize = 256;
const MAX_GENERATION_TOKENS: usize = 1024;

struct Model {
    embedding: Vec<f32>,
    weight_ih: Vec<f32>,
    weight_hh: Vec<f32>,
    bias_ih: Vec<f32>,
    bias_hh: Vec<f32>,
    output_weight: Vec<f32>,
    output_bias: Vec<f32>,
    path: PathBuf,
}

static MODEL: OnceLock<Mutex<Option<Model>>> = OnceLock::new();
static CANCEL: AtomicBool = AtomicBool::new(false);

fn model_slot() -> &'static Mutex<Option<Model>> {
    MODEL.get_or_init(|| Mutex::new(None))
}

fn read_u32(bytes: &[u8], offset: &mut usize) -> Result<u32, String> {
    if *offset + 4 > bytes.len() {
        return Err("checkpoint header is truncated".into());
    }
    let value = u32::from_le_bytes(bytes[*offset..*offset + 4].try_into().unwrap());
    *offset += 4;
    Ok(value)
}

fn read_f32_vec(bytes: &[u8], offset: &mut usize, count: usize) -> Result<Vec<f32>, String> {
    let byte_count = count.checked_mul(4).ok_or("checkpoint size overflow")?;
    if *offset + byte_count > bytes.len() {
        return Err("checkpoint tensor is truncated".into());
    }
    let mut values = Vec::with_capacity(count);
    for chunk in bytes[*offset..*offset + byte_count].chunks_exact(4) {
        values.push(f32::from_le_bytes(chunk.try_into().unwrap()));
    }
    *offset += byte_count;
    Ok(values)
}

fn parse_model(path: &Path) -> Result<Model, String> {
    let bytes = std::fs::read(path).map_err(|error| format!("cannot read checkpoint: {error}"))?;
    if bytes.len() < 24 || &bytes[..8] != MAGIC {
        return Err("invalid Mikoo checkpoint magic".into());
    }
    let mut offset = 8;
    let vocab = read_u32(&bytes, &mut offset)? as usize;
    let embed = read_u32(&bytes, &mut offset)? as usize;
    let hidden = read_u32(&bytes, &mut offset)? as usize;
    let _reserved = read_u32(&bytes, &mut offset)?;
    if (vocab, embed, hidden) != (VOCAB, EMBED, HIDDEN) {
        return Err("unsupported Mikoo checkpoint dimensions".into());
    }
    let model = Model {
        embedding: read_f32_vec(&bytes, &mut offset, VOCAB * EMBED)?,
        weight_ih: read_f32_vec(&bytes, &mut offset, 3 * HIDDEN * EMBED)?,
        weight_hh: read_f32_vec(&bytes, &mut offset, 3 * HIDDEN * HIDDEN)?,
        bias_ih: read_f32_vec(&bytes, &mut offset, 3 * HIDDEN)?,
        bias_hh: read_f32_vec(&bytes, &mut offset, 3 * HIDDEN)?,
        output_weight: read_f32_vec(&bytes, &mut offset, VOCAB * HIDDEN)?,
        output_bias: read_f32_vec(&bytes, &mut offset, VOCAB)?,
        path: path.to_path_buf(),
    };
    Ok(model)
}

fn locate_model(app: &AppHandle) -> Result<PathBuf, String> {
    let candidates = [
        app.path()
            .resource_dir()
            .ok()
            .map(|dir| dir.join("models/mikoo_bootstrap.bin")),
        app.path()
            .resource_dir()
            .ok()
            .map(|dir| dir.join("_up_/models/mikoo_bootstrap.bin")),
        app.path()
            .resource_dir()
            .ok()
            .map(|dir| dir.join("resources/models/mikoo_bootstrap.bin")),
        std::env::current_dir()
            .ok()
            .map(|dir| dir.join("models/mikoo_bootstrap.bin")),
        std::env::current_dir()
            .ok()
            .map(|dir| dir.join("../models/mikoo_bootstrap.bin")),
        std::env::current_dir()
            .ok()
            .map(|dir| dir.join("desktop/models/mikoo_bootstrap.bin")),
    ];
    candidates
        .into_iter()
        .flatten()
        .find(|path| path.is_file())
        .ok_or_else(|| "Mikoo checkpoint not found in bundled resources".into())
}

fn sigmoid(value: f32) -> f32 {
    if value >= 0.0 {
        let z = (-value).exp();
        1.0 / (1.0 + z)
    } else {
        let z = value.exp();
        z / (1.0 + z)
    }
}

fn gru_step(
    model: &Model,
    token: u8,
    hidden: &mut [f32; HIDDEN],
    input_gate: &mut [f32; 3 * HIDDEN],
    recurrent_gate: &mut [f32; 3 * HIDDEN],
) {
    input_gate.fill(0.0);
    recurrent_gate.fill(0.0);
    let x_offset = token as usize * EMBED;
    for gate in 0..3 {
        let gate_offset = gate * HIDDEN;
        for row in 0..HIDDEN {
            let mut input_value = model.bias_ih[gate_offset + row];
            let mut recurrent_value = model.bias_hh[gate_offset + row];
            let input_offset = gate_offset * EMBED + row * EMBED;
            let hidden_offset = gate_offset * HIDDEN + row * HIDDEN;
            for column in 0..EMBED {
                input_value +=
                    model.weight_ih[input_offset + column] * model.embedding[x_offset + column];
            }
            for column in 0..HIDDEN {
                recurrent_value += model.weight_hh[hidden_offset + column] * hidden[column];
            }
            input_gate[gate_offset + row] = input_value;
            recurrent_gate[gate_offset + row] = recurrent_value;
        }
    }
    let previous = *hidden;
    for row in 0..HIDDEN {
        let reset = sigmoid(input_gate[row] + recurrent_gate[row]);
        let update = sigmoid(input_gate[HIDDEN + row] + recurrent_gate[HIDDEN + row]);
        let candidate =
            (input_gate[2 * HIDDEN + row] + reset * recurrent_gate[2 * HIDDEN + row]).tanh();
        hidden[row] = (1.0 - update) * candidate + update * previous[row];
    }
}

fn generate(
    model: &Model,
    prompt: &str,
    max_tokens: usize,
    context_tokens: usize,
) -> Result<String, String> {
    if prompt.len() > context_tokens.saturating_mul(16) {
        return Err("prompt exceeds the local context safety bound".into());
    }
    CANCEL.store(false, Ordering::Release);
    let model_prompt = format!("<|user|>\n{prompt}\n<|assistant|>\n");
    let mut hidden = [0.0f32; HIDDEN];
    let mut input_gate = [0.0f32; 3 * HIDDEN];
    let mut recurrent_gate = [0.0f32; 3 * HIDDEN];
    for byte in model_prompt.bytes() {
        gru_step(
            model,
            byte,
            &mut hidden,
            &mut input_gate,
            &mut recurrent_gate,
        );
    }
    let limit = max_tokens.clamp(32, MAX_GENERATION_TOKENS);
    let mut output = Vec::with_capacity(limit);
    for _ in 0..limit {
        if CANCEL.load(Ordering::Acquire) {
            break;
        }
        let mut best_token = 0usize;
        let mut best_score = f32::NEG_INFINITY;
        for token in 0..VOCAB {
            let mut score = model.output_bias[token];
            let offset = token * HIDDEN;
            for column in 0..HIDDEN {
                score += model.output_weight[offset + column] * hidden[column];
            }
            if score > best_score {
                best_score = score;
                best_token = token;
            }
        }
        output.push(best_token as u8);
        gru_step(
            model,
            best_token as u8,
            &mut hidden,
            &mut input_gate,
            &mut recurrent_gate,
        );
        if output.windows(7).any(|window| window == b"<|end|>") {
            break;
        }
    }
    let text = String::from_utf8_lossy(&output)
        .split("<|end|>")
        .next()
        .unwrap_or("")
        .trim()
        .to_string();
    if text.is_empty() {
        Err("local model returned an empty response".into())
    } else {
        Ok(text)
    }
}

#[tauri::command]
fn load_model(app: AppHandle) -> Result<String, String> {
    let path = locate_model(&app)?;
    let model = parse_model(&path)?;
    let mut slot = model_slot().lock().map_err(|_| "model lock poisoned")?;
    *slot = Some(model);
    Ok("Mikoo local checkpoint loaded; offline inference active".into())
}

#[tauri::command]
fn generate_response(
    prompt: String,
    max_tokens: usize,
    context_tokens: usize,
) -> Result<String, String> {
    let slot = model_slot().lock().map_err(|_| "model lock poisoned")?;
    let model = slot.as_ref().ok_or("local checkpoint is not loaded")?;
    generate(model, &prompt, max_tokens, context_tokens)
}

#[tauri::command]
fn cancel_generation() -> Result<(), String> {
    CANCEL.store(true, Ordering::Release);
    Ok(())
}

#[tauri::command]
fn validate_workspace(path: String) -> Result<String, String> {
    let trimmed = path.trim();
    if trimmed.is_empty() {
        return Err("workspace path is empty".into());
    }
    let candidate = PathBuf::from(trimmed);
    if !candidate.is_dir() {
        return Err("workspace folder does not exist".into());
    }
    let canonical = candidate
        .canonicalize()
        .map_err(|error| format!("cannot resolve workspace: {error}"))?;
    Ok(format!(
        "Workspace ready: {}. Writes and tests remain approval-gated.",
        canonical.display()
    ))
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            load_model,
            generate_response,
            cancel_generation,
            validate_workspace
        ])
        .run(tauri::generate_context!())
        .expect("error while running Mikoo Desktop");
}

#[cfg(test)]
mod tests {
    use super::*;

    fn bundled_checkpoint() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../models/mikoo_bootstrap.bin")
    }

    #[test]
    fn bundled_checkpoint_parses() {
        let model = parse_model(&bundled_checkpoint()).expect("bundled checkpoint must parse");
        assert_eq!(model.embedding.len(), VOCAB * EMBED);
        assert_eq!(model.output_bias.len(), VOCAB);
    }

    #[test]
    fn local_generation_returns_readable_response() {
        let model = parse_model(&bundled_checkpoint()).expect("bundled checkpoint must parse");
        let response = generate(&model, "Hello", 768, 1024).expect("local generation must respond");
        assert!(response.contains("Mikoo") || response.contains("Hello"));
        assert!(response.len() <= 768);
    }
}
