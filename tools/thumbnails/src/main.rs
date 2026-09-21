//! Render one thumbnail per show listed in `examples.json`.
//!
//! ```sh
//! cargo run --manifest-path tools/thumbnails/Cargo.toml [-- --check]
//! ```
//!
//! Every show is loaded like the player does, its driver script is played
//! for the entry's `thumbnail_at` seconds (2 by default) and the frame is
//! written to `site/thumbnails/<path>.png`, brought to roughly 640 pixels
//! wide by a whole factor. A show that fails to load, or loads with
//! warnings, fails the run; `--check` stops after that and renders
//! nothing, so it needs no GPU (and with `--no-default-features` the
//! renderer is not built at all).

#[cfg(feature = "render")]
use cuelight::render::{Renderer, RgbaFrame};
use cuelight::Engine;
use cuelight_loader::{Driver, DriverPlayer};
use std::path::Path;

#[cfg(feature = "render")]
const FPS: f64 = 60.0;
#[cfg(feature = "render")]
const TARGET_WIDTH: u32 = 640;

fn main() -> std::process::ExitCode {
    let check_only = std::env::args().any(|a| a == "--check");
    match run(check_only) {
        Ok(()) => std::process::ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("{e}");
            std::process::ExitCode::FAILURE
        }
    }
}

fn run(check_only: bool) -> Result<(), Box<dyn std::error::Error>> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let catalog: serde_json::Value =
        serde_json::from_str(&std::fs::read_to_string(root.join("examples.json"))?)?;
    #[cfg(feature = "render")]
    let mut renderer = if check_only {
        None
    } else {
        Some(Renderer::new()?)
    };
    #[cfg(not(feature = "render"))]
    if !check_only {
        return Err("built without the render feature: only --check works".into());
    }

    let mut problems = 0;
    let examples = catalog["categories"]
        .as_array()
        .into_iter()
        .flatten()
        .flat_map(|category| category["examples"].as_array().into_iter().flatten());
    for example in examples {
        let path = example["path"]
            .as_str()
            .ok_or("an example without a path")?;
        let seconds = example["thumbnail_at"].as_f64().unwrap_or(2.0);

        let mut engine = Engine::new();
        let loaded = match cuelight_loader::load(&mut engine, root.join(path)) {
            Ok(loaded) => loaded,
            Err(e) => {
                eprintln!("{path}: {e}");
                problems += 1;
                continue;
            }
        };
        for field in engine.load_warnings() {
            eprintln!("{path}: show field {field:?} is not understood");
            problems += 1;
        }
        for skipped in &loaded.skipped {
            eprintln!("{path}: asset {skipped:?} has no decoder");
            problems += 1;
        }
        // A driver script that does not parse is a problem too.
        let driver = match &loaded.driver {
            Some(file) => Some(DriverPlayer::new(Driver::from_file(file)?)),
            None => None,
        };
        #[cfg(feature = "render")]
        if let Some(renderer) = renderer.as_mut() {
            let mut driver = driver;
            for _ in 0..(seconds * FPS).round() as u32 {
                if let Some(driver) = driver.as_mut() {
                    driver.advance(&mut engine, 1.0 / FPS);
                }
                engine.advance_frame(1.0 / FPS);
            }
            let frame = resize(renderer.render_to_rgba(&engine)?);
            let out = root.join("site/thumbnails").join(format!("{path}.png"));
            std::fs::create_dir_all(out.parent().expect("has a parent"))?;
            frame.write_png(&out)?;
            println!("{path}: {}x{} at {seconds} s", frame.width, frame.height);
            continue;
        }
        let _ = (driver, seconds);
        println!("{path}: ok");
    }
    if problems > 0 {
        return Err(format!("{problems} problem(s)").into());
    }
    Ok(())
}

/// Bring a frame to about [`TARGET_WIDTH`] by a whole factor: small
/// canvases are repeated pixel for pixel, large ones box filtered.
#[cfg(feature = "render")]
fn resize(frame: RgbaFrame) -> RgbaFrame {
    let up = TARGET_WIDTH / frame.width;
    let down = frame.width.div_ceil(TARGET_WIDTH);
    if up > 1 {
        let (width, height) = (frame.width * up, frame.height * up);
        let mut pixels = Vec::with_capacity((width * height * 4) as usize);
        for y in 0..height {
            for x in 0..width {
                let at = ((y / up * frame.width + x / up) * 4) as usize;
                pixels.extend_from_slice(&frame.pixels[at..at + 4]);
            }
        }
        RgbaFrame {
            width,
            height,
            pixels,
        }
    } else if down > 1 {
        let (width, height) = (frame.width / down, frame.height / down);
        let mut pixels = Vec::with_capacity((width * height * 4) as usize);
        for y in 0..height {
            for x in 0..width {
                let mut sum = [0u32; 4];
                for dy in 0..down {
                    for dx in 0..down {
                        let at = (((y * down + dy) * frame.width + x * down + dx) * 4) as usize;
                        for (s, p) in sum.iter_mut().zip(&frame.pixels[at..at + 4]) {
                            *s += u32::from(*p);
                        }
                    }
                }
                pixels.extend(sum.map(|s| (s / (down * down)) as u8));
            }
        }
        RgbaFrame {
            width,
            height,
            pixels,
        }
    } else {
        frame
    }
}
