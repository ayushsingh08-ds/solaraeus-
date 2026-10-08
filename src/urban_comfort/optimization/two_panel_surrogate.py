"""
Configurable Tabular Surrogate Model for Two-Panel SOLARAEUS Intervention Optimization.

Provides multi-target regression and uncertainty estimation using ensemble decision trees
(Random Forest / Extra-Trees Regressors) and feasibility classification for 14-parameter dual-panel configurations.
Features are permutation-invariant via canonical coordinate ordering.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Dict, Any, List, Optional, Tuple, Sequence
import numpy as np

try:
    from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from urban_comfort.optimization.two_panel_parameters import TwoPanelParams
from urban_comfort.optimization.two_panel_ledger import TwoPanelCandidateRecord


TWO_PANEL_FEATURE_NAMES: Tuple[str, ...] = (
    "x1", "y1", "length1", "width1", "height1", "heading_deg1", "albedo1", "area1_m2",
    "x2", "y2", "length2", "width2", "height2", "heading_deg2", "albedo2", "area2_m2",
    "total_area_m2", "center_distance_m", "separation_distance_m", "delta_height_m",
)

TWO_PANEL_DEFAULT_TARGETS: Tuple[str, ...] = (
    "objective_value",
    "mean_utci_c",
    "p90_utci_c",
    "mean_tmrt_c",
    "delta_mean_tmrt_c",
    "thermal_improvement_utci_c",
    "peak_local_tmrt_improvement_k",
)


@dataclass
class TwoPanelSurrogateConfig:
    """Hyperparameters and configuration for two-panel surrogate model training."""
    model_type: str = "random_forest"         # "random_forest", "extra_trees"
    n_estimators: int = 100
    max_depth: Optional[int] = 12
    min_samples_split: int = 2
    min_samples_leaf: int = 1
    seed: int = 42
    target_names: Tuple[str, ...] = TWO_PANEL_DEFAULT_TARGETS
    feature_names: Tuple[str, ...] = TWO_PANEL_FEATURE_NAMES
    use_feature_scaling: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type,
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "min_samples_split": self.min_samples_split,
            "min_samples_leaf": self.min_samples_leaf,
            "seed": self.seed,
            "target_names": list(self.target_names),
            "feature_names": list(self.feature_names),
            "use_feature_scaling": self.use_feature_scaling,
        }


@dataclass
class TwoPanelSurrogatePrediction:
    """Pointwise prediction containing target means, uncertainties, and feasibility probability."""
    means: Dict[str, float]
    stds: Dict[str, float]
    feasibility_probability: float = 1.0
    feasibility_risk: float = 0.0

    @property
    def objective_mean(self) -> float:
        return self.means.get("objective_value", float("inf"))

    @property
    def objective_std(self) -> float:
        return self.stds.get("objective_value", 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "means": {k: float(v) for k, v in self.means.items()},
            "stds": {k: float(v) for k, v in self.stds.items()},
            "feasibility_probability": float(self.feasibility_probability),
            "feasibility_risk": float(self.feasibility_risk),
        }


def extract_two_panel_features(params: TwoPanelParams | Dict[str, Any],
                               feature_names: Sequence[str] = TWO_PANEL_FEATURE_NAMES) -> np.ndarray:
    """
    Extracts permutation-invariant numeric feature vector for a two-panel configuration.
    Canonicalizes so x1 <= x2 before feature extraction.
    """
    if isinstance(params, dict):
        p = TwoPanelParams.from_dict(params).canonicalize()
    else:
        p = params.canonicalize()

    area1 = p.area1
    area2 = p.area2
    total_area = p.total_area
    center_dist = math.hypot(p.x1 - p.x2, p.y1 - p.y2)
    sep_dist = p.separation_distance()
    delta_h = abs(p.height1 - p.height2)

    feat_map = {
        "x1": p.x1, "y1": p.y1, "length1": p.length1, "width1": p.width1,
        "height1": p.height1, "heading_deg1": p.heading_deg1, "albedo1": p.albedo1, "area1_m2": area1,
        "x2": p.x2, "y2": p.y2, "length2": p.length2, "width2": p.width2,
        "height2": p.height2, "heading_deg2": p.heading_deg2, "albedo2": p.albedo2, "area2_m2": area2,
        "total_area_m2": total_area,
        "center_distance_m": center_dist,
        "separation_distance_m": sep_dist,
        "delta_height_m": delta_h,
    }

    return np.array([float(feat_map.get(f, 0.0)) for f in feature_names], dtype=np.float64)


def extract_two_panel_targets(record: TwoPanelCandidateRecord, target_names: Sequence[str]) -> np.ndarray:
    """Extracts ground-truth physics targets from a two-panel record."""
    vals = []
    m = record.metrics or {}
    for tn in target_names:
        if tn == "objective_value":
            val = float(record.objective_value)
        elif tn in m:
            val = float(m[tn])
        else:
            val = 0.0
        vals.append(val)
    return np.array(vals, dtype=np.float64)


class TwoPanelSurrogateModel:
    """
    Ensemble surrogate model predicting thermal comfort objectives and uncertainty for two-panel interventions.

    Uses scikit-learn tree ensembles (Random Forest / Extra-Trees) to output:
      mu(x): Ensemble mean prediction
      sigma(x): Ensemble standard deviation (empirical tree variance)
      P(feasible | x): Feasibility classification probability
    """

    def __init__(self, config: Optional[TwoPanelSurrogateConfig] = None):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for TwoPanelSurrogateModel.")
        self.config = config or TwoPanelSurrogateConfig()
        self.is_fitted: bool = False
        self.regressors: Dict[str, Any] = {}
        self.classifier: Optional[Any] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_scaling_info: Dict[str, Any] = {}
        self.training_dataset_hash: str = ""
        self.n_train_samples: int = 0
        self.training_metrics: Dict[str, Any] = {}

    def _create_regressor(self, seed_offset: int = 0):
        seed = self.config.seed + seed_offset
        if self.config.model_type == "extra_trees":
            return ExtraTreesRegressor(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                min_samples_split=self.config.min_samples_split,
                min_samples_leaf=self.config.min_samples_leaf,
                random_state=seed,
                n_jobs=-1,
            )
        else:
            return RandomForestRegressor(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                min_samples_split=self.config.min_samples_split,
                min_samples_leaf=self.config.min_samples_leaf,
                random_state=seed,
                n_jobs=-1,
            )

    def fit(self, records: List[TwoPanelCandidateRecord]) -> Dict[str, Any]:
        """
        Fits multi-target regressors on valid physically evaluated records and classifier on all records.
        """
        if not records:
            raise ValueError("Cannot fit surrogate model on empty candidate ledger.")

        data_rep = json.dumps([{"id": r.candidate_id, "params": r.params, "feas": r.is_feasible} for r in records], sort_keys=True)
        self.training_dataset_hash = hashlib.sha256(data_rep.encode("utf-8")).hexdigest()

        # 1. Feasibility Classifier (all proposed candidates)
        X_all_list = []
        y_feas_list = []
        for r in records:
            X_all_list.append(extract_two_panel_features(r.params, self.config.feature_names))
            y_feas_list.append(1 if r.is_feasible else 0)

        X_all = np.array(X_all_list, dtype=np.float64)
        y_feas = np.array(y_feas_list, dtype=np.int64)

        if len(np.unique(y_feas)) > 1:
            clf = RandomForestClassifier(
                n_estimators=min(50, self.config.n_estimators),
                max_depth=6,
                random_state=self.config.seed,
                n_jobs=-1,
            )
            clf.fit(X_all, y_feas)
            self.classifier = clf
        else:
            self.classifier = None

        # 2. Physics Regression Models (FEASIBLE, physically evaluated records only)
        trainable_records = [
            r for r in records
            if r.is_feasible
            and r.metrics is not None
            and math.isfinite(r.objective_value)
            and r.certificate_status in ("certified", None)
        ]

        if len(trainable_records) < 3:
            raise ValueError(
                f"Two-panel surrogate requires at least 3 feasible records for training, found {len(trainable_records)}."
            )

        X_train_list = []
        Y_train_list = []
        for r in trainable_records:
            X_train_list.append(extract_two_panel_features(r.params, self.config.feature_names))
            Y_train_list.append(extract_two_panel_targets(r, self.config.target_names))

        X_train = np.array(X_train_list, dtype=np.float64)
        Y_train = np.array(Y_train_list, dtype=np.float64)
        self.n_train_samples = len(X_train)

        # Feature scaling
        if self.config.use_feature_scaling:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X_train)
            self.feature_scaling_info = {
                "mean": self.scaler.mean_.tolist(),
                "std": self.scaler.scale_.tolist(),
                "feature_names": list(self.config.feature_names),
            }
        else:
            self.scaler = None
            X_scaled = X_train
            self.feature_scaling_info = {"scaling": "none"}

        # Train individual regressors per target
        self.regressors = {}
        self.training_metrics = {
            "n_train_samples": self.n_train_samples,
            "targets": {},
        }

        for idx, t_name in enumerate(self.config.target_names):
            y_target = Y_train[:, idx]
            reg = self._create_regressor(seed_offset=idx * 7)
            reg.fit(X_scaled, y_target)
            self.regressors[t_name] = reg

            y_pred = reg.predict(X_scaled)
            mse = float(mean_squared_error(y_target, y_pred))
            mae = float(mean_absolute_error(y_target, y_pred))
            r2 = float(r2_score(y_target, y_pred)) if len(y_target) > 1 and np.var(y_target) > 1e-9 else 1.0

            self.training_metrics["targets"][t_name] = {
                "mse": round(mse, 6),
                "rmse": round(math.sqrt(mse), 6),
                "mae": round(mae, 6),
                "r2": round(r2, 4),
            }

        self.is_fitted = True
        return self.training_metrics

    def predict(self, params: TwoPanelParams | Dict[str, Any]) -> TwoPanelSurrogatePrediction:
        """Pointwise surrogate prediction with uncertainty quantification."""
        if not self.is_fitted:
            raise RuntimeError("TwoPanelSurrogateModel must be fitted before predict.")

        x_vec = extract_two_panel_features(params, self.config.feature_names).reshape(1, -1)
        x_scaled = self.scaler.transform(x_vec) if self.scaler is not None else x_vec

        means: Dict[str, float] = {}
        stds: Dict[str, float] = {}

        for t_name, reg in self.regressors.items():
            # Tree-ensemble predictions
            tree_preds = np.array([tree.predict(x_scaled)[0] for tree in reg.estimators_], dtype=np.float64)
            mu = float(np.mean(tree_preds))
            sigma = float(np.std(tree_preds))
            means[t_name] = mu
            stds[t_name] = sigma

        # Feasibility classification
        p_feas = 1.0
        risk = 0.0
        if self.classifier is not None:
            proba = self.classifier.predict_proba(x_vec)[0]
            # proba has classes [0, 1]
            classes = list(self.classifier.classes_)
            if 1 in classes:
                p_feas = float(proba[classes.index(1)])
            else:
                p_feas = 0.0
            risk = 1.0 - p_feas

        return TwoPanelSurrogatePrediction(
            means=means,
            stds=stds,
            feasibility_probability=p_feas,
            feasibility_risk=risk,
        )

    def predict_batch(self, params_list: Sequence[TwoPanelParams | Dict[str, Any]]) -> List[TwoPanelSurrogatePrediction]:
        """Batch surrogate prediction for candidate screening."""
        if not self.is_fitted or not params_list:
            return []

        X_vecs = np.array([extract_two_panel_features(p, self.config.feature_names) for p in params_list], dtype=np.float64)
        X_scaled = self.scaler.transform(X_vecs) if self.scaler is not None else X_vecs

        n = len(params_list)
        means_dict: Dict[str, np.ndarray] = {}
        stds_dict: Dict[str, np.ndarray] = {}

        for t_name, reg in self.regressors.items():
            # Estimator matrix [n_estimators, n_samples]
            tree_preds = np.array([tree.predict(X_scaled) for tree in reg.estimators_], dtype=np.float64)
            means_dict[t_name] = np.mean(tree_preds, axis=0)
            stds_dict[t_name] = np.std(tree_preds, axis=0)

        # Feasibility probabilities
        p_feas_arr = np.ones(n, dtype=np.float64)
        if self.classifier is not None:
            proba = self.classifier.predict_proba(X_vecs)
            classes = list(self.classifier.classes_)
            if 1 in classes:
                p_feas_arr = proba[:, classes.index(1)]
            else:
                p_feas_arr = np.zeros(n, dtype=np.float64)

        results = []
        for i in range(n):
            m = {t_name: float(means_dict[t_name][i]) for t_name in self.config.target_names}
            s = {t_name: float(stds_dict[t_name][i]) for t_name in self.config.target_names}
            p_f = float(p_feas_arr[i])
            results.append(TwoPanelSurrogatePrediction(
                means=m, stds=s, feasibility_probability=p_f, feasibility_risk=1.0 - p_f
            ))
        return results

    def get_feature_importances(self) -> Dict[str, Dict[str, float]]:
        """Returns MDI feature importances across all target regressors."""
        if not self.is_fitted:
            return {}
        res = {}
        for t_name, reg in self.regressors.items():
            imp = reg.feature_importances_
            res[t_name] = {f: float(imp[i]) for i, f in enumerate(self.config.feature_names)}
        return res
