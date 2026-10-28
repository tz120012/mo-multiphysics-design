//! ACIM single-cage steady T-equivalent (Wasm). Aligns with Python machines/acim_equiv.py intent.

use crate::materials::Resolved;
use serde_json::{json, Value};
use std::f64::consts::PI;

const MU0: f64 = 4.0e-7 * PI;

fn fnum(obj: &Value, key: &str, default: f64) -> f64 {
    obj.get(key)
        .and_then(|v| v.as_f64().or_else(|| v.as_i64().map(|i| i as f64)))
        .unwrap_or(default)
}

fn parallel(z1: (f64, f64), z2: (f64, f64)) -> (f64, f64) {
    // 1/z = 1/z1 + 1/z2
    let (a, b) = z1;
    let (c, d) = z2;
    let den_re = a + c;
    let den_im = b + d;
    let n_re = a * c - b * d;
    let n_im = a * d + b * c;
    let dd = den_re * den_re + den_im * den_im;
    if dd < 1e-60 {
        return (1e30, 0.0);
    }
    (n_re / dd, n_im / dd)
}

pub fn solve_acim(req: &Value, mat: &Resolved) -> Result<Value, String> {
    let g = req.get("geometry").ok_or("missing geometry")?;
    let op = req.get("operating_point").ok_or("missing operating_point")?;

    let poles = fnum(g, "poles", 4.0).max(2.0);
    let slots = fnum(g, "slots", 36.0).max(3.0);
    let length = fnum(g, "stack_length_m", 0.12);
    let airgap = fnum(g, "airgap_m", 0.0005);
    let rod = fnum(g, "rotor_od_m", 0.119);
    let sid = fnum(g, "stator_id_m", 0.120);
    let turns = fnum(g, "turns_per_phase", 72.0).max(1.0);
    let kw = fnum(g, "winding_factor", 0.90);
    let kg = fnum(g, "carter_factor", 1.2);
    let g_eff = airgap * kg;
    let p = poles / 2.0;
    let m_ph = 3.0;

    let d = 0.5 * (rod + sid);
    let tau_p = PI * d / poles;
    let tau_s = PI * sid / slots;

    let lm = (MU0 * m_ph * (kw * turns).powi(2) * tau_p * length) / (PI * p * g_eff);
    let lm = lm.max(1e-4);
    let l_sigma_s = fnum(g, "leakage_frac_stator", 0.04) * lm;
    let l_sigma_r = fnum(g, "leakage_frac_rotor", 0.05) * lm;

    let end = PI * tau_s * 1.5;
    let mlt = 2.0 * (length + end);
    let a_cond = fnum(
        g,
        "conductor_area_m2",
        (1.0e-6_f64).max(0.12 * (0.45 * tau_s) * (0.12 * sid).max(0.01) / (turns / (slots / 3.0).max(1.0)).max(1.0)),
    );
    let rs = turns * mlt / (mat.sigma_copper * a_cond);

    let n_bars = fnum(g, "rotor_bars", slots);
    let a_bar = fnum(g, "bar_area_m2", (2.0e-5_f64).max(0.08 * tau_s * (0.1 * sid).max(0.008)));
    let r_bar = 1.3 * length / (mat.sigma_bar * a_bar);
    let turns_ratio_sq = (kw * turns).powi(2) * (m_ph / n_bars.max(1.0));
    let mut rr = r_bar * turns_ratio_sq;
    let mut notes = mat.notes.clone();
    if rr < 0.05 * rs {
        rr = 0.3 * rs;
        notes.push("Rr' floored to 0.3*Rs".into());
    }
    if rr > 5.0 * rs {
        rr = 2.0 * rs;
        notes.push("Rr' capped at 2*Rs".into());
    }

    let n_rpm = fnum(op, "speed_rpm", 0.0);
    let f_hz = if let Some(f) = op.get("freq_hz").and_then(|v| v.as_f64()) {
        f
    } else if let Some(s0) = op.get("slip").and_then(|v| v.as_f64()) {
        if (1.0 - s0).abs() > 1e-6 && n_rpm.abs() > 1e-6 {
            let f = n_rpm.abs() * p / (60.0 * (1.0 - s0));
            notes.push(format!("freq_hz derived → {f:.4} Hz"));
            f
        } else {
            notes.push("freq_hz defaulted to 50 Hz".into());
            50.0
        }
    } else {
        notes.push("freq_hz defaulted to 50 Hz".into());
        50.0
    };
    let n_sync = f_hz.abs() * 60.0 / p.max(1e-12);
    let slip = if let Some(s) = op.get("slip").and_then(|v| v.as_f64()) {
        s
    } else {
        let s = if n_sync < 1e-9 {
            1.0
        } else {
            (n_sync - n_rpm) / n_sync
        };
        notes.push(format!("slip computed = {s:.6}"));
        s
    };

    let v_peak = if let Some(v) = op.get("voltage_v_peak").and_then(|x| x.as_f64()) {
        v
    } else if let Some(i_pk) = op.get("current_a_peak").and_then(|x| x.as_f64()) {
        let omega = 2.0 * PI * f_hz.abs();
        let s_u = if slip.abs() < 1e-8 { 1e-8 } else { slip };
        let z1 = (rs, omega * l_sigma_s);
        let zm = (0.0, omega * lm);
        let z2 = (rr / s_u, omega * l_sigma_r);
        let zf = parallel(zm, z2);
        let zin = (z1.0 + zf.0, z1.1 + zf.1);
        let zin_mag = (zin.0 * zin.0 + zin.1 * zin.1).sqrt();
        let v = (i_pk / 2.0f64.sqrt()) * zin_mag * 2.0f64.sqrt();
        notes.push(format!("voltage_v_peak inferred → {v:.4} V"));
        v
    } else {
        return Err(
            "ACIM needs operating_point.voltage_v_peak (preferred) or current_a_peak".into(),
        );
    };

    let s = if slip.abs() < 1e-8 { 1e-8 } else { slip };
    let omega = 2.0 * PI * f_hz.abs();
    let xs = omega * l_sigma_s;
    let xr = omega * l_sigma_r;
    let xm = omega * lm;
    let z1 = (rs, xs);
    let zm = (0.0, xm);
    let z2 = (rr / s, xr);
    let zf = parallel(zm, z2);
    let zin = (z1.0 + zf.0, z1.1 + zf.1);
    let v_rms = v_peak.abs() / 2.0f64.sqrt();
    let zin_mag2 = zin.0 * zin.0 + zin.1 * zin.1;
    let i1_re = v_rms * zin.0 / zin_mag2;
    let i1_im = -v_rms * zin.1 / zin_mag2;
    // I2 = I1 * Zm / (Zm+Z2)
    let den = (zm.0 + z2.0, zm.1 + z2.1);
    let num = (i1_re * zm.0 - i1_im * zm.1, i1_re * zm.1 + i1_im * zm.0);
    let dd = den.0 * den.0 + den.1 * den.1;
    let i2_re = (num.0 * den.0 + num.1 * den.1) / dd;
    let i2_im = (num.1 * den.0 - num.0 * den.1) / dd;
    let i1_rms = (i1_re * i1_re + i1_im * i1_im).sqrt();
    let i2_rms = (i2_re * i2_re + i2_im * i2_im).sqrt();

    let p_cu_s = 3.0 * i1_rms * i1_rms * rs;
    let p_cu_r = 3.0 * i2_rms * i2_rms * rr;
    let p_ag = 3.0 * i2_rms * i2_rms * (rr / s);
    let p_mech = (1.0 - s) * p_ag;
    let omega_sync = n_sync * 2.0 * PI / 60.0;
    let torque = if omega_sync > 1e-12 {
        p_ag / omega_sync
    } else {
        0.0
    };
    let p_in = 3.0 * v_rms * i1_re;
    let s_app = 3.0 * v_rms * i1_rms;
    let pf = if s_app > 1e-18 { p_in / s_app } else { 0.0 };
    let e_ag = {
        let e_re = i1_re * zf.0 - i1_im * zf.1;
        let e_im = i1_re * zf.1 + i1_im * zf.0;
        (e_re * e_re + e_im * e_im).sqrt()
    };
    let e_ag_peak = e_ag * 2.0f64.sqrt();

    // Coarse iron
    let a = tau_p * length * 0.7;
    let denom = 4.44 * f_hz.abs().max(1e-3) * kw * turns * a.max(1e-8);
    let mut b = (e_ag_peak / 2.0f64.sqrt()) / denom;
    b = b.abs().min(1.8);
    let v_iron = PI * d * length * (0.15 * d).max(0.01);
    let iron = (150.0 * f_hz.abs() * b.powf(1.8) + 0.8 * (f_hz * b).powi(2)) * v_iron;

    let mut note = String::from(
        "Wasm ACIM single-cage steady T-model v0. Engineering first cut — not ≤5%. Gold: Python machines/acim_equiv.py.",
    );
    if !notes.is_empty() {
        note.push_str(" Defaults: ");
        note.push_str(&notes.join("; "));
    }

    Ok(json!({
        "schema_version": req.get("schema_version").and_then(|v| v.as_str()).unwrap_or("0.0.0-gate0"),
        "meta": {
            "solver": "acim_equiv",
            "elapsed_ms": 0,
            "mock": false,
            "note": note,
            "wasm": true,
            "acim": {
                "slip": s,
                "freq_hz": f_hz,
                "n_sync_rpm": n_sync,
                "I1_rms": i1_rms,
                "I2_rms": i2_rms,
                "pf": pf,
                "P_in_w": p_in,
                "P_mech_w": p_mech,
                "Rs": rs,
                "Rr_p": rr,
                "Xm": xm,
                "Xsigma_s": xs,
                "Xsigma_r": xr,
            }
        },
        "torque_nm": torque,
        "back_emf_v_peak": e_ag_peak,
        "losses_w": {
            "copper": p_cu_s.max(0.0),
            "iron": iron.max(0.0),
            "rotor_bar": p_cu_r.max(0.0),
        }
    }))
}
