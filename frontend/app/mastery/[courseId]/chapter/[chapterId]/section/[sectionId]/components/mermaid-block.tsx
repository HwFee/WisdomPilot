'use client'

import { useRef, useState, useEffect } from 'react'
import mermaid from 'mermaid'

interface MermaidDiagramProps {
  svg: string
  className: string
}

function MermaidDiagram({ svg, className }: MermaidDiagramProps) {
  // react-doctor-disable-next-line no-danger
  return <div className={className} dangerouslySetInnerHTML={{ __html: svg }} /* eslint-disable-line react/no-danger */ />
}

export function MermaidBlock({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const [mermaidState, setMermaidState] = useState<{ svg: string; err: string | null }>({ svg: '', err: null })

  useEffect(() => {
    let cancelled = false
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'strict',
    })
    const render = async () => {
      try {
        const id = `mermaid-${Math.random().toString(36).slice(2)}`
        const { svg } = await mermaid.render(id, code)
        if (!cancelled) {
          setMermaidState({ svg, err: null })
        }
      } catch (e) {
        if (!cancelled) {
          setMermaidState({ svg: '', err: e instanceof Error ? e.message : 'Mermaid 渲染失败' })
        }
      }
    }
    render()
    return () => { cancelled = true }
  }, [code])

  if (mermaidState.err) {
    return (
      <div className="bg-red-950/30 border border-red-700/50 rounded-lg p-3 my-3">
        <p className="text-red-400 text-xs mb-1">流程图渲染失败</p>
        <pre className="text-red-300 text-xs whitespace-pre-wrap">{code}</pre>
      </div>
    )
  }

  return (
    <div ref={ref}>
      <MermaidDiagram svg={mermaidState.svg} className="mermaid-diagram my-3 flex justify-center bg-gray-800/50 rounded-lg p-4 overflow-x-auto" />
    </div>
  )
}
(MermaidBlock as any).isMermaid = true
