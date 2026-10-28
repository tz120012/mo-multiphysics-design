//! Radial SPM PMSM — simplified nonlinear series MEC (Wasm port of Python radial_mec intent).
//! Engineering first cut; not calibrated to ≤5%. Gold-standard remains Python.

use crate::materials::Resolved;
use serde_json::{json, Value};
use std::f64::consts::PI;

const MU0: f64 = 4.0e-7 * PI;
const MEC_TOL: f64 = 1e-4;
const MEC_MAX_ITER: usize = 80;

fn mu_r_steel(b: f64) -> f64 {
    let b = b.abs();
    let bs = 1.70;
    let mur0 = 5000.0;
    let x = b / bs;
    (1.0 + (mur0 - 1.0) / (1.0 + x.powi(8))).max(1.05)
}

struct Branch {
    name: &'static str,
    length: f64,
    area: f64,
    nonlinear: bool,
    mu: f64,
    r: f64,
    b: f64,
}

fn reluctance(len: f64, area: f64, mu: f64) -> f64 {
    len / (mu * area.max(1e-18))
}

fn solve_series(branches: &mut [Branch], mmf: f64) -> (f64, usize, bool, f64) {
    for b in branches.iter_mut() {
        if b.nonlinear {
            b.mu = MU0 * mu_r_steel(0.0);
        }
        b.r = reluctance(b.length, b.area, b.mu);
    }
    let any_nl = branches.iter().any(|b| b.nonlinear);
    let mut phi = 0.0;
    let mut converged = false;
    let mut it = 0usize;
    for i in 1..=MEC_MAX_ITER {
        it = i;
        for b in branches.iter_mut() {
            b.b = phi / b.area.max(1e-18);
            if b.nonlinear {
                b.mu = MU0 * mu_r_steel(b.b);
            }
            b.r = reluctance(b.length, b.area, b.mu);
        }
        let r_tot: f64 = branches.iter().map(|b| b.r).sum();
        let phi_new = mmf / r_tot;
        if !any_nl {
            phi = phi_new;
            converged = true;
            break;
        }
        let denom = phi_new.abs().max(1e-16);
        if (phi_new - phi).abs() / denom < MEC_TOL {
            phi = phi_new;
            for b in branches.iter_mut() {
                b.b = phi / b.area.max(1e-18);
                if b.nonlinear {
                    b.mu = MU0 * mu_r_steel(b.b);
                }
                b.r = reluctance(b.length, b.area, b.mu);
            }
            converged = true;
            break;
        }
        phi = 0.45 * phi_new + 0.55 * phi;
    }
    let r_tot: f64 = branches.iter().map(|b| b.r).sum();
    (phi, it, converged, r_tot)
}

fn fnum(obj: &Value, key: &str, default: f64) -> f64 {
    obj.get(key)
        .and_then(|v| v.as_f64().or_else(|| v.as_i64().map(|i| i as f64)))
        .unwrap_or(default)
}

