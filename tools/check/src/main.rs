//! Check every show listed in `examples.json`.
//!
//! ```sh
//! cargo run --manifest-path tools/check/Cargo.toml
//! ```
//!
//! Every show is loaded like the player does, with its sounds decoded. A
//! show fails the run when it does not load or loads with warnings, when a
//! sound does not decode, when a layer names an image or font that is not
//! in its assets (the engine would skip the layer silently), when an asset
//! is not used by any layer, or when its driver script fires a trigger or
//! sets a variable the show does not have. Needs no GPU.

use cuelight::{DigitDisplay, Engine, Layer, LayerKind, ReelCells};
use cuelight_audio::Sound;
use cuelight_loader::{Driver, Step};
use std::collections::BTreeSet;
use std::path::Path;

fn main() -> std::process::ExitCode {
    match run() {
        Ok(()) => std::process::ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("{e}");
            std::process::ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let catalog: serde_json::Value =
        serde_json::from_str(&std::fs::read_to_string(root.join("examples.json"))?)?;
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
        for file in &loaded.sounds {
            if let Err(e) = Sound::decode(&file.extension, &file.bytes) {
                eprintln!("{path}: sound {:?}: {e}", file.name);
                problems += 1;
            }
        }
        // The loader parsed the driver script that came with the show.
        let driver = loaded.driver.take();
        for problem in references(&engine, &loaded, driver.as_ref()) {
            eprintln!("{path}: {problem}");
            problems += 1;
        }
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
            if let LayerKind::Vector { vector, .. } = &layer.kind {
                used.insert(vector.clone());
                if engine.vector(vector).is_none() {
                    out.push(format!(
                        "layer {:?} shows vector {vector:?}, which is not in assets/",
                        layer.name
                    ));
                }
            }
            // A reel row draws its symbols from artwork, one per character
            // of its ring, which counts as using those assets too.
            if let LayerKind::Digits {
                display: DigitDisplay::Reel(reel),
                ..
            } = &layer.kind
            {
                match reel.cells.as_ref() {
                    Some(ReelCells::Vectors(names)) => {
                        for name in names {
                            used.insert(name.clone());
                            if engine.vector(name).is_none() {
                                out.push(format!(
                                    "layer {:?} rolls vector {name:?}, which is not in assets/",
                                    layer.name
                                ));
                            }
                        }
                    }
                    Some(ReelCells::Images(names)) => {
                        for name in names {
                            used.insert(name.clone());
                            if engine.image(name).is_none() {
                                out.push(format!(
                                    "layer {:?} rolls image {name:?}, which is not in assets/",
                                    layer.name
                                ));
                            }
                        }
                    }
                    // ReelCells is non-exhaustive: artwork kinds added
                    // later go unchecked rather than failing to build.
                    _ => {}
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
    for asset in loaded
        .images
        .iter()
        .chain(&loaded.vectors)
        .chain(&loaded.fonts)
    {
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
                // Setting a name the show animates itself takes that value
                // over, which is what a host may do.
                for variable in set
                    .keys()
                    .filter(|v| !show.variables.contains_key(*v) && !show.values.contains_key(*v))
                {
                    out.push(format!(
                        "the driver sets {variable:?}, which is not a variable or a value"
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
