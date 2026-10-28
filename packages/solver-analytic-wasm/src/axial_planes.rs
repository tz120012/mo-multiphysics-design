//! AF + PMSM axial multi-plane unfold (Wasm stub port of Python axial_planes).
//! Same SolveRequest/Result contract; meta.solver=axial_planes; meta.wasm=true.
//! Engineering first cut — not calibrated to ≤5%. Gold: Python packages/solver-analytic.

use crate::materials::Resolved;
use serde_json::{json, Value};
use std::f64::consts::PI;

const MU0: f64 = 4.0e-7 * PI;
const MEC_TOL: f64 = 1e-4;
const MEC_MAX_ITER: usize = 80;
const DEFAULT_N_PLANES: usize = 4;

fn mu_r_steel(b: f64) -> f64 {
    let b = b.abs();
    let bs = 1.70;
    let mur0 = 5000.0;
    let x = b / bs;
    (1.0 + (mur0 - 1.0) / (1.0 + x.powi(8))).max(1.05)
}

struct Branch {
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

fn solve_series(branches: &mut [Branch], mmf: f64) -> (f64, usize, bool) {
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
    (phi, it, converged)
}

fn fnum(obj: &Value, key: &str, default: f64) -> f64 {
    obj.get(key)
        .and_then(|v| v.as_f64().or_else(|| v.as_i64().map(|i| i as f64)))
        .unwrap_or(default)
}

fn fnum_opt(obj: &Value, key: &str) -> Option<f64> {
    obj.get(key)
        .and_then(|v| {
            if v.is_null() {
                None
            } else {
                v.as_f64().or_else(|| v.as_i64().map(|i| i as f64))
            }
        })
}

struct Plane {
    r_mean_m: f64,
    dr_m: f64,
    a_pm: f64,
    a_g: f64,
    a_tooth: f64,
    a_sy: f64,
    a_ry: f64,
    hm: f64,
    g_eff: f64,
    l_tooth: f64,
    l_sy: f64,
    l_ry: f64,
    n_teeth: f64,
}

struct Common {
    poles: f64,
    pole_pairs: f64,
    inner_r: f64,
    outer_r: f64,
    disk_t: f64,
    disk_count: f64,
    turns: f64,
    kw: f64,
    hm: f64,
    n_planes: usize,
    r_mean_ann: f64,
}

fn resolve_annulus(g: &Value, notes: &mut Vec<String>) -> Result<(f64, f64), String> {
    if fnum_opt(g, "inner_radius_m").is_some() && fnum_opt(g, "outer_radius_m").is_some() {
        let ri = fnum(g, "inner_radius_m", 0.0);
        let ro = fnum(g, "outer_radius_m", 0.0);
        notes.push("annulus from inner_radius_m / outer_radius_m".into());
        if ri <= 0.0 || ro <= ri {
            return Err(format!("invalid AF annulus: inner_r={ri}, outer_r={ro}"));
        }
        return Ok((ri, ro));
    }
    if fnum_opt(g, "rotor_id_m").is_some() && fnum_opt(g, "rotor_od_m").is_some() {
        let ri = fnum(g, "rotor_id_m", 0.0) / 2.0;
        let ro = fnum(g, "rotor_od_m", 0.0) / 2.0;
        notes.push("annulus from rotor_id_m / rotor_od_m (diameters→radii)".into());
        if ri <= 0.0 || ro <= ri {
            return Err(format!("invalid AF annulus: inner_r={ri}, outer_r={ro}"));
        }
        return Ok((ri, ro));
    }
    if g.get("rotor_od_m").is_none() || g.get("stator_id_m").is_none() {
        return Err(
            "AF geometry needs outer/inner radii: outer_radius_m+inner_radius_m, \
             rotor_od_m+rotor_id_m, or rotor_od_m+stator_id_m (stub mapping)"
                .into(),
        );
    }
    let ro = fnum(g, "rotor_od_m", 0.0) / 2.0;
    let ri = fnum(g, "stator_id_m", 0.0) / 2.0;
    notes.push(
        "annulus from rotor_od_m (outer Ø) / stator_id_m (inner Ø) — AF stub mapping".into(),
    );
    if ri <= 0.0 || ro <= ri {
        return Err(format!("invalid AF annulus: inner_r={ri}, outer_r={ro}"));
    }
    Ok((ri, ro))
}

fn derive_planes(g: &Value, notes: &mut Vec<String>) -> Result<(Common, Vec<Plane>), String> {
    let poles = fnum(g, "poles", 10.0).max(2.0);
    let slots = {
        let s = fnum_opt(g, "slots").unwrap_or(0.0);
        if s < 3.0 {
            let d = (poles + 2.0).max(3.0);
            notes.push(format!("slots defaulted to {d}"));
            d
        } else {
            s
        }
    };
    let airgap = fnum(g, "airgap_m", 0.001);
    let (ri, ro) = resolve_annulus(g, notes)?;

    let n_planes = {
        let raw = fnum_opt(g, "n_planes").map(|v| v as usize).unwrap_or(DEFAULT_N_PLANES);
        let n = raw.max(1);
        if g.get("n_planes").is_none() {
            notes.push(format!("n_planes defaulted to {n}"));
        }
        n
    };

    let hm = match fnum_opt(g, "magnet_thickness_m") {
        Some(h) if h > 0.0 => h,
        Some(_) => {
            let h = (3.0 * airgap).max(0.003);
            notes.push(format!("magnet_thickness_m non-positive; using {h:.4} m"));
            h
        }
        None => {
            let h = (3.0 * airgap).max(0.003);
            notes.push(format!("magnet_thickness_m defaulted to {h:.4} m"));
            h
        }
    };

    let disk_t = if let Some(d) = fnum_opt(g, "disk_thickness_m") {
        d
    } else if let Some(s) = fnum_opt(g, "stack_length_m") {
        notes.push("disk_thickness_m taken from stack_length_m (AF axial thickness)".into());
        s
    } else {
        let d = (2.0 * hm).max(0.006);
        notes.push(format!("disk_thickness_m defaulted to {d:.4} m"));
        d
    };

    let turns = match fnum_opt(g, "turns_per_phase") {
        Some(t) => t.max(1.0),
        None => {
            notes.push("turns_per_phase defaulted to 36".into());
            36.0
        }
    };

    let alpha_m = fnum(g, "magnet_arc_ratio", 0.7);
    if g.get("magnet_arc_ratio").is_none() {
        notes.push("magnet_arc_ratio defaulted to 0.7".into());
    }
    let kg = fnum(g, "carter_factor", 1.15);
    if g.get("carter_factor").is_none() {
        notes.push("carter_factor defaulted to 1.15".into());
    }
    let g_eff = airgap * kg;
    let kw = fnum(g, "winding_factor", 0.93);
    if g.get("winding_factor").is_none() {
        notes.push("winding_factor defaulted to 0.93".into());
    }

    let ht = match fnum_opt(g, "tooth_height_m") {
        Some(h) if h > 0.0 => h,
        _ => {
            let h = (0.35 * disk_t).max(0.002);
            notes.push(format!("tooth_height_m (axial) estimated as {h:.4} m"));
            h
        }
    };

    let r_mean_ann = 0.5 * (ri + ro);
    let tau_p_mean = 2.0 * PI * r_mean_ann / poles;
    let hy_from = 0.85 * alpha_m * tau_p_mean / 1.40;

    let hy_s = match fnum_opt(g, "stator_yoke_height_m") {
        Some(h) if h > 0.0 => h,
        _ => {
            let h = (0.25 * disk_t).max(0.5 * hy_from).max(0.002);
            notes.push(format!("stator_yoke_height_m (axial) estimated as {h:.4} m"));
            h
        }
    };
    let hy_r = match fnum_opt(g, "rotor_yoke_height_m") {
        Some(h) if h > 0.0 => h,
        _ => {
            let h = (0.2 * disk_t).max(0.45 * hy_from).max(0.002);
            notes.push(format!("rotor_yoke_height_m (axial) estimated as {h:.4} m"));
            h
        }
    };

    let disk_count = fnum(g, "disk_count", 1.0).max(1.0);
    if g.get("disk_count").is_none() {
        notes.push("disk_count defaulted to 1 (single airgap equivalent)".into());
    }

    let dr = (ro - ri) / n_planes as f64;
    let mut planes = Vec::with_capacity(n_planes);
    for i in 0..n_planes {
        let r_in = ri + i as f64 * dr;
        let r_out = r_in + dr;
        let r_m = 0.5 * (r_in + r_out);
        let tau_p = 2.0 * PI * r_m / poles;
        let tau_s = 2.0 * PI * r_m / slots;
        let w_m = alpha_m * tau_p;
        let a_pm = w_m * dr;
        let a_g = a_pm;
        let w_tooth = 0.5 * tau_s;
        let n_teeth = (slots / poles).max(0.5);
        let a_tooth = w_tooth * dr * n_teeth;
        let l_sy = PI * r_m / poles;
        let l_ry = l_sy;
        planes.push(Plane {
            r_mean_m: r_m,
            dr_m: dr,
            a_pm,
            a_g,
            a_tooth,
            a_sy: hy_s * dr,
            a_ry: hy_r * dr,
            hm,
            g_eff,
            l_tooth: ht,
            l_sy,
            l_ry,
            n_teeth,
        });
    }

    Ok((
        Common {
            poles,
            pole_pairs: poles / 2.0,
            inner_r: ri,
            outer_r: ro,
            disk_t,
            disk_count,
            turns,
            kw,
            hm,
            n_planes,
            r_mean_ann,
        },
        planes,
    ))
}

fn build_branches(pl: &Plane, mur_pm: f64) -> [Branch; 5] {
    [
        Branch {
            length: pl.hm,
            area: pl.a_pm,
            nonlinear: false,
            mu: MU0 * mur_pm,
            r: 0.0,
            b: 0.0,
        },
        Branch {
            length: pl.g_eff,
            area: pl.a_g,
            nonlinear: false,
            mu: MU0,
            r: 0.0,
            b: 0.0,
        },
        Branch {
            length: pl.l_tooth,
            area: pl.a_tooth,
            nonlinear: true,
            mu: MU0,
            r: 0.0,
            b: 0.0,
        },
        Branch {
            length: pl.l_sy,
            area: pl.a_sy,
            nonlinear: true,
            mu: MU0,
            r: 0.0,
            b: 0.0,
        },
        Branch {
            length: pl.l_ry,
            area: pl.a_ry,
            nonlinear: true,
            mu: MU0,
            r: 0.0,
            b: 0.0,
        },
    ]
}

struct PlaneSol {
    flux_wb: f64,
    b_g: f64,
    b_tooth: f64,
    b_sy: f64,
    b_ry: f64,
    converged: bool,
    iterations: usize,
}

fn solve_planes_flux(planes: &[Plane], mmf: f64, mur_pm: f64) -> (Vec<PlaneSol>, f64) {
    let mut sols = Vec::with_capacity(planes.len());
    let mut phi_sum = 0.0;
    for pl in planes {
        let mut br = build_branches(pl, mur_pm);
        let (phi, it, conv) = solve_series(&mut br, mmf);
        phi_sum += phi;
        sols.push(PlaneSol {
            flux_wb: phi,
            b_g: br[1].b,
            b_tooth: br[2].b,
            b_sy: br[3].b,
            b_ry: br[4].b,
            converged: conv,
            iterations: it,
        });
    }
    (sols, phi_sum)
}

pub fn solve_axial_pmsm(req: &Value, mat: &Resolved) -> Result<Value, String> {
    let g = req.get("geometry").ok_or("missing geometry")?;
    let op = req.get("operating_point").ok_or("missing operating_point")?;

    let mut notes = mat.notes.clone();
    let (common, planes) = derive_planes(g, &mut notes)?;

    let n_rpm = fnum(op, "speed_rpm", 0.0);
    let i_pk = fnum(op, "current_a_peak", 0.0);
    let gamma = fnum(op, "gamma_deg", 0.0).to_radians();
    let iq = i_pk * gamma.cos();
    let id_ = -i_pk * gamma.sin();

    let p = common.pole_pairs;
    let kw = common.kw;
    let nph = common.turns;
    let n_pl = common.n_planes;

    let hc = mat.br_t / (MU0 * mat.mur_pm);
    let f_pm = hc * common.hm;
    let f_d = 1.5 * nph * kw * id_ / p.max(1.0);
    let f_net = f_pm + f_d;

    let (sols, phi_sum) = solve_planes_flux(&planes, f_net, mat.mur_pm);
    let psi_pm = kw * nph * phi_sum.abs();

    let a_g_tot: f64 = planes.iter().map(|pl| pl.a_g).sum::<f64>().max(1e-18);
    let a_tooth_tot: f64 = planes.iter().map(|pl| pl.a_tooth).sum::<f64>().max(1e-18);
    let a_sy_tot: f64 = planes.iter().map(|pl| pl.a_sy).sum::<f64>().max(1e-18);
    let a_ry_tot: f64 = planes.iter().map(|pl| pl.a_ry).sum::<f64>().max(1e-18);

    let b_g_mean = sols
        .iter()
        .zip(planes.iter())
        .map(|(s, pl)| s.b_g * pl.a_g)
        .sum::<f64>()
        / a_g_tot;
    let b_tooth_mean = sols
        .iter()
        .zip(planes.iter())
        .map(|(s, pl)| s.b_tooth * pl.a_tooth)
        .sum::<f64>()
        / a_tooth_tot;
    let b_sy_mean = sols
        .iter()
        .zip(planes.iter())
        .map(|(s, pl)| s.b_sy * pl.a_sy)
        .sum::<f64>()
        / a_sy_tot;
    let b_ry_mean = sols
        .iter()
        .zip(planes.iter())
        .map(|(s, pl)| s.b_ry * pl.a_ry)
        .sum::<f64>()
        / a_ry_tot;

    let omega_m = n_rpm * 2.0 * PI / 60.0;
    let omega_e = p * omega_m;
    let back_emf = omega_e * psi_pm;
    let torque = 1.5 * p * psi_pm * iq;

    if common.disk_count > 1.0 {
        notes.push(format!(
            "disk_count={} recorded; torque uses single-airgap equivalent \
             (multi-disk series/parallel not expanded)",
            common.disk_count as i64
        ));
    }

    let di = (0.05 * i_pk.abs().max(1.0)).max(0.1);
    let psi_for = |id_v: f64, iq_v: f64| -> (f64, f64) {
        let fd = 1.5 * nph * kw * id_v / p.max(1.0);
        let (_, phi_d) = solve_planes_flux(&planes, f_pm + fd, mat.mur_pm);
        let fq = 1.5 * nph * kw * iq_v / p.max(1.0);
        let (_, phi_q) = solve_planes_flux(&planes, fq, mat.mur_pm);
        (kw * nph * phi_d, kw * nph * phi_q)
    };
    let (psi_d0, psi_q0) = psi_for(id_, iq);
    let (psi_d1, _) = psi_for(id_ + di, iq);
    let (_, psi_q1) = psi_for(id_, iq + di);
    let ld = ((psi_d1 - psi_d0) / di).abs();
    let lq = ((psi_q1 - psi_q0) / di).abs();

    // Copper
    let radial_span = common.outer_r - common.inner_r;
    let tau_p = 2.0 * PI * common.r_mean_ann / common.poles;
    let mlt = 2.0 * radial_span + 1.5 * PI * tau_p + 2.0 * common.disk_t;
    let mid = &planes[n_pl / 2];
    let a_cond = (1.5e-6_f64).max(0.12 * mid.a_tooth / (nph / mid.n_teeth).max(1.0));
    let r_ph = nph * mlt / (mat.sigma_copper * a_cond);
    let i_rms = i_pk / 2.0f64.sqrt();
    let copper = 1.5 * i_rms * i_rms * r_ph;

    let f_hz = n_rpm.abs() * p / 60.0;
    let mut v_tooth = 0.0;
    let mut v_yoke = 0.0;
    for pl in &planes {
        v_tooth += pl.a_tooth * pl.l_tooth * common.poles;
        v_yoke += pl.a_sy * pl.l_sy * common.poles;
        v_yoke += pl.a_ry * pl.l_ry * common.poles;
    }
    let b_yoke_mean = 0.5 * (b_sy_mean.abs() + b_ry_mean.abs());
    let iron = {
        let kh = 150.0;
        let alpha = 1.8;
        let ke = 0.8;
        let pwr = |b: f64| kh * f_hz.abs() * b.abs().powf(alpha) + ke * (f_hz * b).powi(2);
        pwr(b_tooth_mean) * v_tooth.max(0.0) + pwr(b_yoke_mean) * v_yoke.max(0.0)
    };
    let v_pm: f64 = planes.iter().map(|pl| pl.a_pm * pl.hm).sum::<f64>() * common.poles;
    let magnet_eddy = 0.02 * b_g_mean.powi(2) * f_hz.powi(2) * v_pm;

    let mut all_converged = true;
    let mut max_iters = 0usize;
    let mut plane_meta = Vec::with_capacity(n_pl);
    for (i, (pl, sol)) in planes.iter().zip(sols.iter()).enumerate() {
        all_converged = all_converged && sol.converged;
        max_iters = max_iters.max(sol.iterations);
        plane_meta.push(json!({
            "index": i,
            "r_mean_m": pl.r_mean_m,
            "dr_m": pl.dr_m,
            "flux_pole_wb": sol.flux_wb,
            "B_airgap_t": sol.b_g,
            "converged": sol.converged,
            "iterations": sol.iterations,
        }));
    }

    let mut note = String::from(
        "Wasm AF PMSM axial multi-plane stub v0 (concentric rings + series MEC per plane). \
         Engineering first cut — not calibrated to ≤5%. Gold: Python packages/solver-analytic/axial_planes \
         (wasm stub vs python golden).",
    );
    if !notes.is_empty() {
        note.push_str(" Defaults: ");
        note.push_str(&notes.join("; "));
    }

    Ok(json!({
        "schema_version": req.get("schema_version").and_then(|v| v.as_str()).unwrap_or("0.0.0-gate0"),
        "meta": {
            "solver": "axial_planes",
            "elapsed_ms": 0,
            "mock": false,
            "wasm": true,
            "n_planes": n_pl,
            "note": note,
            "axial": {
                "inner_radius_m": common.inner_r,
                "outer_radius_m": common.outer_r,
                "disk_thickness_m": common.disk_t,
                "disk_count": common.disk_count as i64,
                "flux_pole_sum_wb": phi_sum,
                "B_airgap_mean_t": b_g_mean,
                "B_tooth_mean_t": b_tooth_mean,
                "B_stator_yoke_mean_t": b_sy_mean,
                "B_rotor_yoke_mean_t": b_ry_mean,
                "F_pm_a": f_pm,
                "F_net_a": f_net,
                "psi_pm_wb": psi_pm,
                "converged": all_converged,
                "max_iterations": max_iters,
                "tol": MEC_TOL,
                "planes": plane_meta,
            },
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
