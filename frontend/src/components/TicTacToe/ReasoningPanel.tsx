import type { TicTacToeReasoningStep } from '../../types/tictactoe'

interface ReasoningPanelProps {
  steps: TicTacToeReasoningStep[]
  isStreaming: boolean
}

function formatConfidence(value: number | null): string | null {
  if (value === null || Number.isNaN(value)) return null
  const percent = Math.round(value * 100)
  return `${percent}% confidence`
}

export function ReasoningPanel({ steps, isStreaming }: ReasoningPanelProps) {
  const visibleSteps = steps.slice(-6)

  return (
    <section className="rounded-2xl border border-slate-300 bg-white/85 p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-slate-800">AI Reasoning</h3>
          <p className="text-sm text-slate-500">Decision trace for the latest AI move.</p>
        </div>
        <span className="rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
          {isStreaming ? 'Streaming live' : `${steps.length} step${steps.length === 1 ? '' : 's'}`}
        </span>
      </div>

      {steps.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4">
          <p className="text-sm text-slate-500">No reasoning yet. Make a move to inspect AI strategy.</p>
        </div>
      ) : (
        <>
          <div className="grid gap-3 md:grid-cols-2">
            {visibleSteps.map((step, index) => {
              const confidence = formatConfidence(step.confidence)
              return (
                <article key={`${step.step}-${index}`} className="rounded-xl border border-slate-200 bg-slate-50 p-3.5">
                  <div className="mb-1.5 flex items-center justify-between gap-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{step.source}</p>
                    {confidence && <p className="text-xs font-semibold text-emerald-700">{confidence}</p>}
                  </div>
                  <p className="text-sm font-semibold text-slate-800">{step.step}</p>
                  <p className="mt-1 text-sm text-slate-600">{step.detail}</p>
                </article>
              )
            })}
          </div>
          {steps.length > visibleSteps.length && (
            <p className="mt-3 text-xs text-slate-500">
              Showing latest {visibleSteps.length} of {steps.length} reasoning steps.
            </p>
          )}
        </>
      )}
    </section>
  )
}
