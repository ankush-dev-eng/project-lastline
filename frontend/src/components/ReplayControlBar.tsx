import React from 'react';
import { Play, Pause, SkipBack, SkipForward, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useLastlineStore } from '../store/useLastlineStore';

export const ReplayControlBar: React.FC = () => {
  const {
    scenarios,
    activeScenarioId,
    selectScenario,
    frame,
    play,
    pause,
    stepForward,
    stepBackward,
    seekHour,
    setSpeed,
  } = useLastlineStore();

  const currentHour = frame.current_hour ?? 0;
  const maxHours = frame.max_hours ?? 24;
  const isPlaying = frame.is_playing ?? false;
  const speed = frame.speed ?? 1.0;
  const isAlarm = frame.system_alarm ?? false;

  return (
    <div className="border-b border-stone dark:border-basalt-subtle bg-white dark:bg-basalt px-5 py-2 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
      {/* Scenario Selector & Alarm Indicator */}
      <div className="flex items-center space-x-3">
        <label htmlFor="scenario-select" className="text-text-muted font-sans font-semibold">
          SCENARIO:
        </label>
        <select
          id="scenario-select"
          value={activeScenarioId}
          onChange={(e) => selectScenario(e.target.value)}
          className="bg-bone dark:bg-ink-muted border border-stone dark:border-basalt-subtle px-2.5 py-1 rounded text-ink dark:text-bone text-xs font-sans focus:outline-hidden focus:ring-1 focus:ring-sage"
        >
          {scenarios.map((s) => (
            <option key={s.scenario_id} value={s.scenario_id}>
              {s.name}
            </option>
          ))}
        </select>

        {/* Alarm Status Badge */}
        <div
          className={`flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full font-semibold border ${
            isAlarm
              ? 'bg-brick-subtle text-brick border-brick/40 animate-pulse'
              : 'bg-moss-subtle text-moss border-moss/40'
          }`}
        >
          {isAlarm ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
          <span>{isAlarm ? 'CYBER THREAT DETECTED' : 'SYSTEM NOMINAL'}</span>
        </div>
      </div>

      {/* Transport Controls & Timeline Scrubber */}
      <div className="flex items-center space-x-3 flex-1 max-w-xl">
        <div className="flex items-center space-x-1">
          <button
            onClick={stepBackward}
            aria-label="Step Backward (1 hr)"
            className="p-1 rounded hover:bg-stone/30 dark:hover:bg-basalt-subtle text-ink dark:text-bone"
            title="Step Backward (1 hr)"
          >
            <SkipBack className="w-4 h-4" />
          </button>

          <button
            onClick={isPlaying ? pause : play}
            aria-label={isPlaying ? 'Pause Simulation' : 'Play Simulation'}
            className={`p-1.5 rounded text-white ${
              isPlaying ? 'bg-copper hover:bg-copper/90' : 'bg-sage hover:bg-sage-hover'
            }`}
            title={isPlaying ? 'Pause Simulation' : 'Play Simulation'}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>

          <button
            onClick={stepForward}
            aria-label="Step Forward (1 hr)"
            className="p-1 rounded hover:bg-stone/30 dark:hover:bg-basalt-subtle text-ink dark:text-bone"
            title="Step Forward (1 hr)"
          >
            <SkipForward className="w-4 h-4" />
          </button>
        </div>

        {/* Time Scrubber Slider */}
        <div className="flex items-center space-x-2 flex-1">
          <input
            type="range"
            min={0}
            max={maxHours}
            step={1}
            value={currentHour}
            aria-label="Simulation timeline scrubber"
            onChange={(e) => seekHour(Number(e.target.value))}
            className="w-full h-1.5 bg-stone dark:bg-basalt-subtle rounded-lg appearance-none cursor-pointer accent-sage"
          />
          <span className="font-telemetry font-bold text-ink dark:text-bone min-w-[5.5rem] text-right">
            T+{currentHour.toString().padStart(2, '0')}.0h / {maxHours}h
          </span>
        </div>
      </div>

      {/* Speed Controls */}
      <div className="flex items-center space-x-1">
        <span className="text-text-muted font-sans mr-1">SPEED:</span>
        {[1.0, 2.0, 5.0, 10.0].map((s) => (
          <button
            key={s}
            onClick={() => setSpeed(s)}
            className={`px-1.5 py-0.5 rounded text-[11px] font-mono transition-colors ${
              speed === s
                ? 'bg-sage text-white font-bold'
                : 'bg-stone/40 dark:bg-basalt-subtle text-ink dark:text-bone hover:bg-stone dark:hover:bg-basalt'
            }`}
          >
            {s}x
          </button>
        ))}
      </div>
    </div>
  );
};