pub fn solve_pmsm(req: &Value, mat: &Resolved, is_bldc: bool) -> Result<Value, String> {
    let g = req.get("geometry").ok_or("missing geometry")?;
    let op = req.get("operating_point").ok_or("missing operating_point")?;

    let poles = fnum(g, "poles", 10.0).max(2.0);
    let slots = fnum(g, "slots", 12.0).max(3.0);
    let length = fnum(g, "stack_length_m", 0.04);
    let airgap = fnum(g, "airgap_m", 0.0008);
    let rod = fnum(g, "rotor_od_m", 0.06);
    let sid = fnum(g, "stator_id_m", 0.0616);
    let hm = {
        let v = g.get("magnet_thickness_m").and_then(|x| x.as_f64());
        match v {
            Some(h) if h > 0.0 => h,
            _ => (3.0 * airgap).max(0.003),
        }
    };
    let turns = fnum(g, "turns_per_phase", 48.0).max(1.0);
    let kw = fnum(g, "winding_factor", 0.93);
    let kg = fnum(g, "carter_factor", 1.15);
    let alpha_m = fnum(g, "magnet_arc_ratio", 0.7);
    let g_eff = airgap * kg;
    let p = poles / 2.0;

    let tau_p = PI * sid / poles;
    let tau_s = PI * sid / slots;
    let w_m = alpha_m * tau_p;
    let a_pm = w_m * length;
    let a_g = w_m * length;
    let w_tooth = 0.5 * tau_s;
    let n_teeth = (slots / poles).max(0.5);
    let a_tooth = w_tooth * length * n_teeth;
    let ht = fnum(g, "tooth_height_m", (0.12 * sid).max(0.55 * tau_p));
    let hy_from = 0.85 * alpha_m * tau_p / 1.40;
    let hy_s = fnum(g, "stator_yoke_height_m", (0.06 * sid).max(hy_from));
    let hy_r = fnum(g, "rotor_yoke_height_m", (0.05 * sid).max(0.85 * hy_from));
    let d_sy = sid + 2.0 * ht + hy_s;
    let d_ry = (rod - 2.0 * hm - hy_r).max(0.25 * rod);
    let l_sy = PI * d_sy / poles;
    let l_ry = PI * d_ry / poles;
    let a_sy = hy_s * length;
    let a_ry = hy_r * length;

    let n_rpm = fnum(op, "speed_rpm", 0.0);
    let i_pk = fnum(op, "current_a_peak", 0.0);
    let gamma_deg = fnum(op, "gamma_deg", 0.0);
    let gamma = gamma_deg.to_radians();
    let mut iq = i_pk * gamma.cos();
    let id_ = -i_pk * gamma.sin();
    let mut notes = mat.notes.clone();
    if is_bldc {
        let k = 2.0 / 3.0f64.sqrt();
        iq *= k;
        notes.push(format!("BLDC torque coeff {k:.6} applied on Iq"));
    }

    let hc = mat.br_t / (MU0 * mat.mur_pm);
    let f_pm = hc * hm;
    let f_d = 1.5 * turns * kw * id_ / p.max(1.0);
    let f_net = f_pm + f_d;

    let mut branches = [
        Branch {
            name: "pm",
            length: hm,
            area: a_pm,
            nonlinear: false,
            mu: MU0 * mat.mur_pm,
            r: 0.0,
            b: 0.0,
        },
        Branch {
            name: "airgap",
            length: g_eff,
            area: a_g,
            nonlinear: false,
            mu: MU0,
            r: 0.0,
            b: 0.0,
        },
        Branch {
            name: "stator_tooth",
            length: ht,
            area: a_tooth,
            nonlinear: true,
            mu: MU0,
            r: 0.0,
            b: 0.0,
        },
        Branch {
            name: "stator_yoke",
            length: l_sy,
            area: a_sy,
            nonlinear: true,
            mu: MU0,
            r: 0.0,
            b: 0.0,
        },
        Branch {
            name: "rotor_yoke",
            length: l_ry,
            area: a_ry,
            nonlinear: true,
            mu: MU0,
            r: 0.0,
            b: 0.0,
        },
    ];
    let (phi, iters, converged, r_tot) = solve_series(&mut branches, f_net);
    let b_g = branches[1].b;
    let b_tooth = branches[2].b;
    let psi_pm = kw * turns * phi.abs();
    let omega_m = n_rpm * 2.0 * PI / 60.0;
    let omega_e = p * omega_m;
    let back_emf = omega_e * psi_pm;
    let torque = 1.5 * p * psi_pm * iq;

    // Copper: crude R_ph
    let end = PI * tau_s * 1.5;
    let mlt = 2.0 * (length + end);
    let a_cond = (1.5e-6_f64).max(0.15 * a_tooth / (turns / n_teeth).max(1.0));
    let r_ph = turns * mlt / (mat.sigma_copper * a_cond);
    let i_rms = i_pk / 2.0f64.sqrt();
    let copper = 1.5 * i_rms * i_rms * r_ph;

    let f_hz = n_rpm.abs() * p / 60.0;
    let v_tooth = a_tooth * ht * poles;
    let v_yoke = (a_sy * l_sy + a_ry * l_ry) * poles;
    let b_y = 0.5 * (branches[3].b.abs() + branches[4].b.abs());
    let iron = {
        let kh = 150.0;
        let alpha = 1.8;
        let ke = 0.8;
        let pwr = |b: f64| kh * f_hz.abs() * b.abs().powf(alpha) + ke * (f_hz * b).powi(2);
        pwr(b_tooth) * v_tooth.max(0.0) + pwr(b_y) * v_yoke.max(0.0)
    };
    let v_pm = a_pm * hm * poles;
    let magnet_eddy = 0.02 * b_g.powi(2) * f_hz.powi(2) * v_pm;

    // Ld/Lq incremental
    let di = (0.05 * i_pk.abs().max(1.0)).max(0.1);
    let psi_at = |id_v: f64, iq_v: f64| {
        let fd = 1.5 * turns * kw * id_v / p.max(1.0);
        let mut br = [
            Branch {
                name: "pm",
                length: hm,
                area: a_pm,
                nonlinear: false,
                mu: MU0 * mat.mur_pm,
                r: 0.0,
                b: 0.0,
            },
            Branch {
                name: "airgap",
                length: g_eff,
                area: a_g,
                nonlinear: false,
                mu: MU0,
                r: 0.0,
                b: 0.0,
            },
            Branch {
                name: "stator_tooth",
                length: ht,
                area: a_tooth,
                nonlinear: true,
                mu: MU0,
                r: 0.0,
                b: 0.0,
            },
            Branch {
                name: "stator_yoke",
                length: l_sy,
                area: a_sy,
                nonlinear: true,
                mu: MU0,
                r: 0.0,
                b: 0.0,
            },
            Branch {
                name: "rotor_yoke",
                length: l_ry,
                area: a_ry,
                nonlinear: true,
                mu: MU0,
                r: 0.0,
                b: 0.0,
            },
        ];
        let (phid, _, _, _) = solve_series(&mut br, f_pm + fd);
        let fq = 1.5 * turns * kw * iq_v / p.max(1.0);
        let mut brq = br;
        let (phiq, _, _, _) = solve_series(&mut brq, fq);
        (kw * turns * phid, kw * turns * phiq)
    };
    let iq_l = if is_bldc { i_pk * gamma.cos() } else { iq };
    let (psi_d0, psi_q0) = psi_at(id_, iq_l);
    let (psi_d1, _) = psi_at(id_ + di, iq_l);
    let (_, psi_q1) = psi_at(id_, iq_l + di);
    let ld = ((psi_d1 - psi_d0) / di).abs();
    let lq = ((psi_q1 - psi_q0) / di).abs();

    let mut note = String::from(
        "Wasm radial SPM PMSM MEC v0 (series one-pole, analytic μ(B)). Engineering first cut — not ≤5%. Gold: Python packages/solver-analytic.",
    );
    if !notes.is_empty() {
        note.push_str(" Defaults: ");
        note.push_str(&notes.join("; "));
    }
    if is_bldc {
        note.push_str(" [BLDC approx path]");
    }

    Ok(json!({
        "schema_version": req.get("schema_version").and_then(|v| v.as_str()).unwrap_or("0.0.0-gate0"),
        "meta": {
            "solver": "mec",
            "elapsed_ms": 0,
            "mock": false,
            "note": note,
            "wasm": true,
            "mec": {
                "converged": converged,
                "iterations": iters,
                "tol": MEC_TOL,
                "max_iter": MEC_MAX_ITER,
                "flux_pole_wb": phi,
                "B_airgap_t": b_g,
                "B_tooth_t": b_tooth,
                "R_total": r_tot,
                "F_pm_a": f_pm,
                "F_net_a": f_net,
                "psi_pm_wb": psi_pm,
            },
            "bldc_approx": is_bldc,
        },
        "torque_nm": torque,
        "back_emf_v_peak": back_emf,
        "losses_w": {
            "copper": copper.max(0.0),
            "iron": iron.max(0.0),
            "magnet_eddy": magnet_eddy.max(0.0),
        },
        "inductance_h": { "ld": ld, "lq": lq }
    }))
}
