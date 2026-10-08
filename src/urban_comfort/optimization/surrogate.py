"""
Configurable Tabular Surrogate Model for SOLARAEUS Intervention Optimization.

Provides multi-target regression and uncertainty estimation using ensemble decision trees
(Random Forest / Extra-Trees Regressors) and feasibility classification.
Quantifies tree-ensemble variance without Gaussian process matrix inversion instability.
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


from urban_comfort.optimization.parameters import ShadePanelParams, ParameterBounds
from urban_comfort.optimization.ledger import CandidateRecord


FEATURE_NAMES: Tuple[str, ...] = (
    "x", "y", "length", "width", "height", "heading_deg", "albedo", "area_m2"
)

DEFAULT_TARGETS: Tuple[str, ...] = (
    "objective_value",
    "mean_utci_c",
    "p90_utci_c",
    "mean_tmrt_c",
    "delta_mean_tmrt_c",
    "peak_local_tmrt_improvement",
)


@dataclass
class SurrogateConfig:
    """Hyperparameters and configuration for surrogate model training."""
    model_type: str = "random_forest"         # "random_forest", "extra_trees"
    n_estimators: int = 100
    max_depth: Optional[int] = 12
    min_samples_split: int = 2
    min_samples_leaf: int = 1
    seed: int = 42
    target_names: Tuple[str, ...] = DEFAULT_TARGETS
    feature_names: Tuple[str, ...] = FEATURE_NAMES
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
class SurrogatePrediction:
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


def extract_features(params: ShadePanelParams | Dict[str, Any], feature_names: Sequence[str] = FEATURE_NAMES) -> np.ndarray:
    """Extracts numeric feature vector from ShadePanelParams or param dict."""
    if isinstance(params, ShadePanelParams):
        p_dict = params.to_dict()
    else:
        p_dict = dict(params)
    if "area_m2" not in p_dict:
        p_dict["area_m2"] = float(p_dict.get("length", 0.0) * p_dict.get("width", 0.0))

    vec = [float(p_dict.get(fn, 0.0)) for fn in feature_names]
    return np.array(vec, dtype=np.float64)


def extract_targets(record: CandidateRecord, target_names: Sequence[str] = DEFAULT_TARGETS) -> Optional[np.ndarray]:
    """Extracts target values from a feasible candidate record."""
    if not record.is_feasible or record.metrics is None or not math.isfinite(record.objective_value):
        return None

    m = record.metrics
    vals = []
    for tn in target_names:
        if tn == "objective_value":
            val = float(record.objective_value)
        elif tn in m:
            val = float(m[tn])
        elif tn == "peak_local_tmrt_improvement":
            # If explicit peak_local_tmrt_improvement exists, use it; else fallback to absolute delta_mean_tmrt_c
            val = float(m.get("peak_local_tmrt_improvement", abs(m.get("delta_mean_tmrt_c", 0.0))))
        else:
            val = 0.0
        vals.append(val)
    return np.array(vals, dtype=np.float64)


class SurrogateModel:
    """
    Ensemble surrogate model predicting thermal comfort objectives and uncertainty.
    
    Uses scikit-learn tree ensembles (Random Forest / Extra-Trees) to output:
      mu(x): Ensemble mean prediction
      sigma(x): Ensemble standard deviation (empirical tree variance)
      P(feasible | x): Feasibility classification probability
    """

    def __init__(self, config: Optional[SurrogateConfig] = None):
        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "scikit-learn is required for SurrogateModel. Please install scikit-learn "
                "or ensure the environment has scikit-learn available."
            )
        self.config = config or SurrogateConfig()
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
            # Default: RandomForestRegressor
            return RandomForestRegressor(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                min_samples_split=self.config.min_samples_split,
                min_samples_leaf=self.config.min_samples_leaf,
                random_state=seed,
                n_jobs=-1,
            )

    def fit(self, records: List[CandidateRecord]) -> Dict[str, Any]:
        """
        Fits multi-target regressors on valid physical records and classifier on all records.
        
        Args:
            records: Candidate records from ledger.
            
        Returns:
            Dictionary of training summary metrics.
        """
        if not records:
            raise ValueError("Cannot fit surrogate model on empty candidate ledger.")

        # Compute dataset hash over record IDs and parameter values for provenance
        data_rep = json.dumps([{"id": r.candidate_id, "params": r.params, "feas": r.is_feasible} for r in records], sort_keys=True)
        self.training_dataset_hash = hashlib.sha256(data_rep.encode("utf-8")).hexdigest()

        # 1. Feasibility Classifier (all proposed candidates)
        X_all_list = []
        y_feas_list = []
        for r in records:
            X_all_list.append(extract_features(r.params, self.config.feature_names))
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

        # 2. Physics Regression Models (FEASIBLE, VALID CERTIFICATE records only)
        trainable_records = [
            r for r in records
            if r.is_feasible
            and r.metrics is not None
            and math.isfinite(r.objective_value)
            and r.certificate_status in ("certified", None)
        ]

        if len(trainable_records) < 3:
            raise ValueError(
                f"Surrogate model requires at least 3 feasible records for training, found {len(trainable_records)}."
            )

        X_train_list = []
        Y_train_list = []
        for r in trainable_records:
            X_train_list.append(extract_features(r.params, self.config.feature_names))
            Y_train_list.append(extract_targets(r, self.config.target_names))

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

        # Fit independent regressor per target to allow target-specific tree statistics
        reg_metrics: Dict[str, Dict[str, float]] = {}
        for t_idx, target_name in enumerate(self.config.target_names):
            y_target = Y_train[:, t_idx]
            reg = self._create_regressor(seed_offset=t_idx)
            reg.fit(X_scaled, y_target)
            self.regressors[target_name] = reg

            # Training error metrics
            y_pred = reg.predict(X_scaled)
            mse = float(mean_squared_error(y_target, y_pred))
            rmse = float(math.sqrt(mse))
            mae = float(mean_absolute_error(y_target, y_pred))
            r2 = float(r2_score(y_target, y_pred)) if len(y_target) > 1 else 1.0

            # Feature importances
            fi = {fn: float(imp) for fn, imp in zip(self.config.feature_names, reg.feature_importances_)}

            reg_metrics[target_name] = {
                "rmse": round(rmse, 6),
                "mae": round(mae, 6),
                "r2": round(r2, 4),
                "feature_importances": fi,
            }

        self.is_fitted = True
        self.training_metrics = {
            "n_train_samples": self.n_train_samples,
            "n_total_candidates": len(records),
            "dataset_hash": self.training_dataset_hash,
            "target_metrics": reg_metrics,
        }
        return self.training_metrics

    def predict(self, params: ShadePanelParams | Dict[str, Any]) -> SurrogatePrediction:
        """Predicts target means, standard deviations, and feasibility for a single candidate."""
        preds = self.predict_batch([params])
        return preds[0]

    def predict_batch(self, params_list: List[ShadePanelParams | Dict[str, Any]]) -> List[SurrogatePrediction]:
        """
        Batch prediction over multiple candidates.
        
        Computes exact empirical tree variance across estimators:
          sigma^2(x) = (1 / B) * sum_{b=1}^B (f_b(x) - mu(x))^2
        """
        if not self.is_fitted:
            raise RuntimeError("SurrogateModel must be fitted before predict() is called.")

        n = len(params_list)
        if n == 0:
            return []

        X_raw = np.array([extract_features(p, self.config.feature_names) for p in params_list], dtype=np.float64)
        if self.scaler is not None:
            X = self.scaler.transform(X_raw)
        else:
            X = X_raw

        # Feasibility probabilities
        if self.classifier is not None:
            probs = self.classifier.predict_proba(X_raw)
            # Find index of class 1 (feasible)
            classes = list(self.classifier.classes_)
            if 1 in classes:
                idx_1 = classes.index(1)
                feas_probs = probs[:, idx_1]
            else:
                feas_probs = np.zeros(n, dtype=np.float64)
        else:
            feas_probs = np.ones(n, dtype=np.float64)

        # Regressor predictions per target
        target_means: Dict[str, np.ndarray] = {}
        target_stds: Dict[str, np.ndarray] = {}

        for target_name in self.config.target_names:
            reg = self.regressors[target_name]
            # Accumulate predictions from each individual decision tree
            tree_preds = np.stack([tree.predict(X) for tree in reg.estimators_], axis=0) # (B, n)
            mu = np.mean(tree_preds, axis=0)
            if reg.n_estimators > 1:
                var = np.var(tree_preds, axis=0, ddof=1)
                sigma = np.sqrt(np.maximum(0.0, var))
            else:
                sigma = np.zeros_like(mu)

            target_means[target_name] = mu
            target_stds[target_name] = sigma

        results: List[SurrogatePrediction] = []
        for i in range(n):
            means_i = {tn: float(target_means[tn][i]) for tn in self.config.target_names}
            stds_i = {tn: float(target_stds[tn][i]) for tn in self.config.target_names}
            p_feas = float(np.clip(feas_probs[i], 0.0, 1.0))
            risk = float(1.0 - p_feas)

            results.append(SurrogatePrediction(
                means=means_i,
                stds=stds_i,
                feasibility_probability=p_feas,
                feasibility_risk=risk,
            ))

        return results


class FallbackSurrogateModel:
    """
    Robust fallback surrogate model when scikit-learn is not installed or surrogate modeling is disabled.
    Uses empirical parameter-space distance weighted averages.
    """

    def __init__(self, config: Optional[SurrogateConfig] = None):
        self.config = config or SurrogateConfig()
        self.is_fitted: bool = False
        self.train_X: np.ndarray = np.empty((0, len(self.config.feature_names)))
        self.train_Y: np.ndarray = np.empty((0, len(self.config.target_names)))
        self.n_train_samples: int = 0
        self.training_dataset_hash: str = ""

    def fit(self, records: List[CandidateRecord]) -> Dict[str, Any]:
        data_rep = json.dumps([{"id": r.candidate_id, "params": r.params} for r in records], sort_keys=True)
        self.training_dataset_hash = hashlib.sha256(data_rep.encode("utf-8")).hexdigest()

        trainable = [
            r for r in records
            if r.is_feasible and r.metrics is not None and math.isfinite(r.objective_value)
        ]
        if len(trainable) < 1:
            raise ValueError("Fallback surrogate requires at least 1 feasible candidate.")

        self.train_X = np.array([extract_features(r.params, self.config.feature_names) for r in trainable], dtype=np.float64)
        self.train_Y = np.array([extract_targets(r, self.config.target_names) for r in trainable], dtype=np.float64)
        self.n_train_samples = len(trainable)
        self.is_fitted = True
        return {"n_train_samples": self.n_train_samples, "model_type": "fallback_empirical"}

    def predict(self, params: ShadePanelParams | Dict[str, Any]) -> SurrogatePrediction:
        preds = self.predict_batch([params])
        return preds[0]

    def predict_batch(self, params_list: List[ShadePanelParams | Dict[str, Any]]) -> List[SurrogatePrediction]:
        if not self.is_fitted:
            raise RuntimeError("FallbackSurrogateModel must be fitted before predict.")

        results: List[SurrogatePrediction] = []
        mean_y = np.mean(self.train_Y, axis=0)
        std_y = np.std(self.train_Y, axis=0) if len(self.train_Y) > 1 else np.ones_like(mean_y) * 0.1

        for p in params_list:
            x_vec = extract_features(p, self.config.feature_names)
            # Distance to nearest sample
            dists = np.linalg.norm(self.train_X - x_vec, axis=1)
            min_dist = float(np.min(dists)) if len(dists) > 0 else 1.0

            # Scale uncertainty with distance
            uncertainty_scale = min(3.0, 1.0 + min_dist * 0.1)
            means_dict = {tn: float(mean_y[i]) for i, tn in enumerate(self.config.target_names)}
            stds_dict = {tn: float(std_y[i] * uncertainty_scale) for i, tn in enumerate(self.config.target_names)}

            results.append(SurrogatePrediction(
                means=means_dict,
                stds=stds_dict,
                feasibility_probability=1.0,
                feasibility_risk=0.0,
            ))
        return results
