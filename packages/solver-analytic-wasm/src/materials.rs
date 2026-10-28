//! Resolve materials: inline → curves → meta → default (bfd27ab).

use serde_json::Value;

pub struct Resolved {
    pub br_t: f64,
    pub mur_pm: f64,
    pub sigma_copper: f64,
    pub sigma_bar: f64,
    pub notes: Vec<String>,
}

const DEFAULT_BR: f64 = 1.2;
const DEFAULT_MUR: f64 = 1.05;
const DEFAULT_SIG_CU: f64 = 5.8e7;
const DEFAULT_SIG_BAR: f64 = 3.5e7;

fn item_of<'a>(catalog: &'a Value, id: Option<&str>) -> Option<&'a Value> {
    let id = id?;
    match catalog {
        Value::Object(map) => {
            if let Some(v) = map.get(id) {
                return Some(v);
            }
            // wrapper {items:[...]}
            if let Some(Value::Array(arr)) = map.get("items") {
                return arr
                    .iter()
                    .find(|x| x.get("id").and_then(|v| v.as_str()) == Some(id));
            }
            None
        }
        Value::Array(arr) => arr
            .iter()
            .find(|x| x.get("id").and_then(|v| v.as_str()) == Some(id)),
        _ => None,
    }
}

fn meta_of<'a>(item: &'a Value) -> Option<&'a Value> {
    item.get("meta")
}

fn curves_bucket<'a>(item: &'a Value, category: &str) -> Option<&'a Value> {
    let c = item.get("curves")?;
    c.get(category).or(Some(c))
}

fn num(v: Option<&Value>) -> Option<f64> {
    v.and_then(|x| x.as_f64().or_else(|| x.as_i64().map(|i| i as f64)))
}

fn pick(cands: &[Option<f64>], default: f64) -> (f64, bool) {
    for c in cands {
        if let Some(v) = c {
            return (*v, true);
        }
    }
    (default, false)
}

pub fn resolve(materials: &Value, catalog: Option<&Value>, need_magnet: bool, need_bar: bool) -> Resolved {
    let mats = materials.as_object();
    let get = |k: &str| mats.and_then(|m| m.get(k)).and_then(|v| num(Some(v)));
    let get_str = |k: &str| mats.and_then(|m| m.get(k)).and_then(|v| v.as_str());

    let magnet_id = get_str("magnet_id");
    let coil_id = get_str("conductor_id").or_else(|| get_str("coil_id"));
    let bar_id = get_str("bar_id").or_else(|| get_str("rotor_bar_id"));

    let magnet_item = catalog.and_then(|c| item_of(c, magnet_id));
    let coil_item = catalog.and_then(|c| item_of(c, coil_id));
    let bar_item = catalog.and_then(|c| item_of(c, bar_id));

    let magnet_c = magnet_item.and_then(|i| curves_bucket(i, "magnet"));
    let coil_c = coil_item.and_then(|i| curves_bucket(i, "coil"));
    let bar_c = bar_item.and_then(|i| curves_bucket(i, "acim_bar"));

    let magnet_m = magnet_item.and_then(meta_of);
    let coil_m = coil_item.and_then(meta_of);
    let bar_m = bar_item.and_then(meta_of);

    let mut notes = Vec::new();

    let (br, found) = pick(
        &[
            get("br_t"),
            get("brT"),
            magnet_c.and_then(|m| num(m.get("br_t"))),
            magnet_m.and_then(|m| num(m.get("brT"))),
            magnet_m.and_then(|m| num(m.get("br_t"))),
        ],
        DEFAULT_BR,
    );
    if !found && need_magnet {
        notes.push(format!("br_t defaulted to {br} T"));
    }

    let (mur, found) = pick(
        &[
            get("mur_pm"),
            get("muRec"),
            magnet_m.and_then(|m| num(m.get("muRec"))),
            magnet_m.and_then(|m| num(m.get("mur_pm"))),
        ],
        DEFAULT_MUR,
    );
    if !found {
        notes.push(format!("mur_pm/muRec defaulted to {mur}"));
    }

    let rho_curves = coil_c
        .and_then(|m| num(m.get("resistivity_ohm_m")))
        .filter(|r| *r > 0.0)
        .map(|r| 1.0 / r);
    let rho_meta = coil_m
        .and_then(|m| num(m.get("resistivityOhmM")))
        .filter(|r| *r > 0.0)
        .map(|r| 1.0 / r);
    let (sig_cu, found) = pick(
        &[
            get("sigma_copper"),
            get("sigma"),
            get("conductivitySPerM"),
            rho_curves,
            coil_m.and_then(|m| num(m.get("conductivitySPerM"))),
            rho_meta,
        ],
        DEFAULT_SIG_CU,
    );
    if !found {
        notes.push(format!("sigma_copper defaulted to {sig_cu} S/m"));
    }

    let (sig_bar, found) = pick(
        &[
            get("sigma_bar"),
            bar_c.and_then(|m| num(m.get("conductivity_s_per_m"))),
            bar_m.and_then(|m| num(m.get("conductivitySPerM"))),
            bar_m.and_then(|m| num(m.get("sigma_bar"))),
        ],
        DEFAULT_SIG_BAR,
    );
    if !found && need_bar {
        notes.push(format!("sigma_bar defaulted to {sig_bar} S/m"));
    }

    Resolved {
        br_t: br,
        mur_pm: mur,
        sigma_copper: sig_cu,
        sigma_bar: sig_bar,
        notes,
    }
}
