//! Render one thumbnail per show listed in `examples.json`.
//!
//! ```sh
//! cargo run --manifest-path tools/thumbnails/Cargo.toml [-- --check]
//! ```
//!
//! Every show is loaded like the player does, its driver script is played
//! for the entry's `thumbnail_at` seconds (2 by default) and the frame is
//! written to `site/thumbnails/<path>.png`, brought to roughly 640 pixels
//! wide by a whole factor. A `dots` pass of the show's output is drawn into
//! the thumbnail, since the offscreen renderer leaves passes to whoever
//! shows the frame. A show fails the run when it does not load or
//! loads with warnings, when a layer names an image or font that is not in
//! its assets (the engine would skip the layer silently), when an asset is
//! not used by any layer, or when its driver script fires a trigger or sets
//! a variable the show does not have; `--check` stops after that and renders
//! nothing, so it needs no GPU (and with `--no-default-features` the
//! renderer is not built at all).

#[cfg(feature = "render")]
use cuelight::render::{Renderer, RgbaFrame};
#[cfg(feature = "render")]
use cuelight::{DotShape, Dots, Pass};
use cuelight::{Engine, Layer, LayerKind};
use cuelight_loader::{Driver, DriverPlayer, Step};
use std::collections::BTreeSet;
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
        let mut loaded = match cuelight_loader::load(&mut engine, root.join(path)) {
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
        // The loader parsed the driver script that came with the show.
        let driver = loaded.driver.take();
        for problem in references(&engine, &loaded, driver.as_ref()) {
            eprintln!("{path}: {problem}");
            problems += 1;
        }
        let driver = driver.map(DriverPlayer::new);
        #[cfg(feature = "render")]
        if let Some(renderer) = renderer.as_mut() {
            let mut driver = driver;
            for _ in 0..(seconds * FPS).round() as u32 {
                if let Some(driver) = driver.as_mut() {
                    driver.advance(&mut engine, 1.0 / FPS);
                }
                engine.advance_frame(1.0 / FPS);
            }
            let frame = renderer.render_to_rgba(&engine)?;
            let up = TARGET_WIDTH / frame.width;
            let pass = engine.passes().into_iter().find_map(|pass| match pass {
                Pass::Dots(dots) if up >= 3 => Some(dots),
                _ => None,
            });
            let frame = match pass {
                Some(pass) => dots(&frame, up, &pass),
                None => resize(frame),
            };
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

/// What the show and its driver refer to that is not there, and the assets
/// nothing refers to.
fn references(
    engine: &Engine,
    loaded: &cuelight_loader::Loaded,
    driver: Option<&Driver>,
) -> Vec<String> {
    fn walk(engine: &Engine, layers: &[Layer], used: &mut BTreeSet<String>, out: &mut Vec<String>) {
        for layer in layers {
            if let LayerKind::Image { image, .. } = &layer.kind {
                used.insert(image.clone());
                if engine.image(image).is_none() {
                    out.push(format!(
                        "layer {:?} shows image {image:?}, which is not in assets/",
                        layer.name
                    ));
                }
            }
            walk(engine, layer.children(), used, out);
        }
    }

    let show = engine.show().expect("show loaded");
    let mut out = Vec::new();
    let mut used = BTreeSet::new();
    for layers in show.layer_trees() {
        walk(engine, layers, &mut used, &mut out);
    }
    for (name, style) in &show.fonts {
        used.insert(style.file.clone());
        if !engine.has_font(&style.file) {
            out.push(format!(
                "font style {name:?} uses {:?}, which is not in assets/fonts/",
                style.file
            ));
        }
    }
    for asset in loaded.images.iter().chain(&loaded.fonts) {
        if !used.contains(asset) {
            out.push(format!("asset {asset:?} is not used by the show"));
        }
    }

    let triggers = show.triggers();
    for step in driver.map(|d| d.steps.as_slice()).unwrap_or_default() {
        match step {
            Step::Trigger { trigger } if !triggers.contains(trigger) => {
                out.push(format!(
                    "the driver fires {trigger:?}, which nothing listens to"
                ));
            }
            Step::Set { set } => {
                for variable in set.keys().filter(|v| !show.variables.contains_key(*v)) {
                    out.push(format!(
                        "the driver sets {variable:?}, which is not a variable"
                    ));
                }
            }
            _ => {}
        }
    }
    out.sort();
    out.dedup();
    out
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

/// The dot matrix look of a `dots` pass, the way the presenter shows it:
/// every canvas pixel a dot of `up` pixels on black, never darker than the
/// unlit color, with a smoothly scaled copy of the frame screened on top as
/// the glow.
#[cfg(feature = "render")]
fn dots(frame: &RgbaFrame, up: u32, dots: &Dots) -> RgbaFrame {
    let (width, height) = (frame.width * up, frame.height * up);
    let unlit = dots.unlit.as_deref().and_then(rgb).unwrap_or([0; 3]);
    let texel = |x: u32, y: u32, c: usize| {
        f64::from(frame.pixels[((y * frame.width + x) * 4) as usize + c])
    };
    // Where an output pixel lies between the canvas pixels around it.
    let between = |at: u32, size: u32| {
        let u = ((f64::from(at) + 0.5) / f64::from(up) - 0.5).clamp(0.0, f64::from(size - 1));
        (
            u.floor() as u32,
            (u.floor() as u32 + 1).min(size - 1),
            u.fract(),
        )
    };
    let mut pixels = Vec::with_capacity((width * height * 4) as usize);
    for y in 0..height {
        for x in 0..width {
            // Distance from the dot's center, in pixel pitches.
            let offset = |at: u32| (f64::from(at % up) + 0.5) / f64::from(up) - 0.5;
            let distance = match dots.shape {
                DotShape::Square => offset(x).abs().max(offset(y).abs()),
                _ => offset(x).hypot(offset(y)),
            };
            let cover = ((dots.size / 2.0 - distance) * f64::from(up) + 0.5).clamp(0.0, 1.0);
            let ((x0, x1, fx), (y0, y1, fy)) = (between(x, frame.width), between(y, frame.height));
            for (c, unlit) in unlit.iter().enumerate() {
                let dot = texel(x / up, y / up, c).max(f64::from(*unlit)) / 255.0 * cover;
                let top = texel(x0, y0, c) * (1.0 - fx) + texel(x1, y0, c) * fx;
                let bottom = texel(x0, y1, c) * (1.0 - fx) + texel(x1, y1, c) * fx;
                let glow = (top * (1.0 - fy) + bottom * fy) / 255.0 * dots.glow;
                pixels.push(((dot + glow * (1.0 - dot)) * 255.0).round() as u8);
            }
            pixels.push(255);
        }
    }
    RgbaFrame {
        width,
        height,
        pixels,
    }
}

/// `#RRGGBB` as bytes.
#[cfg(feature = "render")]
fn rgb(color: &str) -> Option<[u8; 3]> {
    let hex = color.strip_prefix('#').filter(|hex| hex.len() == 6)?;
    let value = u32::from_str_radix(hex, 16).ok()?;
    Some([(value >> 16) as u8, (value >> 8) as u8, value as u8])
}
