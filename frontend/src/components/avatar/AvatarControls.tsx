import React from 'react';
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Camera,
  Eye,
  Footprints,
  RotateCcw,
  Zap,
} from 'lucide-react';
import { useAppStore } from '../../stores/appStore';

export const AvatarControls: React.FC = () => {
  const {
    avatarMode,
    cameraMode,
    setCameraMode,
    avatarSpeed,
    setAvatarSpeed,
    teleportAvatar,
    resetAvatarPosition,
  } = useAppStore();

  if (!avatarMode) return null;

  // Discrete step impulse for instantaneous click responsiveness
  const stepMove = (forwardDir: number) => {
    const state = useAppStore.getState();
    const [x, y, z] = state.avatarPosition;
    const heading = state.avatarHeading;
    const speed = state.avatarSpeed;
    const dist = speed * 0.7; // ~2.1m step
    const dx = Math.sin(heading) * forwardDir * dist;
    const dz = -Math.cos(heading) * forwardDir * dist;
    state.setAvatarPosition([x + dx, y, z + dz]);
  };

  const stepTurn = (turnDir: number) => {
    const state = useAppStore.getState();
    state.setAvatarHeading(state.avatarHeading + turnDir * 0.35); // ~20 degrees
  };

  // Virtual key trigger for hold-to-walk interaction
  const triggerKey = (key: string, isDown: boolean) => {
    const eventType = isDown ? 'keydown' : 'keyup';
    window.dispatchEvent(
      new KeyboardEvent(eventType, {
        key,
        code: key === 'shift' ? 'ShiftLeft' : `Key${key.toUpperCase()}`,
        bubbles: true,
      })
    );
  };

  const toggleCamera = () => {
    setCameraMode(cameraMode === 'third-person' ? 'first-person' : 'third-person');
  };

  return (
    <div className="avatar-controls-container">
      <div className="controls-glass-panel">
        <div className="controls-header">
          <div className="controls-title">
            <Footprints size={14} />
            <span>NAVIGATION CONTROLS</span>
          </div>
          <button
            className="cam-toggle-btn"
            onClick={toggleCamera}
            title={cameraMode === 'third-person' ? 'Switch to First-Person' : 'Switch to Third-Person'}
          >
            {cameraMode === 'third-person' ? <Eye size={13} /> : <Camera size={13} />}
            <span>{cameraMode === 'third-person' ? '3rd Person' : '1st Person'}</span>
          </button>
        </div>

        {/* Virtual Directional D-Pad */}
        <div className="dpad-grid">
          <div className="dpad-empty" />
          <button
            className="dpad-btn dpad-up"
            title="Walk Forward (W or ↑)"
            onClick={() => stepMove(1)}
            onMouseDown={() => triggerKey('w', true)}
            onMouseUp={() => triggerKey('w', false)}
            onMouseLeave={() => triggerKey('w', false)}
            onTouchStart={() => triggerKey('w', true)}
            onTouchEnd={() => triggerKey('w', false)}
          >
            <ArrowUp size={18} />
          </button>
          <div className="dpad-empty" />

          <button
            className="dpad-btn dpad-left"
            title="Turn Left (A or ←)"
            onClick={() => stepTurn(1)}
            onMouseDown={() => triggerKey('a', true)}
            onMouseUp={() => triggerKey('a', false)}
            onMouseLeave={() => triggerKey('a', false)}
            onTouchStart={() => triggerKey('a', true)}
            onTouchEnd={() => triggerKey('a', false)}
          >
            <ArrowLeft size={18} />
          </button>
          <button
            className="dpad-btn dpad-center"
            title="Reset to Fountain Center"
            onClick={resetAvatarPosition}
          >
            <RotateCcw size={14} />
          </button>
          <button
            className="dpad-btn dpad-right"
            title="Turn Right (D or →)"
            onClick={() => stepTurn(-1)}
            onMouseDown={() => triggerKey('d', true)}
            onMouseUp={() => triggerKey('d', false)}
            onMouseLeave={() => triggerKey('d', false)}
            onTouchStart={() => triggerKey('d', true)}
            onTouchEnd={() => triggerKey('d', false)}
          >
            <ArrowRight size={18} />
          </button>

          <div className="dpad-empty" />
          <button
            className="dpad-btn dpad-down"
            title="Walk Backward (S or ↓)"
            onClick={() => stepMove(-1)}
            onMouseDown={() => triggerKey('s', true)}
            onMouseUp={() => triggerKey('s', false)}
            onMouseLeave={() => triggerKey('s', false)}
            onTouchStart={() => triggerKey('s', true)}
            onTouchEnd={() => triggerKey('s', false)}
          >
            <ArrowDown size={18} />
          </button>
          <div className="dpad-empty" />
        </div>

        {/* Quick Speed & Action Modifiers */}
        <div className="controls-action-row">
          <button
            className="sprint-btn"
            title="Hold to Sprint"
            onMouseDown={() => triggerKey('shift', true)}
            onMouseUp={() => triggerKey('shift', false)}
            onMouseLeave={() => triggerKey('shift', false)}
            onTouchStart={() => triggerKey('shift', true)}
            onTouchEnd={() => triggerKey('shift', false)}
          >
            <Zap size={13} />
            <span>SPRINT ({avatarSpeed.toFixed(1)} m/s)</span>
          </button>
          <button
            className="speed-step-btn"
            title="Decrease Speed"
            onClick={() => setAvatarSpeed(Math.max(1.0, avatarSpeed - 0.5))}
          >
            -
          </button>
          <button
            className="speed-step-btn"
            title="Increase Speed"
            onClick={() => setAvatarSpeed(Math.min(5.0, avatarSpeed + 0.5))}
          >
            +
          </button>
        </div>

        {/* Preset Landmark Teleports */}
        <div className="teleport-section">
          <span className="teleport-label">Quick Teleports:</span>
          <div className="teleport-chips">
            <button
              className="teleport-chip"
              onClick={() => teleportAvatar([-27, 3.0, 13], 0)}
              title="Park Center Fountain & Lawn"
            >
              ⛲ Fountain
            </button>
            <button
              className="teleport-chip"
              onClick={() => teleportAvatar([-27, 2.5, -61], 0)}
              title="Washington Arch (North Plaza)"
            >
              🏛️ Arch
            </button>
            <button
              className="teleport-chip"
              onClick={() => teleportAvatar([80, 5.0, 13], -Math.PI / 2)}
              title="Shaded East Building Canyon (Waverly Place)"
            >
              🏢 Canyon
            </button>
            <button
              className="teleport-chip"
              onClick={() => teleportAvatar([-27, 3.8, 74], 0)}
              title="South Tree Lawn Area"
            >
              🌳 Lawn
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
