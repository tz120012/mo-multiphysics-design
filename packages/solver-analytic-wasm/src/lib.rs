//! Mo solver-analytic Wasm entry.
//!
//! JSON contract: `packages/solver-analytic/api/solve.schema.json`
//! (`SolveRequest` → `SolveResult`). Export for browsers via wasm-bindgen.

mod acim;
mod materials;
mod pmsm;

use serde_json::{json, Value};
use wasm_bindgen::prelude::*;

/// Solve a `SolveRequest` JSON string → `SolveResult` JSON string.
///
/// On parse / validation / unsupported-path errors returns a JSON object
/// `{ "error": { "code", "message" }, "meta": { "mock": false, "wasm": true } }`
/// (still a string so FE can `JSON.parse` uniformly).
#[wasm_bindgen]
pub fn solve_json(input: &str) -> String {
    match solve_json_inner(input) {
        Ok(v) => v.to_string(),
        Err(e) => json!({
            "error": { "code": e.0, "message": e.1 },
            "meta": { "mock": false, "wasm": true, "solver": "error" }
        })
        .to_string(),
    }
}

fn solve_json_inner(input: &str) -> Result<Value, (&'static str, String)> {
    let req: Value = serde_json::from_str(input)
        .map_err(|e| ("parse_error", format!("invalid JSON: {e}")))?;

    if !req.is_object() {
        return Err(("validation_error", "root must be a JSON object".into()));
    }

    let solver = req
        .get("solver")
        .and_then(|v| v.as_str())
        .unwrap_or("mec")
        .to_ascii_lowercase();
    if solver == "mock" {
        return Ok(mock_pmsm(&req)?);
    }
    if solver != "mec" {
        return Err((
            "validation_error",
            format!("unknown solver={solver}; expected mec|mock"),
        ));
    }

    let topo = req.get("topology").and_then(|v| v.as_str()).unwrap_or("");
    let mtype = req
        .get("machine_type")
        .and_then(|v| v.as_str())
        .unwrap_or("");

    if topo != "RF" {
        return Err((
            "not_implemented",
            format!("Wasm path is RF-only for Q2; topology={topo:?}"),
        ));
    }

    let catalog = req.get("materials_catalog");
    let materials = req.get("materials").cloned().unwrap_or(json!({}));

    match mtype {
        "PMSM" => {
            let mat = materials::resolve(&materials, catalog, true, false);
            pmsm::solve_pmsm(&req, &mat, false).map_err(|m| ("solve_error", m))
        }
        "BLDC" => {
            let mat = materials::resolve(&materials, catalog, true, false);
            pmsm::solve_pmsm(&req, &mat, true).map_err(|m| ("solve_error", m))
        }
        "ACIM" => {
            let mat = materials::resolve(&materials, catalog, false, true);
            acim::solve_acim(&req, &mat).map_err(|m| ("solve_error", m))
        }
        other => Err((
            "validation_error",
            format!("unsupported machine_type={other:?}"),
        )),
    }
}

fn mock_pmsm(req: &Value) -> Result<Value, (&'static str, String)> {
    let topo = req.get("topology").and_then(|v| v.as_str());
    let mtype = req.get("machine_type").and_then(|v| v.as_str());
    if topo != Some("RF") || mtype != Some("PMSM") {
        return Err((
            "validation_error",
            "mock path only covers RF + PMSM".into(),
        ));
    }
    let g = req.get("geometry").ok_or(("validation_error", "missing geometry".into()))?;
    let m = req.get("materials").cloned().unwrap_or(json!({}));
    let op = req
        .get("operating_point")
        .ok_or(("validation_error", "missing operating_point".into()))?;

    let poles = g.get("poles").and_then(|v| v.as_f64()).unwrap_or(10.0);
    let length = g
        .get("stack_length_m")
        .and_then(|v| v.as_f64())
        .unwrap_or(0.04);
    let rod = g.get("rotor_od_m").and_then(|v| v.as_f64()).unwrap_or(0.06);
    let turns = g
        .get("turns_per_phase")
        .and_then(|v| v.as_f64())
        .unwrap_or(1.0);
    let br = m
        .get("br_t")
        .or_else(|| m.get("brT"))
        .and_then(|v| v.as_f64())
        .unwrap_or(1.0);
    let i_pk = op
        .get("current_a_peak")
        .and_then(|v| v.as_f64())
        .unwrap_or(0.0);
    let n_rpm = op.get("speed_rpm").and_then(|v| v.as_f64()).unwrap_or(0.0);
    let gamma = op
        .get("gamma_deg")
        .and_then(|v| v.as_f64())
        .unwrap_or(0.0)
        .to_radians();

    let flux = br * rod * rod * length / poles.max(1.0);
    let ke = turns * poles * flux * 0.5;
    let omega = n_rpm * 2.0 * std::f64::consts::PI / 60.0;
    let back_emf = ke * omega;
    let torque = ke * i_pk * gamma.cos();
    let copper = 1.5 * (i_pk / 2.0f64.sqrt()).powi(2) * 0.05;
    let iron = 0.02 * n_rpm.abs() * br * br * length * 1000.0;
    let magnet_eddy = 0.005 * n_rpm.abs() * br * br;
    let ld = 1e-3 * turns * turns * length / poles.max(1.0);
    let lq = ld * 0.85;

    Ok(json!({
        "schema_version": req.get("schema_version").and_then(|v| v.as_str()).unwrap_or("0.0.0-gate0"),
        "meta": {
            "solver": "mock",
            "elapsed_ms": 0,
            "mock": true,
            "wasm": true,
            "note": "Wasm Gate0 radial PMSM mock — not for accuracy benchmarking"
        },
        "torque_nm": (torque * 1e6).round() / 1e6,
        "back_emf_v_peak": (back_emf * 1e6).round() / 1e6,
        "losses_w": {
            "copper": (copper * 1e6).round() / 1e6,
            "iron": (iron * 1e6).round() / 1e6,
            "magnet_eddy": (magnet_eddy * 1e6).round() / 1e6
        },
        "inductance_h": { "ld": ld, "lq": lq }
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pmsm_fixture_finite() {
        let req = r#"{
          "schema_version":"0.0.0-gate0","topology":"RF","machine_type":"PMSM",
          "geometry":{"poles":10,"slots":12,"stack_length_m":0.04,"airgap_m":0.0008,
            "rotor_od_m":0.06,"stator_id_m":0.0616,"magnet_thickness_m":0.003,"turns_per_phase":48},
          "materials":{"br_t":1.2},"operating_point":{"speed_rpm":3000,"current_a_peak":25,"gamma_deg":0}
        }"#;
        let out: Value = serde_json::from_str(&solve_json(req)).unwrap();
        assert_eq!(out["meta"]["solver"], "mec");
        assert_eq!(out["meta"]["mock"], false);
        assert!(out["torque_nm"].as_f64().unwrap().is_finite());
        assert!(out["torque_nm"].as_f64().unwrap().abs() > 0.0);
    }

    #[test]
    fn acim_fixture_finite() {
        let req = r#"{
          "schema_version":"0.0.0-gate0","topology":"RF","machine_type":"ACIM",
          "geometry":{"poles":4,"slots":36,"stack_length_m":0.12,"airgap_m":0.0005,
            "rotor_od_m":0.119,"stator_id_m":0.120,"turns_per_phase":96,"rotor_bars":28,"bar_area_m2":5e-5},
          "materials":{"sigma_copper":5.8e7,"sigma_bar":3.5e7},
          "operating_point":{"speed_rpm":1450,"voltage_v_peak":311.0,"freq_hz":50.0}
        }"#;
        let out: Value = serde_json::from_str(&solve_json(req)).unwrap();
        assert_eq!(out["meta"]["solver"], "acim_equiv");
        assert_eq!(out["meta"]["mock"], false);
        assert!(out["losses_w"]["rotor_bar"].as_f64().unwrap().is_finite());
    }

    #[test]
    fn bad_json_error_shape() {
        let out: Value = serde_json::from_str(&solve_json("{")).unwrap();
        assert!(out.get("error").is_some());
    }
}
